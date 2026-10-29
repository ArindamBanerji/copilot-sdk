#!/usr/bin/env python3
"""Trace SDK-FIXTURES seed_purchasing() conservation failure.

Run from copilot-sdk root with Purchasing backend running on :8020:
    python scripts/trace_preseed_fixtures.py

Outputs: docs/preseed_fixtures_trace.md
"""

from __future__ import annotations

import ast
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx


REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://localhost:8020"
OUTPUT_PATH = REPO_ROOT / "docs" / "preseed_fixtures_trace.md"
FIXTURE_PATH = REPO_ROOT / "scripts" / "preseed_demo_fixtures.py"
SEED_PATH = (
    REPO_ROOT
    / "apps"
    / "purchasing"
    / "backend"
    / "data"
    / "purchasing_seed_v2.json"
)
FACTORS = (
    "expected_demand",
    "day_of_week",
    "weather_forecast",
    "event_flag",
    "historical_waste",
    "supplier_lead_time",
    "price_memory_index",
)
FIELD_MAP = {"day_of_week": "day_of_week_factor"}
ACTIONS = ("order_as_planned", "order_more", "order_less", "skip")
CONSERVATION_KEYS = (
    "status",
    "reason",
    "conservation_status",
    "conservation_mode",
    "conservation_applicable",
    "q",
    "alpha",
    "V",
    "theta_min",
    "verified_count",
    "correct_count",
    "category_coverage",
    "override_rate",
    "recent_q",
    "recent_window",
    "passed",
    "blocked_by_gate",
    "paused",
    "pause_reason",
)

JsonDict = dict[str, Any]


def _json_block(value: Any) -> str:
    return "```json\n" + json.dumps(value, indent=2, sort_keys=True, default=str) + "\n```"


def _request(
    client: httpx.Client,
    method: str,
    path: str,
    payload: JsonDict | None = None,
) -> JsonDict:
    """Return the complete observable HTTP response without raising for HTTP status."""
    try:
        response = client.request(method, path, json=payload)
        try:
            body: Any = response.json()
        except (json.JSONDecodeError, ValueError):
            body = response.text
        return {
            "method": method,
            "url": str(response.request.url),
            "request_body": payload,
            "status_code": response.status_code,
            "response_body": body,
        }
    except Exception as exc:
        return {
            "method": method,
            "url": BASE_URL.rstrip("/") + path,
            "request_body": payload,
            "exception": f"{type(exc).__name__}: {exc}",
        }


def _body(result: JsonDict) -> JsonDict:
    body = result.get("response_body")
    return body if isinstance(body, dict) else {}


def _connection_failed(result: JsonDict) -> bool:
    return "exception" in result and isinstance(
        result.get("exception"), str
    ) and any(
        marker in str(result["exception"])
        for marker in ("ConnectError", "Connection refused", "WinError 10061")
    )


def _coerce_factor(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.5
    if not math.isfinite(number):
        return 0.5
    return max(0.0, min(1.0, number))


def _load_fixture_rows() -> list[JsonDict]:
    payload = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"Purchasing seed must be a non-empty list: {SEED_PATH}")
    return [dict(row) for row in payload if isinstance(row, dict)]


def _fixture_score_payload(rows: list[JsonDict], index: int) -> JsonDict:
    """Match score_outcome() in preseed_demo_fixtures.py for Purchasing."""
    row = rows[index % len(rows)]
    nested = row.get("factors")
    nested_factors = nested if isinstance(nested, dict) else {}
    factors: dict[str, float] = {}
    for factor in FACTORS:
        raw = (
            nested_factors.get(factor)
            if factor in nested_factors
            else row.get(FIELD_MAP.get(factor, factor))
        )
        factors[factor] = _coerce_factor(raw)
    provenance = {
        "planted": True,
        "provenance": "sample",
        "evidence_tier": "T-sim",
        "fixture": "SDK-PRESEED",
        "seed_index": index,
    }
    return {
        "category": row["category"],
        "factors": factors,
        "metadata": dict(provenance),
        "context": provenance,
    }


def _incorrect_action(recommended: Any) -> str:
    action = str(recommended or "")
    return next(candidate for candidate in ACTIONS if candidate != action)


def _conservation_fields(payload: JsonDict) -> JsonDict:
    fields = {key: payload[key] for key in CONSERVATION_KEYS if key in payload}
    gate = payload.get("gate_status")
    if isinstance(gate, dict):
        fields["gate_status"] = gate
    return fields


def _decision_count(health: JsonDict, conservation: JsonDict) -> JsonDict:
    for key in ("decision_count", "decisions_total", "total_decisions"):
        if key in health:
            return {"value": health[key], "source": f"health.{key}"}
    for key in ("decision_count", "decisions_total", "total_decisions", "V"):
        if key in conservation:
            return {"value": conservation[key], "source": f"conservation_status.{key}"}
    return {"value": None, "source": "not present in health or conservation response"}


def _seed_purchasing_source() -> JsonDict:
    try:
        source = FIXTURE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        function = next(
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "seed_purchasing"
        )
        excerpt = ast.get_source_segment(source, function) or ""
        uses_per_decision_evidence = (
            '"conservation_status" in result' in excerpt
            and 'result["conservation_status"] == "RED"' in excerpt
        )
        return {
            "source_file": str(FIXTURE_PATH.relative_to(REPO_ROOT)),
            "function_source": excerpt,
            "uses_per_decision_evidence": uses_per_decision_evidence,
            "endpoint_checked": (
                'POST /api/learn response["conservation_status"] (primary); '
                "GET /api/conservation/status (returned as secondary context)"
                if uses_per_decision_evidence
                else "GET /api/conservation/status"
            ),
            "condition_expected": (
                "At least one learn response must contain the explicit top-level "
                'field conservation_status with value "RED".'
                if uses_per_decision_evidence
                else "After up to 20 alternating correct/incorrect outcomes, aggregate "
                "status must not be GREEN and passed must be false."
            ),
        }
    except Exception as exc:
        return {
            "source_file": str(FIXTURE_PATH.relative_to(REPO_ROOT)),
            "exception": f"{type(exc).__name__}: {exc}",
        }


def _math(status: JsonDict) -> JsonDict:
    try:
        alpha = float(status["alpha"])
        q = float(status["q"])
        verified = float(status["V"])
        computed = 23.53 / (alpha * verified)
        endpoint_theta = status.get("theta_min")
        signal = alpha * q * verified
        theta_value = float(endpoint_theta) if endpoint_theta is not None else computed
        return {
            "alpha": alpha,
            "q": q,
            "V": verified,
            "theta_min_computed": computed,
            "theta_min_from_endpoint": endpoint_theta,
            "q_vs_theta_min": {
                "q": q,
                "relation": "below" if q < theta_value else "at_or_above",
                "theta_min": theta_value,
            },
            "aggregate_signal_alpha_q_V": signal,
            "would_be_RED": signal < theta_value,
            "formula_note": (
                "The aggregate endpoint compares alpha*q*V with theta_min. "
                "q alone is also shown because the per-decision recent-quality "
                "gate can compare q with a fixed threshold."
            ),
        }
    except Exception as exc:
        return {"exception": f"{type(exc).__name__}: {exc}", "input": status}


def _per_decision_comparison(
    decisions: list[JsonDict], aggregate: JsonDict
) -> JsonDict:
    learn_fields: list[JsonDict] = []
    statuses: list[str] = []
    for item in decisions:
        fields = item.get("learn_conservation_fields")
        if not isinstance(fields, dict):
            continue
        learn_fields.append(fields)
        status = fields.get("conservation_status")
        if status is None and fields.get("reason") == "conservation_red":
            status = "RED"
        if status is None and fields.get("pause_reason") == "conservation_red":
            status = "RED"
        if status is not None:
            statuses.append(str(status))
    aggregate_status = aggregate.get("status")
    mismatch = bool(statuses) and any(
        status != str(aggregate_status) for status in statuses
    )
    return {
        "learn_response_has_conservation": bool(learn_fields),
        "per_decision_conservation_status": statuses or None,
        "per_decision_conservation_fields": learn_fields,
        "aggregate_conservation_status": aggregate_status,
        "mismatch": mismatch,
    }


def _diagnosis(
    unavailable: bool,
    post_status: JsonDict,
    comparison: JsonDict,
    math_result: JsonDict,
    fixture_uses_per_decision_evidence: bool,
) -> str:
    if unavailable:
        return (
            "The Purchasing backend was unavailable on localhost:8020, so the live "
            "conservation behavior could not be diagnosed. The source inspection "
            "still confirms that seed_purchasing() checks the aggregate conservation endpoint."
        )
    aggregate = str(post_status.get("status") or "unknown")
    per_status = comparison.get("per_decision_conservation_status")
    if aggregate == "GREEN" and per_status and "RED" in per_status:
        if fixture_uses_per_decision_evidence:
            return (
                "The live endpoint mismatch remains reproducible: /api/learn reports "
                "per-decision conservation RED while /api/conservation/status remains "
                "GREEN. The updated seed_purchasing() now validates the explicit "
                "top-level learn-response conservation_status field, so this trace "
                "provides the evidence the fixture expects."
            )
        return (
            "The trace confirms an endpoint-semantics mismatch: at least one /api/learn "
            "response reported per-decision conservation RED while "
            "/api/conservation/status remained GREEN. seed_purchasing() only checks the "
            "aggregate endpoint, whose accumulated verified volume keeps alpha*q*V above "
            "theta_min, so its expected aggregate degradation is not observed."
        )
    if aggregate == "GREEN":
        signal = math_result.get("aggregate_signal_alpha_q_V")
        threshold = math_result.get("theta_min_from_endpoint")
        return (
            "The five forced incorrect outcomes did not turn the aggregate endpoint RED. "
            f"After the probe, alpha*q*V={signal!r} and theta_min={threshold!r}; the "
            "existing verified history dominates this small degradation sequence. "
            "seed_purchasing() expects that aggregate endpoint to become non-GREEN after "
            "only 20 roughly 50%-accurate fixture outcomes, so its failure condition is "
            "incompatible with the accumulated preseed state."
        )
    return (
        f"The five forced incorrect outcomes produced aggregate status {aggregate}. "
        "This run therefore reproduced aggregate degradation; inspect the raw per-decision "
        "responses above to determine whether a separate learn-response gate also fired."
    )


def _render_report(results: JsonDict) -> str:
    probe1 = results["probe1"]
    probe2 = results["probe2"]
    probe3 = results["probe3"]
    probe4 = results["probe4"]
    probe5 = results["probe5"]
    lines = [
        "# SDK-FIXTURES Conservation Trace",
        "",
        f"Date: {results['timestamp']}",
        "Target: Purchasing backend on localhost:8020",
        "",
        "## PROBE 1: Pre-State",
        "",
        "health:",
        _json_block(probe1["health"]),
        "",
        "conservation_status:",
        _json_block(probe1["conservation_status"]),
        "",
        f"decision_count: `{probe1['decision_count'].get('value')}` "
        f"(source: `{probe1['decision_count'].get('source')}`)",
        f"theta_min: `{probe1.get('theta_min')}`",
        f"q: `{probe1.get('q')}`",
        "",
        "## PROBE 2: Degradation Sequence (5 decisions)",
        "",
    ]
    decisions = probe2.get("decisions", [])
    if decisions:
        for decision in decisions:
            lines.extend(
                [
                    f"### Decision {decision['probe_index']} (fixture seed index {decision['seed_index']})",
                    "",
                    "conservation_before:",
                    _json_block(decision["conservation_before"]),
                    "",
                    "score_response summary:",
                    _json_block(decision["score_summary"]),
                    "",
                    "score_response full:",
                    _json_block(decision["score_response"]),
                    "",
                    "learn_response summary (including conservation fields):",
                    _json_block(decision["learn_summary"]),
                    "",
                    "learn_response full:",
                    _json_block(decision["learn_response"]),
                    "",
                    "conservation_after:",
                    _json_block(decision["conservation_after"]),
                    "",
                ]
            )
    else:
        lines.extend(["No degradation decisions were sent.", ""])
    if probe2.get("exceptions"):
        lines.extend(["Probe exceptions:", _json_block(probe2["exceptions"]), ""])
    lines.extend(
        [
            "Post-degradation conservation_status:",
            _json_block(probe2["post_degradation_conservation_status"]),
            "",
            "## PROBE 3: Conservation Math",
            "",
            _json_block(probe3),
            "",
            "## PROBE 4: Per-Decision vs Aggregate",
            "",
            _json_block(probe4),
            "",
            "## PROBE 5: seed_purchasing() Failure Condition",
            "",
            f"endpoint_checked: `{probe5.get('endpoint_checked')}`",
            "",
            f"condition_expected: {probe5.get('condition_expected')}",
            "",
            f"actual_value: `{probe5.get('actual_value')}`",
            "",
            "Source inspection:",
            _json_block(probe5),
            "",
            "## DIAGNOSIS",
            "",
            str(results["diagnosis"]),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    source_probe = _seed_purchasing_source()
    probe1: JsonDict = {}
    probe2: JsonDict = {"decisions": [], "exceptions": []}
    probe3: JsonDict = {}
    probe4: JsonDict = {}

    with httpx.Client(base_url=BASE_URL, timeout=httpx.Timeout(5.0, connect=2.0)) as client:
        health = _request(client, "GET", "/api/health")
        unavailable = _connection_failed(health)
        if unavailable:
            conservation = {
                "method": "GET",
                "url": BASE_URL + "/api/conservation/status",
                "skipped": "Purchasing backend connection failed during health probe",
            }
        else:
            conservation = _request(client, "GET", "/api/conservation/status")

        health_body = _body(health)
        conservation_body = _body(conservation)
        probe1 = {
            "health": health,
            "conservation_status": conservation,
            "decision_count": _decision_count(health_body, conservation_body),
            "theta_min": conservation_body.get("theta_min"),
            "q": conservation_body.get("q"),
        }

        if not unavailable:
            try:
                rows = _load_fixture_rows()
                decisions = probe2["decisions"]
                assert isinstance(decisions, list)
                for offset in range(5):
                    seed_index = 30 + offset
                    item: JsonDict = {
                        "probe_index": offset + 1,
                        "seed_index": seed_index,
                    }
                    try:
                        before = _request(client, "GET", "/api/conservation/status")
                        score_payload = _fixture_score_payload(rows, seed_index)
                        score = _request(client, "POST", "/api/score", score_payload)
                        score_body = _body(score)
                        action = score_body.get("action") or score_body.get("recommended_action")
                        decision_id = score_body.get("decision_id")
                        item["conservation_before"] = before
                        item["score_response"] = score
                        item["score_summary"] = {
                            "decision_id": decision_id,
                            "action": action,
                            "score": score_body.get("score"),
                            "confidence": score_body.get("confidence"),
                        }
                        if not decision_id or not action:
                            raise RuntimeError("Incomplete /api/score response")
                        provenance = dict(score_payload["context"])
                        learn_payload = {
                            "decision_id": decision_id,
                            "actual_action": _incorrect_action(action),
                            "outcome": "overridden",
                            "context": provenance,
                        }
                        learn = _request(client, "POST", "/api/learn", learn_payload)
                        learn_body = _body(learn)
                        learn_fields = _conservation_fields(learn_body)
                        after = _request(client, "GET", "/api/conservation/status")
                        item["learn_response"] = learn
                        item["learn_conservation_fields"] = learn_fields
                        item["learn_summary"] = {
                            "http_status": learn.get("status_code"),
                            "decision_id": learn_body.get("decision_id", decision_id),
                            "outcome": learn_body.get("outcome"),
                            "conservation_fields": learn_fields,
                        }
                        item["conservation_after"] = after
                    except Exception as exc:
                        item["exception"] = f"{type(exc).__name__}: {exc}"
                        exceptions = probe2["exceptions"]
                        assert isinstance(exceptions, list)
                        exceptions.append(item["exception"])
                        item.setdefault("conservation_before", {})
                        item.setdefault("score_response", {})
                        item.setdefault("score_summary", {})
                        item.setdefault("learn_response", {})
                        item.setdefault("learn_conservation_fields", {})
                        item.setdefault("learn_summary", {})
                        item.setdefault("conservation_after", {})
                    decisions.append(item)
            except Exception as exc:
                exceptions = probe2["exceptions"]
                assert isinstance(exceptions, list)
                exceptions.append(f"{type(exc).__name__}: {exc}")

            post = _request(client, "GET", "/api/conservation/status")
        else:
            post = {
                "method": "GET",
                "url": BASE_URL + "/api/conservation/status",
                "skipped": "Purchasing backend unavailable; no mutations attempted",
            }

    probe2["post_degradation_conservation_status"] = post
    post_body = _body(post)
    probe3 = _math(post_body)
    decisions_value = probe2["decisions"]
    assert isinstance(decisions_value, list)
    probe4 = _per_decision_comparison(decisions_value, post_body)
    per_decision_statuses = probe4.get("per_decision_conservation_status")
    source_probe["actual_value"] = {
        "per_decision_conservation_status": per_decision_statuses,
        "per_decision_red_observed": (
            isinstance(per_decision_statuses, list) and "RED" in per_decision_statuses
        ),
        "aggregate_status": post_body.get("status"),
        "aggregate_passed": post_body.get("passed"),
    }
    diagnosis = _diagnosis(
        unavailable,
        post_body,
        probe4,
        probe3,
        bool(source_probe.get("uses_per_decision_evidence")),
    )
    results: JsonDict = {
        "timestamp": timestamp,
        "probe1": probe1,
        "probe2": probe2,
        "probe3": probe3,
        "probe4": probe4,
        "probe5": source_probe,
        "diagnosis": diagnosis,
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(_render_report(results), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")
    if unavailable:
        print(
            "Purchasing backend is unavailable on localhost:8020; "
            "recorded the connection failure and exited without sending decisions."
        )
    else:
        print(diagnosis)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
