"""Failure-isolated platform state snapshots."""
from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from copilot_sdk.backend.diagnostics_models import DiagnosticsResponse
from scripts.graph_census_v2 import run_census

COPILOT_PORTS: dict[str, int] = {
    "soc": 8001,
    "s2p": 8002,
    "trading": 8010,
    "purchasing": 8020,
    "dataops": 8030,
}
EXPECTED_DOMAINS = tuple(COPILOT_PORTS)


def _get_json(url: str) -> tuple[int, dict[str, Any]]:
    with urlopen(Request(url, method="GET"), timeout=30) as response:
        body = response.read().decode("utf-8")
        value = json.loads(body)
        return int(response.status), value if isinstance(value, dict) else {"value": value}


def _collect_copilot_state(domain: str, port: int) -> dict[str, Any]:
    state: dict[str, Any] = {"domain": domain, "port": port, "health": None, "diagnostics": None, "errors": []}
    try:
        state["health_status"], state["health"] = _get_json(f"http://127.0.0.1:{port}/health")
    except HTTPError as exc:
        state["health_status"] = exc.code
        state["errors"].append(f"health_http_{exc.code}")
    except Exception as exc:
        state["errors"].append(f"unreachable: {exc}")
    try:
        status, payload = _get_json(f"http://127.0.0.1:{port}/api/diagnostics")
        state["diagnostics_status"] = status
        state["diagnostics"] = DiagnosticsResponse.model_validate(payload).model_dump(mode="json")
    except HTTPError as exc:
        state["diagnostics_status"] = exc.code
        state["errors"].append("diagnostics_404" if exc.code == 404 else f"diagnostics_http_{exc.code}")
    except Exception as exc:
        state["errors"].append(f"diagnostics_error: {exc}")
    return state


def _redact_dsn(dsn: str) -> str:
    return re.sub(r"(password=)([^ ]+)", r"\1<redacted>", dsn, flags=re.IGNORECASE)


def _collect_age_state(dsn: str, graph_name: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "dsn": _redact_dsn(dsn),
        "reachable": False,
        "graph_name": graph_name,
        "total_nodes": None,
    }
    try:
        census = run_census(dsn, graph_name)
        result["reachable"] = True
        total_section = census.get("sections", {}).get("TOTAL NODE COUNT", [])
        if total_section and total_section[0]:
            result["total_nodes"] = int(total_section[0][0])
        else:
            result["total_nodes"] = 0
        if census.get("errors"):
            result["census_errors"] = census["errors"]
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def _clean(value: Any) -> str:
    return str(value).strip('"')


def _section(state: dict[str, Any], title: str) -> list[Any]:
    census = state.get("census", {})
    return list(census.get("sections", {}).get(title, []))


def _domain_counts(state: dict[str, Any], title: str) -> dict[str, int]:
    values: dict[str, int] = {}
    for row in _section(state, title):
        if len(row) >= 2:
            try:
                values[_clean(row[0])] = int(_clean(row[1]))
            except (TypeError, ValueError):
                continue
    return values


def _check_integrity(state: dict[str, Any]) -> dict[str, Any]:
    decisions = _domain_counts(state, "DECISIONS PER DOMAIN")
    conservation = _domain_counts(state, "CONSERVATION SNAPSHOTS PER DOMAIN")
    checkpoints = _domain_counts(state, "CHECKPOINTS PER DOMAIN")
    fingerprints = _domain_counts(state, "FINGERPRINTS PER DOMAIN")
    receipts = _domain_counts(state, "EVIDENCE RECEIPTS PER DOMAIN")
    anchors = {_clean(row[0]) for row in _section(state, "DOMAIN ANCHORS") if row}
    transfer_rows = _section(state, "TRANSFER PATTERNS")
    transfers = int(_clean(transfer_rows[0][0])) if transfer_rows and transfer_rows[0] else 0
    monetary = sum(
        int(_clean(row[1])) for row in _section(state, "DOMAIN CONTEXT ENTITIES")
        if len(row) >= 2 and _clean(row[0]) in {"sap_change", "celonis_process", "operations_context"}
        and _clean(row[1]).isdigit()
    )
    checks = {
        "all_decisions": all(decisions.get(domain, 0) > 0 for domain in EXPECTED_DOMAINS),
        "all_conservation": all(conservation.get(domain, 0) > 0 for domain in EXPECTED_DOMAINS),
        "all_checkpoints": all(checkpoints.get(domain, 0) > 0 for domain in EXPECTED_DOMAINS),
        "all_anchors": all(domain in anchors for domain in EXPECTED_DOMAINS),
        "all_fingerprints": all(fingerprints.get(domain, 0) > 0 for domain in EXPECTED_DOMAINS),
        "all_receipts": all(receipts.get(domain, 0) > 0 for domain in EXPECTED_DOMAINS),
        "transfer_patterns": transfers > 0,
        "monetary_entities": monetary > 0,
    }
    return {**checks, "decisions": decisions, "conservation": conservation, "checkpoints": checkpoints,
            "fingerprints": fingerprints, "receipts": receipts, "anchors": sorted(anchors),
            "transfer_patterns": transfers, "monetary_entities": monetary}


def _compute_verdict(state: dict[str, Any]) -> tuple[str, dict[str, list[str]]]:
    checks = state.get("integrity") or _check_integrity(state)
    blocking: list[str] = []
    expected_limitations: list[str] = []
    pending_operations: list[str] = []

    for name in ("all_decisions", "all_conservation", "all_anchors"):
        if not bool(checks.get(name)):
            blocking.append(name)

    diagnostics = state.get("copilots", {})
    soc_diagnostics = diagnostics.get("soc", {}).get("diagnostics") or {}
    soc_conservation = soc_diagnostics.get("conservation") or {}
    soc_status = str(
        soc_conservation.get("conservation_status")
        or soc_conservation.get("status")
        or ""
    ).upper()
    soc_non_scorable = soc_status in {"RED", "CALIBRATING"}

    if not bool(checks.get("all_fingerprints")):
        if soc_non_scorable and checks.get("fingerprints", {}).get("soc", 0) == 0:
            expected_limitations.append("soc:fingerprints")
        else:
            blocking.append("all_fingerprints")
    if not bool(checks.get("all_receipts")):
        if soc_non_scorable and checks.get("receipts", {}).get("soc", 0) == 0:
            expected_limitations.append("soc:evidence_receipts")
        else:
            blocking.append("all_receipts")

    for domain in EXPECTED_DOMAINS:
        if checks.get("checkpoints", {}).get(domain, 0) == 0:
            expected_limitations.append(f"{domain}:checkpoints")

    if not bool(checks.get("transfer_patterns")):
        pending_operations.append("transfer_patterns")
    if not bool(checks.get("monetary_entities")):
        pending_operations.append("monetary_entities")

    categories = {
        "blocking": blocking,
        "expected_limitations": expected_limitations,
        "pending_operations": pending_operations,
    }
    return ("READY" if not blocking else "NOT READY", categories)


def collect_platform_state(age_dsn: str, graph_name: str = "soc_graph") -> dict[str, Any]:
    state: dict[str, Any] = {"timestamp": datetime.now(timezone.utc).isoformat(), "graph_name": graph_name,
                             "age": _collect_age_state(age_dsn, graph_name), "copilots": {}, "census": {}, "integrity": {}}
    for domain, port in COPILOT_PORTS.items():
        try:
            state["copilots"][domain] = _collect_copilot_state(domain, port)
        except Exception as exc:
            state["copilots"][domain] = {"domain": domain, "port": port, "errors": [f"collector_error: {exc}"]}
    try:
        state["census"] = run_census(age_dsn, graph_name)
    except Exception as exc:
        state["census"] = {"graph_name": graph_name, "sections": {}, "errors": [f"census_error: {exc}"]}
    state["integrity"] = _check_integrity(state)
    state["verdict"], state["blocking_issues"] = _compute_verdict(state)
    return state


def dump_to_file(state: dict[str, Any], output_dir: str | os.PathLike[str] = "out") -> Path:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = directory / f"platform_dump_{stamp}.json"
    path.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
    return path


def print_summary(state: dict[str, Any], dump_path: Path | None = None) -> None:
    print(f"Platform dump — {state.get('timestamp', 'unavailable')}")
    for domain, item in state.get("copilots", {}).items():
        diagnostics = item.get("diagnostics") or {}
        artifacts = diagnostics.get("graph_artifacts") or {}
        conservation = diagnostics.get("conservation") or {}
        print(f"{domain:12} port={item.get('port')} health={item.get('health_status', 'unavailable')} "
              f"conservation={conservation.get('conservation_status', 'unavailable')} "
              f"D={artifacts.get('decisions', 'unavailable')} C={artifacts.get('conservation_snapshots', 'unavailable')} "
              f"CP={artifacts.get('centroid_checkpoints', 'unavailable')} F={artifacts.get('fingerprints', 'unavailable')} "
              f"R={artifacts.get('evidence_receipts', 'unavailable')}")
    integrity = state.get("integrity", {})
    print(f"Census total nodes: {state.get('age', {}).get('total_nodes', 'unavailable')}")
    print(f"VERDICT: {state.get('verdict', 'NOT READY')}")
    categories = state.get("blocking_issues") or {}
    if isinstance(categories, dict):
        for label in ("blocking", "expected_limitations", "pending_operations"):
            values = categories.get(label) or []
            if values:
                print(f"{label.replace('_', ' ').title()}: " + ", ".join(values))
    elif categories:
        print("Blocking issues: " + ", ".join(categories))
    if dump_path is not None:
        print(f"Saved: {dump_path}")
