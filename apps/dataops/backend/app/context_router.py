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
        return [entry for entry in metadata.values() if isinstance(entry, dict)]
    if isinstance(metadata, list):
        return [entry for entry in metadata if isinstance(entry, dict)]
    return []


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
