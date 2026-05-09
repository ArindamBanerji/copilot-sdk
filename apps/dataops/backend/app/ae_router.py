"""Operational AgentEvolver endpoints for DataOps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from .graph_queries import DataOpsGraphClient


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
ENGINE_EVOLUTION = {"gae": "gae.evolution"}
ENGINE_CONSERVATION = {"gae": "gae.calibration"}

router = APIRouter()


def _graph_client() -> DataOpsGraphClient:
    return DataOpsGraphClient(fallback_dir=DATA_DIR / "fallback")


def _load_json(name: str, default: Any | None = None) -> Any:
    path = DATA_DIR / name
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text(encoding="utf-8"))


def _factor(alert: dict[str, Any], name: str) -> float:
    factors = alert.get("factors") or {}
    try:
        return float(factors.get(name, 0.0))
    except (TypeError, ValueError):
        return 0.0


def match_ae_rule(alert: dict[str, Any], variant: dict[str, Any]) -> tuple[bool, str]:
    """Return whether a promoted AE variant applies to the alert."""

    match = variant.get("match") or {}
    categories = match.get("categories")
    if categories and alert.get("category") not in categories:
        return False, "category did not match"

    action = match.get("action")
    if action and alert.get("action_taken") != action:
        return False, "action did not match"

    min_recurrence = match.get("min_recurrence_count")
    if min_recurrence is not None and int(alert.get("recurrence_count") or 0) < int(min_recurrence):
        return False, "recurrence count below threshold"

    min_impact = match.get("min_impact_scope")
    if min_impact is not None and _factor(alert, "impact_scope") < float(min_impact):
        return False, "impact scope below threshold"

    max_reliability = match.get("max_source_reliability")
    if max_reliability is not None and _factor(alert, "source_reliability") > float(max_reliability):
        return False, "source reliability above threshold"

    max_freshness = match.get("max_data_freshness")
    if max_freshness is not None and _factor(alert, "data_freshness") > float(max_freshness):
        return False, "data freshness above threshold"

    min_urgency = match.get("min_downstream_urgency")
    if min_urgency is not None and _factor(alert, "downstream_urgency") < float(min_urgency):
        return False, "downstream urgency below threshold"

    return True, variant.get("description") or "AE rule matched this alert"


@router.get("/recommendation/{alert_id}")
async def recommendation(alert_id: str) -> dict[str, Any]:
    alert_payload = await _graph_client().get_alert(alert_id)
    alert = alert_payload.get("alert")
    if not alert:
        return {
            "alert_id": alert_id,
            "has_recommendation": False,
            "recommendations": [],
            "count": 0,
            "source": alert_payload.get("source", "fixture"),
            "engine": ENGINE_EVOLUTION,
        }

    recommendations = []
    for variant in _load_json("evolution_fixtures.json", {"variants": []}).get("variants", []):
        if variant.get("event_type") != "promotion_approved":
            continue
        matched, reason = match_ae_rule(alert, variant)
        if matched:
            recommendations.append(
                {
                    "id": variant.get("id"),
                    "variant_id": variant.get("variant_id"),
                    "artifact_type": variant.get("artifact_type"),
                    "description": variant.get("description"),
                    "impact": variant.get("impact"),
                    "confidence": round(float(variant.get("magnitude") or 0.0), 4),
                    "match_reason": reason,
                }
            )

    return {
        "alert_id": alert_id,
        "has_recommendation": bool(recommendations),
        "recommendations": recommendations,
        "count": len(recommendations),
        "source": alert_payload.get("source", "fixture"),
        "engine": ENGINE_EVOLUTION,
    }


@router.get("/impact")
def impact() -> dict[str, Any]:
    payload = _load_json("ae_impact.json")
    payload.setdefault("engine", ENGINE_EVOLUTION)
    return payload


@router.get("/pattern-origin")
def pattern_origin() -> dict[str, Any]:
    variants = _load_json("evolution_fixtures.json", {"variants": []}).get("variants", [])
    promoted = [variant for variant in variants if variant.get("event_type") == "promotion_approved"]
    rejected = [variant for variant in variants if variant.get("event_type") != "promotion_approved"]
    chain = [
        {
            "copilot": "soc",
            "rule_id": "RULE-CAMPAIGN-ESCALATE",
            "description": "Escalate when 3+ correlated alerts in 24h",
            "contribution": "Discovered that correlated alert bursts need escalation, not individual triage",
        },
        {
            "copilot": "s2p",
            "rule_id": "V-S2P-RECURRING-001",
            "description": "Auto-approve recurring low-risk invoices with consistent patterns",
            "contribution": "Generalized the burst pattern to recurring events across domains",
        },
        {
            "copilot": "dataops",
            "rule_id": "V-DO-RECUR-001",
            "description": "Auto-resolve recurring warehouse timeouts when recurrence > 8",
            "contribution": "Applied recurring-event pattern to pipeline monitoring",
            "warm_start_prior": 0.757,
        },
    ]
    return {
        "engine": ENGINE_EVOLUTION,
        "source": "fixture",
        "narrative": "SOC alert-burst escalation patterns were generalized by S2P and warm-started DataOps recurrence handling.",
        "chain": chain,
        "patterns": [
            {
                "id": variant.get("id"),
                "variant_id": variant.get("variant_id"),
                "source_copilot": variant.get("source_copilot"),
                "source_rule": variant.get("source_rule"),
                "match": variant.get("match") or {},
            }
            for variant in promoted
        ],
        "rejected": [
            {
                "id": variant.get("id"),
                "variant_id": variant.get("variant_id"),
                "reason": (variant.get("metadata") or {}).get("reject_reason"),
            }
            for variant in rejected
        ],
    }


@router.get("/incident")
def incident() -> dict[str, Any]:
    payload = _load_json("incident.json")
    payload.setdefault("engine", ENGINE_EVOLUTION)
    return payload


@router.get("/conservation-history")
def conservation_history() -> dict[str, Any]:
    payload = _load_json("conservation_history.json", {"events": []})
    payload.setdefault("engine", ENGINE_CONSERVATION)
    return payload
