"""DataOps context endpoints backed by AGE or fixture graph data."""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status

from .graph_queries import DataOpsGraphClient


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
METADATA_PATH = DATA_DIR / "alert_metadata.json"
DATAOPS_SEED_PATH = Path(__file__).resolve().parents[4] / "copilot_sdk" / "scoring" / "presets" / "dataops_seed.json"
FACTOR_NAMES = (
    "impact_scope",
    "source_reliability",
    "recurrence_frequency",
    "downstream_urgency",
    "data_freshness",
    "business_criticality",
)
DATAOPS_CATEGORIES = (
    "schema_change",
    "volume_anomaly",
    "quality_anomaly",
    "freshness_violation",
    "pipeline_failure",
    "transform_drift",
)
CATEGORY_SLA_MINUTES = {
    "pipeline_failure": 30,
    "schema_change": 60,
    "volume_anomaly": 45,
    "quality_anomaly": 30,
    "freshness_violation": 15,
    "transform_drift": 60,
}
DEFAULT_SLA_MINUTES = 30
SEVERITY_AGE_MINUTES = {
    "critical": 5,
    "high": 15,
    "medium": 25,
    "low": 40,
}
AGE_JITTER_MINUTES = (-2, -1, 0, 1, 2)

router = APIRouter()


def _graph_client() -> DataOpsGraphClient:
    return DataOpsGraphClient(fallback_dir=DATA_DIR / "fallback")


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_dataops_seed() -> list[dict[str, Any]]:
    try:
        seed = _load_json(DATAOPS_SEED_PATH, [])
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(seed, list):
        return []
    return [entry for entry in seed if isinstance(entry, dict)]


def _vector_from_factors(factors: dict[str, Any]) -> list[float]:
    vector = []
    for name in FACTOR_NAMES:
        try:
            vector.append(float(factors.get(name, 0.0)))
        except (TypeError, ValueError):
            vector.append(0.0)
    return vector


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def _normalize_system_key(system: str) -> str:
    return system.strip().lower().replace("-", "_").replace(" ", "_")


def _normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        normalized = value.replace(",", " ")
        return [item.strip() for item in normalized.split() if item.strip()]
    return []


def _get_display_name(system_name: str, pipelines: dict[str, dict[str, Any]]) -> str:
    pipeline = pipelines.get(system_name, {})
    return str(pipeline.get("display_name") or system_name)


def _get_criticality(system_name: str, pipelines: dict[str, dict[str, Any]]) -> float:
    try:
        return float(pipelines.get(system_name, {}).get("business_criticality", 0.0))
    except (TypeError, ValueError):
        return 0.0


def _find_roots(
    system: str,
    upstream_map: dict[str, list[str]],
    visited: set[str] | None = None,
) -> set[str]:
    visited = set(visited or set())
    if system in visited:
        return set()
    visited.add(system)

    upstream = upstream_map.get(system, [])
    if not upstream:
        return {system}

    roots: set[str] = set()
    for parent in upstream:
        roots.update(_find_roots(parent, upstream_map, visited))
    return roots


def _infer_system_from_dataset(dataset: str) -> str | None:
    key = _normalize_system_key(str(dataset or ""))
    if not key:
        return None

    if key.startswith("sap_mara") or key.startswith("sap_vbak") or key.startswith("sap_bseg"):
        return "sap_s4hana_extract"
    if key.startswith("sap_") or key.startswith("erp_"):
        return "sap_s4hana_extract"
    if "revenue_mart" in key or "risk_feature" in key:
        return "warehouse_etl"
    if "billing_export" in key:
        return "billing_api"
    if "customer_event" in key:
        return "crm_sync"
    if "identity_dim" in key:
        return "hr_feed"
    if "campaign_attrib" in key:
        return "marketing_db"
    if key.startswith("payments_") or key.startswith("payment_"):
        return "payment_gateway"
    if key.startswith("inventory_"):
        return "inventory_feed"
    if key.startswith("sensor_"):
        return "iot_sensors"
    return None


def _iter_metadata_decisions() -> list[dict[str, Any]]:
    metadata = _load_json(METADATA_PATH, {})
    if isinstance(metadata, dict):
        decisions = []
        for key, entry in metadata.items():
            if isinstance(entry, dict):
                enriched = dict(entry)
                enriched.setdefault("decision_id", key)
                decisions.append(enriched)
        return decisions
    if isinstance(metadata, list):
        return [entry for entry in metadata if isinstance(entry, dict)]
    return []


def _coerce_correct_filter(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    # Invalid query values are ignored so exploratory filtering cannot make the
    # endpoint look empty because of a typo.
    return None


def _correct_from_decision(entry: dict[str, Any]) -> bool | None:
    raw = entry.get("is_correct")
    if isinstance(raw, bool):
        return raw
    outcome = str(entry.get("outcome") or "").strip().lower()
    if outcome == "correct":
        return True
    if outcome == "incorrect":
        return False
    return None


def _numeric_or_none(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _alert_category_by_id() -> dict[str, str]:
    payload = _load_json(DATA_DIR / "fallback" / "alerts.json", {})
    raw_alerts = payload.get("alerts", []) if isinstance(payload, dict) else []
    categories: dict[str, str] = {}
    for alert in raw_alerts:
        if not isinstance(alert, dict):
            continue
        category = str(alert.get("category") or "").strip()
        if not category or category.lower() == "unknown":
            continue
        for key in (alert.get("alert_id"), alert.get("event_id")):
            if key:
                categories[str(key)] = category
    return categories


def _is_missing_category(value: Any) -> bool:
    return not value or str(value).strip().lower() == "unknown"


def _normalize_live_decision(entry: dict[str, Any]) -> dict[str, Any]:
    dataset = entry.get("dataset")
    system = entry.get("system_name") or entry.get("system") or entry.get("systemName")
    if not system and dataset:
        system = _infer_system_from_dataset(str(dataset))
    return {
        "decision_id": entry.get("decision_id"),
        "alert_id": entry.get("alert_id") or entry.get("event_id"),
        "event_id": entry.get("event_id") or entry.get("alert_id"),
        "system": _normalize_system_key(str(system or "")) or None,
        "dataset": dataset,
        "category": entry.get("category"),
        "action_taken": entry.get("action_taken") or entry.get("actual_action") or entry.get("actionTaken"),
        "score_action": entry.get("score_action") or entry.get("scored_action"),
        "score_confidence": _numeric_or_none(entry.get("score_confidence")),
        "outcome": entry.get("outcome"),
        "is_correct": _correct_from_decision(entry),
        "date": entry.get("date") or entry.get("timestamp") or "live",
        "source": "live_decision",
        "factors": entry.get("scored_factors") or entry.get("factors") or entry.get("seed_factors"),
    }


def _enrich_live_decision_category(
    decision: dict[str, Any],
    category_by_alert_id: dict[str, str],
) -> dict[str, Any]:
    if not _is_missing_category(decision.get("category")):
        return decision
    alert_id = decision.get("alert_id") or decision.get("event_id")
    category = category_by_alert_id.get(str(alert_id)) if alert_id else None
    if not category:
        return decision
    enriched = dict(decision)
    enriched["category"] = category
    return enriched


def _normalize_seed_decision(entry: dict[str, Any]) -> dict[str, Any]:
    dataset = entry.get("dataset")
    system = entry.get("system_name") or entry.get("system") or _infer_system_from_dataset(str(dataset or ""))
    is_correct = entry.get("is_correct")
    if not isinstance(is_correct, bool):
        is_correct = bool(is_correct)
    action = entry.get("action_taken")
    return {
        "decision_id": None,
        "alert_id": entry.get("event_id") or entry.get("alert_id"),
        "event_id": entry.get("event_id") or entry.get("alert_id"),
        "system": _normalize_system_key(str(system or "")) or None,
        "dataset": dataset,
        "category": entry.get("category"),
        "action_taken": action,
        "score_action": None,
        "score_confidence": None,
        "outcome": "correct" if is_correct else "incorrect",
        "is_correct": is_correct,
        "date": entry.get("date") or entry.get("timestamp") or "historical",
        "source": "seed_history",
        "factors": entry.get("factors"),
    }


def _decision_breakdown(decisions: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    breakdown: dict[str, dict[str, Any]] = {}
    for decision in decisions:
        key = str(decision.get(field) or "unknown")
        bucket = breakdown.setdefault(key, {"count": 0, "correct": 0, "win_rate": None})
        bucket["count"] += 1
        if decision.get("is_correct") is True:
            bucket["correct"] += 1
    for bucket in breakdown.values():
        bucket["win_rate"] = round(bucket["correct"] / bucket["count"], 3) if bucket["count"] else None
    return breakdown


def _decision_summary(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(decisions)
    correct = sum(1 for decision in decisions if decision.get("is_correct") is True)
    return {
        "total_decisions": total,
        "correct": correct,
        "accuracy": round(correct / total, 3) if total else None,
        "by_action": _decision_breakdown(decisions, "action_taken"),
        "by_category": _decision_breakdown(decisions, "category"),
    }


def _all_context_decisions() -> list[dict[str, Any]]:
    category_by_alert_id = _alert_category_by_id()
    return [
        *(
            _enrich_live_decision_category(_normalize_live_decision(entry), category_by_alert_id)
            for entry in _iter_metadata_decisions()
        ),
        *(_normalize_seed_decision(entry) for entry in _load_dataops_seed()),
    ]


def _matches_decision_filters(
    decision: dict[str, Any],
    system: str | None,
    category: str | None,
    action: str | None,
    correct_filter: bool | None,
) -> bool:
    if system and _normalize_system_key(str(decision.get("system") or "")) != _normalize_system_key(system):
        return False
    if category and decision.get("category") != category:
        return False
    if action and decision.get("action_taken") != action:
        return False
    if correct_filter is not None and decision.get("is_correct") is not correct_filter:
        return False
    return True


def _inject_alert_runtime_fields(alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_with_alert_runtime_fields(alert, index) for index, alert in enumerate(alerts)]


def _with_alert_runtime_fields(alert: dict[str, Any], index: int = 0) -> dict[str, Any]:
    enriched = dict(alert)
    enriched.setdefault("created_at", _created_at_for_alert(enriched, index))
    enriched["sla_minutes"] = _sla_minutes_for_alert(enriched)
    return enriched


def _created_at_for_alert(alert: dict[str, Any], index: int) -> str:
    age_minutes = SEVERITY_AGE_MINUTES.get(str(alert.get("severity") or "").lower(), 25)
    jitter = AGE_JITTER_MINUTES[_stable_alert_index(alert, index) % len(AGE_JITTER_MINUTES)]
    timestamp = datetime.now(timezone.utc) - timedelta(minutes=max(age_minutes + jitter, 1))
    return timestamp.isoformat(timespec="seconds").replace("+00:00", "Z")


def _stable_alert_index(alert: dict[str, Any], fallback: int) -> int:
    raw_id = str(alert.get("alert_id") or alert.get("event_id") or "")
    digits = "".join(character for character in raw_id if character.isdigit())
    return int(digits) if digits else fallback


def _sla_minutes_for_alert(alert: dict[str, Any]) -> int:
    category = str(alert.get("category") or "")
    return CATEGORY_SLA_MINUTES.get(category, DEFAULT_SLA_MINUTES)


def _fallback_alerts_by_id() -> dict[str, dict[str, Any]]:
    payload = _load_json(DATA_DIR / "fallback" / "alerts.json", {})
    raw_alerts = payload.get("alerts", []) if isinstance(payload, dict) else []
    alerts: dict[str, dict[str, Any]] = {}
    for index, alert in enumerate(raw_alerts):
        if not isinstance(alert, dict):
            continue
        enriched = _with_alert_runtime_fields(alert, index)
        for key in (enriched.get("alert_id"), enriched.get("event_id")):
            if key:
                alerts[str(key)] = enriched
    return alerts


def _metadata_for_alert(alert_id: str) -> dict[str, Any] | None:
    matches = [
        entry
        for entry in _iter_metadata_decisions()
        if str(entry.get("alert_id") or "") == alert_id or str(entry.get("event_id") or "") == alert_id
    ]
    return matches[-1] if matches else None


def _audit_variant_matches(alert: dict[str, Any], variant: dict[str, Any]) -> bool:
    match = variant.get("match") if isinstance(variant.get("match"), dict) else {}
    factors = alert.get("factors") if isinstance(alert.get("factors"), dict) else {}
    categories = match.get("categories")
    if categories and alert.get("category") not in categories:
        return False
    action = match.get("action")
    if action and alert.get("action_taken") != action:
        return False
    min_recurrence = match.get("min_recurrence_count")
    if min_recurrence is not None and int(alert.get("recurrence_count") or 0) < int(min_recurrence):
        return False
    threshold_checks = (
        ("min_impact_scope", "impact_scope", ">="),
        ("max_source_reliability", "source_reliability", "<="),
        ("max_data_freshness", "data_freshness", "<="),
        ("min_downstream_urgency", "downstream_urgency", ">="),
    )
    for rule_key, factor_key, operator in threshold_checks:
        if rule_key not in match:
            continue
        value = _numeric_or_none(factors.get(factor_key))
        threshold = _numeric_or_none(match.get(rule_key))
        if value is None or threshold is None:
            return False
        if operator == ">=" and value < threshold:
            return False
        if operator == "<=" and value > threshold:
            return False
    return True


def _audit_recommendation_for_alert(alert: dict[str, Any]) -> dict[str, Any] | None:
    payload = _load_json(DATA_DIR / "evolution_fixtures.json", {"variants": []})
    variants = payload.get("variants", []) if isinstance(payload, dict) else []
    for variant in variants:
        if not isinstance(variant, dict) or variant.get("event_type") != "promotion_approved":
            continue
        if _audit_variant_matches(alert, variant):
            return {
                "variant_id": variant.get("variant_id") or variant.get("id"),
                "description": variant.get("description"),
                "action": (variant.get("match") or {}).get("action") if isinstance(variant.get("match"), dict) else None,
            }
    return None


def _audit_complete(metadata: dict[str, Any] | None) -> bool:
    if not metadata:
        return False
    has_decision = bool(metadata.get("action_taken") or metadata.get("actionTaken") or metadata.get("actual_action"))
    has_outcome = (
        "is_correct" in metadata
        or "isCorrect" in metadata
        or metadata.get("outcome") is not None
        or metadata.get("reward") is not None
    )
    return has_decision and has_outcome


def _decision_category(decision: dict[str, Any]) -> str | None:
    category = decision.get("category")
    if _is_missing_category(category):
        return None
    return str(category)


def _accuracy_for_decisions(decisions: list[dict[str, Any]]) -> float | None:
    if not decisions:
        return None
    correct = sum(1 for decision in decisions if decision.get("is_correct") is True)
    return round(correct / len(decisions), 3)


def _trend_for_category(decisions: list[dict[str, Any]]) -> tuple[str, float | None]:
    if len(decisions) < 2:
        return "stable", _accuracy_for_decisions(decisions)
    split = len(decisions) // 2
    first = decisions[:split]
    second = decisions[split:]
    first_accuracy = _accuracy_for_decisions(first) or 0.0
    second_accuracy = _accuracy_for_decisions(second) or 0.0
    if second_accuracy < first_accuracy - 0.10:
        return "declining", second_accuracy
    if second_accuracy > first_accuracy + 0.10:
        return "improving", second_accuracy
    return "stable", second_accuracy


def _alert_level_for_accuracy(accuracy: float | None) -> str:
    if accuracy is None:
        return "warning"
    if accuracy < 0.40:
        return "critical"
    if accuracy < 0.60:
        return "warning"
    return "ok"


def _decision_factors(decision: dict[str, Any]) -> dict[str, float] | None:
    raw_factors = decision.get("factors")
    if not isinstance(raw_factors, dict):
        return None
    factors: dict[str, float] = {}
    for name in FACTOR_NAMES:
        value = _numeric_or_none(raw_factors.get(name))
        if value is not None:
            factors[name] = value
    return factors if factors else None


def _average_factors(decisions: list[dict[str, Any]]) -> dict[str, float]:
    totals = {name: 0.0 for name in FACTOR_NAMES}
    counts = {name: 0 for name in FACTOR_NAMES}
    for decision in decisions:
        factors = _decision_factors(decision)
        if not factors:
            continue
        for name, value in factors.items():
            totals[name] += value
            counts[name] += 1
    return {
        name: round(totals[name] / counts[name], 3) if counts[name] else 0.5
        for name in FACTOR_NAMES
    }


def _top_centroid_shifts(centroid: dict[str, float]) -> list[dict[str, Any]]:
    shifts = [
        {
            "factor": name,
            "from": 0.5,
            "to": round(value, 3),
            "delta": round(value - 0.5, 3),
        }
        for name, value in centroid.items()
    ]
    shifts.sort(key=lambda item: abs(item["delta"]), reverse=True)
    return shifts[:3]


@router.get("/pipelines")
async def pipelines() -> dict[str, Any]:
    return await _graph_client().get_pipelines()


@router.get("/alerts")
async def alerts() -> dict[str, Any]:
    payload = await _graph_client().get_alerts()
    raw_alerts = payload.get("alerts")
    if payload.get("source") == "fixture" and isinstance(raw_alerts, list):
        return {**payload, "alerts": _inject_alert_runtime_fields([alert for alert in raw_alerts if isinstance(alert, dict)])}
    return payload


@router.get("/alert-groups")
def alert_groups() -> dict[str, Any]:
    pipelines_payload = _load_json(DATA_DIR / "fallback" / "pipelines.json", {})
    alerts_payload = _load_json(DATA_DIR / "fallback" / "alerts.json", {})
    raw_pipelines = pipelines_payload.get("pipelines", []) if isinstance(pipelines_payload, dict) else []
    raw_alerts = alerts_payload.get("alerts", []) if isinstance(alerts_payload, dict) else []
    raw_alerts = _inject_alert_runtime_fields([alert for alert in raw_alerts if isinstance(alert, dict)])

    pipelines = {
        str(pipeline.get("name")): pipeline
        for pipeline in raw_pipelines
        if isinstance(pipeline, dict) and pipeline.get("name")
    }
    upstream_map = {
        name: [
            upstream
            for upstream in _normalize_list(pipeline.get("upstream"))
            if upstream in pipelines
        ]
        for name, pipeline in pipelines.items()
    }

    groups: dict[str, dict[str, Any]] = {}
    ungrouped = []
    # Fixture-mode correlation uses fallback upstream topology. Graph-mode FEEDS
    # traversal is deferred because it belongs in graph_queries.py.
    for alert in raw_alerts:
        system_name = alert.get("system_name") or alert.get("system")
        system_key = _normalize_system_key(str(system_name or ""))
        alert_summary = {
            "alert_id": alert.get("alert_id"),
            "system_name": system_key or None,
            "category": alert.get("category"),
            "severity": alert.get("severity"),
            "created_at": alert.get("created_at"),
            "sla_minutes": alert.get("sla_minutes"),
        }
        if not system_key or system_key not in pipelines:
            ungrouped.append(alert_summary)
            continue

        roots = _find_roots(system_key, upstream_map)
        roots = {root for root in roots if root in pipelines}
        if not roots:
            ungrouped.append(alert_summary)
            continue
        root_system = sorted(
            roots,
            key=lambda root: (-_get_criticality(root, pipelines), root),
        )[0]
        group = groups.setdefault(
            root_system,
            {
                "root_system": root_system,
                "root_display": _get_display_name(root_system, pipelines),
                "alerts": [],
                "cascading_systems": set(),
                "alert_count": 0,
            },
        )
        group["alerts"].append(alert_summary)
        group["alert_count"] += 1
        if system_key != root_system:
            group["cascading_systems"].add(system_key)

    result_groups = []
    for group in groups.values():
        result_groups.append(
            {
                **group,
                "cascading_systems": sorted(group["cascading_systems"]),
            }
        )
    result_groups.sort(key=lambda group: (-group["alert_count"], group["root_system"]))

    return {
        "groups": result_groups,
        "ungrouped": ungrouped,
        "total_alerts": len(raw_alerts),
        "total_groups": len(result_groups),
    }


@router.get("/system/{name}/history")
def system_history(name: str, limit: int = 5) -> dict[str, Any]:
    system_key = _normalize_system_key(name)
    real_decisions = []
    for entry in _iter_metadata_decisions():
        entry_system = (
            entry.get("system_name")
            or entry.get("system")
            or entry.get("systemName")
            or _infer_system_from_dataset(str(entry.get("dataset", "")))
        )
        if _normalize_system_key(str(entry_system or "")) != system_key:
            continue
        real_decisions.append(
            {
                "decision_id": entry.get("decision_id"),
                "alert_id": entry.get("alert_id") or entry.get("event_id"),
                "date": entry.get("date") or entry.get("timestamp") or "live",
                "action_taken": entry.get("action_taken") or entry.get("actionTaken"),
                "outcome": entry.get("outcome"),
                "is_correct": entry.get("is_correct"),
                "category": entry.get("category"),
                "resolution_time_minutes": entry.get("resolution_time_minutes"),
                "source": "live_decision",
            }
        )

    seed_decisions = []
    for entry in _load_dataops_seed():
        entry_system = entry.get("system_name") or entry.get("system") or _infer_system_from_dataset(
            str(entry.get("dataset", ""))
        )
        if _normalize_system_key(str(entry_system or "")) != system_key:
            continue
        is_correct = bool(entry.get("is_correct"))
        seed_decisions.append(
            {
                "decision_id": None,
                "alert_id": entry.get("event_id") or entry.get("alert_id"),
                "date": entry.get("date") or entry.get("timestamp") or "historical",
                "action_taken": entry.get("action_taken"),
                "outcome": "correct" if is_correct else "incorrect",
                "is_correct": is_correct,
                "category": entry.get("category"),
                "resolution_time_minutes": None,
                "source": "seed_history",
            }
        )

    all_decisions = real_decisions + seed_decisions
    total = len(all_decisions)
    correct_count = sum(1 for entry in all_decisions if entry.get("is_correct") is True)
    action_breakdown: dict[str, dict[str, Any]] = {}
    for entry in all_decisions:
        action = str(entry.get("action_taken") or "unknown")
        bucket = action_breakdown.setdefault(action, {"count": 0, "correct": 0, "win_rate": None})
        bucket["count"] += 1
        if entry.get("is_correct") is True:
            bucket["correct"] += 1

    for bucket in action_breakdown.values():
        bucket["win_rate"] = round(bucket["correct"] / bucket["count"], 3) if bucket["count"] else None

    ranked_actions = [
        (action, data["win_rate"], data["count"])
        for action, data in action_breakdown.items()
        if data["win_rate"] is not None
    ]
    best_action = None
    worst_action = None
    if ranked_actions:
        best_action = sorted(ranked_actions, key=lambda item: (-item[1], -item[2], item[0]))[0][0]
        worst_action = sorted(ranked_actions, key=lambda item: (item[1], -item[2], item[0]))[0][0]

    safe_limit = max(int(limit), 0)
    return {
        "system": system_key,
        "resolutions": all_decisions[:safe_limit],
        "total": total,
        "accuracy": round(correct_count / total, 3) if total else None,
        "action_breakdown": action_breakdown,
        "best_action": best_action,
        "worst_action": worst_action,
    }


@router.get("/decisions")
def decisions(
    system: str | None = None,
    category: str | None = None,
    action: str | None = None,
    correct: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    correct_filter = _coerce_correct_filter(correct)
    all_decisions = _all_context_decisions()
    filtered = [
        decision
        for decision in all_decisions
        if _matches_decision_filters(decision, system, category, action, correct_filter)
    ]
    safe_limit = max(1, min(int(limit), 100))
    filters_applied = {
        "system": system,
        "category": category,
        "action": action,
        "correct": correct,
    }
    return {
        "decisions": filtered[:safe_limit],
        "total": len(filtered),
        "filters_applied": filters_applied,
        "summary": _decision_summary(filtered),
    }


@router.get("/accuracy-by-category")
def accuracy_by_category() -> dict[str, Any]:
    decisions_by_category: dict[str, list[dict[str, Any]]] = {}
    for decision in _all_context_decisions():
        category = _decision_category(decision)
        if not category:
            continue
        decisions_by_category.setdefault(category, []).append(decision)

    categories: dict[str, dict[str, Any]] = {}
    declining: list[str] = []
    improving: list[str] = []
    for category, category_decisions in decisions_by_category.items():
        total = len(category_decisions)
        correct = sum(1 for decision in category_decisions if decision.get("is_correct") is True)
        accuracy = round(correct / total, 3) if total else None
        trend, recent_accuracy = _trend_for_category(category_decisions)
        alert_level = _alert_level_for_accuracy(accuracy)
        categories[category] = {
            "total": total,
            "correct": correct,
            "accuracy": accuracy,
            "trend": trend,
            "recent_accuracy": recent_accuracy,
            "alert_level": alert_level,
        }
        if trend == "declining":
            declining.append(category)
        if trend == "improving":
            improving.append(category)

    total_decisions = sum(data["total"] for data in categories.values())
    total_correct = sum(data["correct"] for data in categories.values())
    return {
        "categories": categories,
        "overall_accuracy": round(total_correct / total_decisions, 3) if total_decisions else None,
        "categories_declining": declining,
        "categories_improving": improving,
        "total_decisions": total_decisions,
    }


@router.get("/centroid-history")
def centroid_history(category: str | None = None) -> dict[str, Any]:
    normalized_category = str(category).strip() if category else None
    decisions = [
        decision
        for decision in _all_context_decisions()
        if _decision_factors(decision)
        and (not normalized_category or decision.get("category") == normalized_category)
    ]
    current_centroid = _average_factors(decisions)
    total_decisions = len(decisions)
    snapshots = [
        {
            "decision_index": 0,
            "label": "Initial (generic)",
            "centroids_sample": {name: 0.5 for name in FACTOR_NAMES},
            "top_shifts": [],
            "note": "Factory defaults before any decisions",
        },
        {
            "decision_index": total_decisions,
            "label": f"Current ({total_decisions} decisions)",
            "centroids_sample": current_centroid,
            "top_shifts": _top_centroid_shifts(current_centroid),
            "note": "Decision-derived centroid estimate from DataOps history",
        },
    ]
    return {
        "snapshots": snapshots,
        "factor_names": list(FACTOR_NAMES),
        "total_decisions": total_decisions,
    }


@router.get("/system/{name}")
async def system_detail(name: str) -> dict[str, Any]:
    return await _graph_client().get_system(name)


@router.get("/alert/{id}")
async def alert_detail(id: str) -> dict[str, Any]:
    payload = await _graph_client().get_alert(id)
    alert = payload.get("alert")
    if payload.get("source") == "fixture" and isinstance(alert, dict):
        return {**payload, "alert": _with_alert_runtime_fields(alert)}
    return payload


@router.get("/alert/{id}/deps")
async def alert_deps(id: str) -> dict[str, Any]:
    return await _graph_client().get_blast_radius(id)


@router.get("/alert/{id}/recurrence")
async def alert_recurrence(id: str) -> dict[str, Any]:
    return await _graph_client().get_recurrence(id)


@router.get("/alert/{id}/factors")
async def alert_factors(id: str) -> dict[str, Any]:
    return await _graph_client().get_factors(id)


@router.get("/similar")
def similar_alerts(
    category: str,
    impact_scope: float,
    source_reliability: float,
    recurrence_frequency: float,
    downstream_urgency: float,
    data_freshness: float,
    business_criticality: float,
    n: int = 5,
) -> dict[str, Any]:
    seed = _load_dataops_seed()
    if not seed:
        return {"similar": [], "count": 0}

    current_vector = [
        impact_scope,
        source_reliability,
        recurrence_frequency,
        downstream_urgency,
        data_freshness,
        business_criticality,
    ]
    matches = []
    for alert in seed:
        if alert.get("category") != category:
            continue
        factors = alert.get("factors")
        if not isinstance(factors, dict):
            continue
        similarity = _cosine_similarity(current_vector, _vector_from_factors(factors))
        if similarity <= 0.85:
            continue
        matches.append(
            {
                "event_id": alert.get("event_id") or alert.get("alert_id"),
                "dataset": alert.get("dataset"),
                "category": alert.get("category"),
                "action_taken": alert.get("action_taken"),
                "is_correct": alert.get("is_correct"),
                "similarity": round(similarity, 4),
            }
        )

    matches.sort(key=lambda item: item["similarity"], reverse=True)
    limit = max(int(n), 0)
    return {"similar": matches[:limit], "count": len(matches)}


@router.get("/process-signals/{system}")
def process_signals(system: str) -> dict[str, Any]:
    system_key = _normalize_system_key(system)
    signals = _load_json(DATA_DIR / "process_signals.json", {})
    entry = signals.get(system_key) if isinstance(signals, dict) else None
    if not isinstance(entry, dict):
        return {
            "system": system_key,
            "source": "celonis_ems",
            "signals": {},
            "metrics": [],
            "variant": {},
            "correlation": {},
            "narrative": f"No process mining data available for {system_key}.",
            "engine": "celonis_ems.process_mining",
        }
    return {
        "system": system_key,
        "source": entry.get("source") or "celonis_ems",
        "signals": entry.get("signals") or {},
        "metrics": entry.get("metrics") or [],
        "variant": entry.get("variant") or {},
        "correlation": entry.get("correlation") or {},
        "engine": "celonis_ems.process_mining",
    }


@router.get("/audit-trail/{alert_id}")
def audit_trail(alert_id: str) -> dict[str, Any]:
    alerts_by_id = _fallback_alerts_by_id()
    alert = alerts_by_id.get(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    system = alert.get("system") or alert.get("system_name")
    chain: list[dict[str, Any]] = [
        {
            "step": "signal",
            "label": "Alert Detected",
            "detail": f"{alert.get('category') or 'unknown'} on {system or 'unknown system'}",
            "timestamp": alert.get("created_at") or alert.get("timestamp"),
            "source": alert.get("source") or "fixture",
            "data": {
                "alert_id": alert.get("alert_id"),
                "event_id": alert.get("event_id"),
                "dataset": alert.get("dataset"),
                "system": system,
                "category": alert.get("category"),
                "severity": alert.get("severity"),
            },
        }
    ]

    factors = alert.get("factors") if isinstance(alert.get("factors"), dict) else {}
    if factors:
        chain.append(
            {
                "step": "context",
                "label": "Context Gathered",
                "detail": f"{len(factors)} factors auto-computed from fixture graph",
                "source": "fixture",
                "data": factors,
            }
        )

    recommendation = _audit_recommendation_for_alert(alert)
    if recommendation:
        chain.append(
            {
                "step": "enrichment",
                "label": "AE Recommendation",
                "detail": f"{recommendation.get('variant_id')} matched",
                "variant_id": recommendation.get("variant_id"),
                "action": recommendation.get("action"),
                "data": recommendation,
            }
        )
    else:
        chain.append(
            {
                "step": "enrichment",
                "label": "AE Recommendation",
                "detail": "No AE recommendation",
                "data": {},
            }
        )

    metadata = _metadata_for_alert(alert_id)
    if metadata:
        score_action = metadata.get("score_action") or metadata.get("scored_action") or metadata.get("action")
        score_confidence = _numeric_or_none(metadata.get("score_confidence"))
        if score_action or score_confidence is not None:
            chain.append(
                {
                    "step": "score",
                    "label": "Action Scored",
                    "detail": str(score_action or "score recorded"),
                    "data": {
                        "score_action": score_action,
                        "score_confidence": score_confidence,
                    },
                }
            )

        action_taken = metadata.get("action_taken") or metadata.get("actionTaken") or metadata.get("actual_action")
        if action_taken:
            chain.append(
                {
                    "step": "decision",
                    "label": "Decision Captured",
                    "detail": str(action_taken),
                    "data": {
                        "decision_id": metadata.get("decision_id"),
                        "action_taken": action_taken,
                        "followed_ae": metadata.get("followed_ae"),
                    },
                }
            )

        if (
            "is_correct" in metadata
            or "isCorrect" in metadata
            or metadata.get("outcome") is not None
            or metadata.get("reward") is not None
        ):
            chain.append(
                {
                    "step": "outcome",
                    "label": "Outcome Recorded",
                    "detail": str(metadata.get("outcome") or "outcome recorded"),
                    "data": {
                        "is_correct": metadata.get("is_correct") if "is_correct" in metadata else metadata.get("isCorrect"),
                        "outcome": metadata.get("outcome"),
                        "reward": metadata.get("reward"),
                    },
                }
            )

    return {
        "alert_id": alert.get("alert_id") or alert_id,
        "system": system,
        "chain": chain,
        "complete": _audit_complete(metadata),
    }


@router.post("/alert-metadata", status_code=status.HTTP_201_CREATED)
def store_alert_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    decision_id = payload.get("decision_id")
    if not decision_id:
        raise HTTPException(status_code=400, detail="decision_id is required")

    metadata = _load_json(METADATA_PATH, {})
    metadata[str(decision_id)] = dict(payload)
    _write_json(METADATA_PATH, metadata)
    return {"stored": True, "decision_id": decision_id, "metadata": metadata[str(decision_id)]}


@router.get("/alert-metadata")
def alert_metadata() -> dict[str, Any]:
    return {"metadata": _load_json(METADATA_PATH, {})}
