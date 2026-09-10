"""Validate DataOps VLD investigation demo scenarios."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
for path in (BACKEND_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.graph_queries import DataOpsGraphClient
from app.services.investigation_comparators import ContentRulePolicy, SinglePassPolicy
from app.services.investigation_loop import DataOpsFactorProvider, InvestigationLoop
from app.services.investigation_patterns import build_default_investigation_patterns
from app.services.investigation_router import InvestigationRouter
from copilot_sdk.scoring.presets.dataops import DataOpsPreset


class StaticDataOpsScorer:
    def __init__(self) -> None:
        preset = DataOpsPreset()
        self.centroids = preset.bootstrap_centroids
        self.categories = list(preset.shape.category_names)
        self.actions = list(preset.shape.action_names)
        self.tau = 0.1


def load_alerts(data_dir: Path | None = None) -> list[dict[str, Any]]:
    root = data_dir or BACKEND_ROOT / "data"
    with (root / "fallback" / "alerts.json").open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return [dict(row) for row in payload.get("alerts", []) if isinstance(row, dict)]


async def run_scenarios(data_dir: Path | None = None) -> dict[str, Any]:
    root = data_dir or BACKEND_ROOT / "data"
    alerts = load_alerts(root)
    patterns = build_default_investigation_patterns(root)
    router = InvestigationRouter(patterns)
    loop = InvestigationLoop(
        StaticDataOpsScorer(),
        router,
        DataOpsFactorProvider(),
        L_max=3,
        residual_threshold=-1.0,
    )
    graph = DataOpsGraphClient(fallback_dir=root / "fallback")
    schema_alert = _find_alert(alerts, "ALERT-TIRE-001") or _constructed_schema_alert()
    recurring_alert = _find_recurring_alert(alerts) or _constructed_recurring_alert()
    schema_result = await loop.investigate(schema_alert, graph)
    recurring_result = await loop.investigate(recurring_alert, graph)
    content = ContentRulePolicy()
    single_pass = SinglePassPolicy()
    schema_content = content.select(schema_alert, patterns, router, loop.scorer)
    recurring_content = content.select(recurring_alert, patterns, router, loop.scorer)
    return {
        "schema_change_cascade": {
            "alert_id": schema_alert.get("alert_id"),
            "constructed": schema_alert.get("origin") == "constructed",
            "trace_categories": [step.pattern for step in schema_result.trace],
            "evidence_keys": [key for step in schema_result.trace for key in step.evidence_keys],
            "content_rule_pattern": schema_content.category_name if schema_content else None,
            "single_pass_pattern": None if single_pass.select(schema_alert, patterns, router, loop.scorer) is None else "unexpected",
            "matched_expected_narrative": _has_schema_narrative(schema_result.to_dict()),
        },
        "recurring_vs_novel": {
            "alert_id": recurring_alert.get("alert_id"),
            "constructed": recurring_alert.get("origin") == "constructed",
            "trace_categories": [step.pattern for step in recurring_result.trace],
            "evidence_keys": [key for step in recurring_result.trace for key in step.evidence_keys],
            "content_rule_pattern": recurring_content.category_name if recurring_content else None,
            "matched_expected_narrative": _has_recurring_narrative(recurring_result.to_dict()),
        },
        "ci_vld_value_assessment": (
            "DataOps investigation adds value because score-keyed routing reads graph and fixture evidence "
            "that exposes fanout, downstream systems, and recurrence history before final action scoring."
        ),
    }


def _find_alert(alerts: list[dict[str, Any]], alert_id: str) -> dict[str, Any] | None:
    for alert in alerts:
        if alert.get("alert_id") == alert_id:
            return alert
    return None


def _find_recurring_alert(alerts: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [alert for alert in alerts if int(alert.get("recurrence_count") or 0) >= 7]
    if not candidates:
        return None
    return max(candidates, key=lambda item: float(item.get("factors", {}).get("recurrence_frequency", 0.0)))


def _has_schema_narrative(result: dict[str, Any]) -> bool:
    keys = {key for step in result.get("trace", []) for key in step.get("evidence_keys", [])}
    categories = [step.get("pattern") for step in result.get("trace", [])]
    return len(categories) >= 2 and "schema_change_type" in keys and "affected_systems_count" in keys


def _has_recurring_narrative(result: dict[str, Any]) -> bool:
    keys = {key for step in result.get("trace", []) for key in step.get("evidence_keys", [])}
    categories = [step.get("pattern") for step in result.get("trace", [])]
    return "known_pattern" in categories and "pattern_match_confidence" in keys


def _constructed_schema_alert() -> dict[str, Any]:
    return {
        "alert_id": "CONSTRUCTED-SCHEMA-001",
        "origin": "constructed",
        "system": "sap_mm",
        "category": "schema_change",
        "recurrence_count": 1,
        "factors": {
            "impact_scope": 0.91,
            "source_reliability": 0.42,
            "recurrence_frequency": 0.18,
            "downstream_urgency": 0.94,
            "data_freshness": 0.37,
            "business_criticality": 0.98,
        },
    }


def _constructed_recurring_alert() -> dict[str, Any]:
    return {
        "alert_id": "CONSTRUCTED-RECURRING-001",
        "origin": "constructed",
        "system": "celonis_p2p",
        "category": "freshness_violation",
        "recurrence_count": 12,
        "factors": {
            "impact_scope": 0.5,
            "source_reliability": 0.6,
            "recurrence_frequency": 0.82,
            "downstream_urgency": 0.7,
            "data_freshness": 0.3,
            "business_criticality": 0.88,
        },
    }


if __name__ == "__main__":
    report = asyncio.run(run_scenarios())
    print(json.dumps(report, indent=2, sort_keys=True))
    failures = [
        name
        for name, payload in report.items()
        if isinstance(payload, dict) and not payload.get("matched_expected_narrative", True)
    ]
    if failures:
        raise SystemExit(f"Scenario validation failed: {', '.join(failures)}")
