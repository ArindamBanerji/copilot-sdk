#!/usr/bin/env python
"""Truth checks for the live demo.

This is deliberately a read-only checker.  It never repairs state and never
turns synthetic data into a measured claim; missing proof surfaces are errors.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass
from http.client import HTTPException
from typing import Any, Iterable
from urllib import error, request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from copilot_sdk.evidence.f26 import scan_for_sample
except ImportError:  # pragma: no cover - only useful for a broken checkout
    scan_for_sample = None


@dataclass(frozen=True)
class CopilotSpec:
    name: str
    url: str
    health: tuple[str, ...]
    trajectory: tuple[str, ...]
    claims: tuple[str, ...]
    twins: tuple[str, ...]
    promotions: tuple[str, ...]
    metrics: tuple[str, ...]


def _url(name: str, port: int) -> str:
    return os.environ.get("%s_URL" % name.upper(), "http://127.0.0.1:%s" % port)


SPECS = {
    "soc": CopilotSpec("soc", _url("soc", 8001), ("/health",), ("/api/soc/learning-health",),
                        ("/api/soc/claims", "/api/evidence/summary"), ("/api/soc/frozen-twin", "/api/frozen-twin/status"),
                        ("/api/soc/promotion", "/api/promotion"), ("/api/soc/learning-health",)),
    "trading": CopilotSpec("trading", _url("trading", 8010), ("/health",), ("/api/trajectory",),
                            ("/api/trading/claims", "/api/evidence/summary", "/api/trading/evidence"),
                            ("/api/trading/frozen-twin", "/api/frozen-twin/status", "/api/twin/status"),
                            ("/api/trading/promotion/dashboard", "/api/trading/promotion"),
                            ("/api/trajectory", "/api/trading/learning-health")),
    "purchasing": CopilotSpec("purchasing", _url("purchasing", 8020), ("/health",), ("/api/trajectory",),
                               ("/api/purchasing/claims", "/api/evidence/summary", "/api/purchasing/proof-ledger"),
                               ("/api/purchasing/frozen-twin", "/api/frozen-twin/status"),
                               ("/api/purchasing/promotion",),
                               ("/api/purchasing/proof-ledger", "/api/purchasing/day-0-readiness")),
    "dataops": CopilotSpec("dataops", _url("dataops", 8030), ("/health",), ("/api/trajectory",),
                            ("/api/dataops/claims", "/api/evidence/summary"), ("/api/dataops/frozen-twin/status",),
                            ("/api/dataops/promotion",), ("/api/dataops/claims", "/api/dataops/holdout/status")),
    "s2p": CopilotSpec("s2p", _url("s2p", 8002), ("/health",), ("/api/trajectory", "/api/s2p/trajectory"),
                        ("/api/s2p/claims", "/api/evidence/summary", "/api/s2p/evidence"),
                        ("/api/s2p/frozen-twin", "/api/frozen-twin/status", "/api/twin/status"),
                        ("/api/s2p/promotion", "/api/promotion"), ("/api/s2p/trajectory",)),
}


class PreflightApiError(RuntimeError):
    """Classified request failure; only missing routes may be tried as aliases."""

    def __init__(self, path: str, classification: str, detail: str, status: int | None = None) -> None:
        super().__init__(f"GET {path}: {classification}: {detail}")
        self.classification = classification
        self.status = status


class PreflightClient:
    def get(self, base_url: str, path: str) -> Any:
        req = request.Request(base_url.rstrip("/") + path, headers={"Accept": "application/json"})
        try:
            with request.urlopen(req, timeout=10) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except error.HTTPError as exc:
            try:
                raw = exc.read(513)
                snippet = raw[:512].decode("utf-8", errors="replace")
                if len(raw) > 512:
                    snippet += "... [truncated]"
                body_detail = repr(snippet) if snippet else "<empty>"
            except (OSError, HTTPException, ValueError) as body_error:
                body_detail = f"<unavailable: {type(body_error).__name__}: {body_error}>"
            finally:
                try:
                    exc.close()
                except (OSError, HTTPException) as close_error:
                    body_detail += f"; close failed: {type(close_error).__name__}: {close_error}"
            detail = f"HTTP {exc.code} {exc.reason}; body={body_detail}"
            raise PreflightApiError(req.full_url, "http_error", detail, exc.code) from exc
        except error.URLError as exc:
            classification = "timeout" if isinstance(exc.reason, TimeoutError) else "connection_error"
            raise PreflightApiError(req.full_url, classification, str(exc.reason)) from exc
        except TimeoutError as exc:
            raise PreflightApiError(req.full_url, "timeout", str(exc)) from exc
        except OSError as exc:
            raise PreflightApiError(req.full_url, "connection_error", str(exc)) from exc
        except (HTTPException, UnicodeError, json.JSONDecodeError) as exc:
            raise PreflightApiError(req.full_url, "invalid_response", str(exc)) from exc


def _first_available(client: PreflightClient, spec: CopilotSpec, paths: Iterable[str]) -> tuple[str, Any] | None:
    for path in paths:
        try:
            return path, client.get(spec.url, path)
        except PreflightApiError as exc:
            if exc.status not in {404, 405}:
                raise
    return None


def _walk(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _has_positive(value: Any, keys: tuple[str, ...]) -> bool:
    for item in _walk(value):
        for key in keys:
            raw = item.get(key)
            try:
                if raw is not None and float(raw) > 0:
                    return True
            except (TypeError, ValueError):
                continue
    return False


def _has_green(value: Any) -> bool:
    for item in _walk(value):
        for key in ("phase", "status", "conservation_status", "conservation_phase"):
            if str(item.get(key, "")).upper() == "GREEN":
                return True
    return False


def _has_verified(value: Any) -> bool:
    return _has_positive(value, ("verified_count", "verified_outcomes", "outcomes_verified", "confirmed_count"))


def _check_no_sample(name: str, path: str, payload: Any, failures: list[str]) -> None:
    if isinstance(payload, list):
        for index, item in enumerate(payload):
            item_path = f"{path}[{index}]"
            if isinstance(item, dict):
                _check_no_sample(name, item_path, item, failures)
            else:
                print(f"WARNING: {name} {item_path}: unexpected metric response shape "
                      f"{type(item).__name__}; expected a dictionary element", file=sys.stderr)
                if isinstance(item, list):
                    # Preserve nested F-27 enforcement as well as list indices.
                    _check_no_sample(name, item_path, item, failures)
        return
    if not isinstance(payload, dict):
        print(f"WARNING: {name} {path}: unexpected metric response shape "
              f"{type(payload).__name__}; expected a dictionary or list", file=sys.stderr)
        return
    if scan_for_sample is not None:
        findings = scan_for_sample(payload)
        if findings:
            failures.append("%s %s: F-26 sample/demo-fixture metric (%s)" % (name, path, findings))
    for item in _walk(payload):
        for key, value in item.items():
            if key in {"evidence_label", "label", "provenance"} and str(value).lower() in {"measured", "observed"}:
                source = str(item.get("source") or item.get("data_source") or item.get("provenance") or "").lower()
                if "synthetic" in source or "sample" in source or "fixture" in source or "demo" in source:
                    failures.append("%s %s: F-27 synthetic value labeled measured" % (name, path))


def _nonblank_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


# Wire values from the shared PromotionStage and Trading's category pipeline.
_PROMOTION_STAGES = {"discovered", "shadowing", "promoted", "measuring", "kept", "rolled_back", "transferred"}
_TRADING_STAGES = {"paper", "small_live", "full_live"}


def _promotion_record(value: Any) -> bool:
    if not isinstance(value, dict) or value.get("error"):
        return False
    flags = [value[key] for key in ("promoted", "eligible") if key in value]
    if flags:
        return all(isinstance(flag, bool) for flag in flags)
    stage = value.get("current_stage")
    if "record_id" in value:
        return (all(_nonblank_text(value.get(key)) for key in ("record_id", "copilot", "decision_class"))
                and isinstance(stage, str) and stage in _PROMOTION_STAGES)
    if "current_stage" in value:
        return (_nonblank_text(value.get("category")) and isinstance(stage, str) and stage in _TRADING_STAGES
                and isinstance(value.get("ready"), bool))
    # Compact lifecycle summaries and rule records used by existing callers.
    stage = value.get("stage")
    if "stage" in value:
        return isinstance(stage, str) and stage in _PROMOTION_STAGES
    if "rule_id" in value:
        status = value.get("status")
        return _nonblank_text(value["rule_id"]) and isinstance(status, str) and status in _PROMOTION_STAGES
    return (_nonblank_text(value.get("id")) and _finite_number(value.get("score")))


def _has_promotion_artifact(payload: Any) -> bool:
    if isinstance(payload, list):
        return bool(payload) and all(_has_promotion_artifact(row) for row in payload)
    if not isinstance(payload, dict) or payload.get("error"):
        return False
    if any(key in payload for key in ("promoted", "eligible")):
        return _promotion_record(payload)
    collections = [payload[key] for key in ("candidates", "promotions", "records") if key in payload]
    if collections:
        # Do not recurse into malformed collections and accept an isolated field.
        return all(isinstance(rows, list) and bool(rows) and all(_promotion_record(row) for row in rows)
                   for rows in collections)
    if _promotion_record(payload):
        return True
    return any(_has_promotion_artifact(child) for child in payload.values() if isinstance(child, (dict, list)))


def _purchasing_twin_status(item: dict[str, Any]) -> bool:
    timestamp = item.get("snapshot_time")
    if (item.get("available") is not True or item.get("status") != "FROZEN"
            or not _nonblank_text(item.get("checksum"))
            or not (_nonblank_text(timestamp) or (isinstance(timestamp, (int, float))
                                                  and _finite_number(timestamp) and timestamp >= 0))):
        return False
    learning, frozen = item.get("learning_curve"), item.get("frozen_curve")
    # Empty paired curves are legitimate immediately after capturing a snapshot.
    return (isinstance(learning, list) and isinstance(frozen, list) and len(learning) == len(frozen)
            and all(isinstance(row, dict) and _finite_number(row.get("accuracy"))
                    and 0 <= row["accuracy"] <= 1 for row in learning + frozen))


def _has_artifact(payload: Any, kind: str) -> bool:
    """Require artifact data, not merely a successful health/error envelope."""
    def nonempty(value: Any) -> bool:
        return (isinstance(value, str) and bool(value.strip())) or (
            isinstance(value, (dict, list)) and bool(value)
        )

    if kind == "promotions":
        return _has_promotion_artifact(payload)

    for item in _walk(payload):
        if kind == "claims":
            has_id = isinstance(item.get("claim_id"), str) and bool(item["claim_id"].strip())
            if "confidence" in item and not _finite_number(item["confidence"]):
                continue
            has_detail = (
                (isinstance(item.get("status"), str) and bool(item["status"].strip()))
                or _finite_number(item.get("confidence"))
                or any(isinstance(item.get(key), (dict, list)) and bool(item[key])
                       for key in ("evidence", "factors"))
            )
            if has_id and has_detail:
                return True
        elif kind == "twins":
            has_id = any(isinstance(item.get(key), str) and bool(item[key].strip())
                         for key in ("twin_id", "snapshot_id"))
            has_comparison = (
                any(_finite_number(item.get(key)) for key in ("delta", "divergence"))
                or any(isinstance(item.get(key), (dict, list)) and bool(item[key])
                       for key in ("current_vs_frozen", "comparison"))
            )
            count = item.get("decision_count")
            has_status = isinstance(item.get("frozen"), bool) and (
                (isinstance(item.get("snapshot_time"), str) and bool(item["snapshot_time"].strip()))
                or (isinstance(count, int) and not isinstance(count, bool) and count >= 0)
            )
            if (has_id and has_comparison) or has_status or _purchasing_twin_status(item):
                return True
        else:
            recognized = (
                "claim_id", "status", "confidence", "evidence", "factors", "twin_id", "snapshot_id",
                "current_vs_frozen", "delta", "divergence", "comparison", "promoted", "eligible",
                "candidates", "promotions",
            )
            if sum(1 for key in recognized if key in item and nonempty(item[key])) >= 2:
                return True
    return False


def check_copilot(spec: CopilotSpec, client: PreflightClient | None = None) -> list[str]:
    active_client = client or PreflightClient()
    failures: list[str] = []

    def probe(paths: Iterable[str], label: str) -> tuple[str, Any] | None:
        try:
            result = _first_available(active_client, spec, paths)
        except RuntimeError as exc:
            classification = exc.classification if isinstance(exc, PreflightApiError) else "client_error"
            failures.append(f"{spec.name}: {label} request failed [{classification}]: {exc}")
            return None
        if result is None:
            failures.append(f"{spec.name}: {label} unavailable")
        return result

    if scan_for_sample is None:
        print("WARNING: F-26 sample scan unavailable (copilot_sdk.evidence.f26 not importable)", file=sys.stderr)
    health = probe(spec.health, "backend")
    if health is None:
        return failures
    trajectory = probe(spec.trajectory, "verified trajectory endpoint")
    if trajectory is not None:
        path, payload = trajectory
        _check_no_sample(spec.name, path, payload, failures)
        if not _has_positive(payload, ("current_iks", "iks", "intelligence_knowledge_score")):
            failures.append("%s: IKS is not positive" % spec.name)
        if not _has_verified(payload):
            failures.append("%s: no verified outcomes reported" % spec.name)
        if not _has_green(payload):
            failures.append("%s: conservation is not GREEN" % spec.name)
    metrics_seen = False
    for path in spec.metrics:
        try:
            payload = active_client.get(spec.url, path)
        except RuntimeError as exc:
            if isinstance(exc, PreflightApiError) and exc.status in {404, 405}:
                continue
            classification = exc.classification if isinstance(exc, PreflightApiError) else "client_error"
            failures.append(f"{spec.name} {path}: metric request failed [{classification}]: {exc}")
            break
        metrics_seen = True
        _check_no_sample(spec.name, path, payload, failures)
    if not metrics_seen:
        failures.append("%s: no metric/evidence surface available" % spec.name)
    for kind, label, paths in (
        ("claims", "claim registry", spec.claims),
        ("twins", "Frozen Twin", spec.twins),
        ("promotions", "promotion records", spec.promotions),
    ):
        result = probe(paths, label)
        if result is not None and not _has_artifact(result[1], kind):
            failures.append("%s: %s returned empty or unrelated payload" % (spec.name, label))
    return failures


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only demo truth preflight")
    parser.add_argument("--copilots", nargs="+", choices=sorted(SPECS), default=sorted(SPECS))
    parser.add_argument("--dry-run", action="store_true", help="Validate configuration without contacting backends")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if args.dry_run:
        print("preflight configuration: OK (%s)" % ", ".join(args.copilots))
        return 0
    failures: list[str] = []
    for name in args.copilots:
        failures.extend(check_copilot(SPECS[name]))
    if failures:
        print("DEMO TRUTH PREFLIGHT: FAIL")
        for failure in failures:
            print("  FAIL: %s" % failure)
        return 1
    print("DEMO TRUTH PREFLIGHT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
