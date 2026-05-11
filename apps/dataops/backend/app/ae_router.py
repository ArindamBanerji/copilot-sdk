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


def _variants() -> list[dict[str, Any]]:
    payload = _load_json("evolution_fixtures.json", {"variants": []})
    if isinstance(payload, list):
        variants = payload
    elif isinstance(payload, dict):
        variants = payload.get("variants", [])
    else:
        variants = []
    return [variant for variant in variants if isinstance(variant, dict)]


def _variant_id(variant: dict[str, Any]) -> str:
    return str(variant.get("variant_id") or variant.get("variantId") or variant.get("id") or "")


def _normalize_variant_status(variant: dict[str, Any]) -> str:
    event_type = str(variant.get("event_type") or variant.get("eventType") or "").lower()
    status = str(variant.get("status") or "").lower()
    artifact_type = str(variant.get("artifact_type") or variant.get("artifactType") or "").lower()
    if status in {"promoted", "approved"} or event_type == "promotion_approved":
        return "promoted"
    if status in {"rejected", "promotion_rejected"} or event_type == "promotion_rejected":
        return "rejected"
    if status in {"shadow", "shadow_testing"} or "shadow" in artifact_type:
        return "shadow"
    return "proposed"


def _variant_number(variant: dict[str, Any], keys: tuple[str, ...]) -> float | None:
    metadata = variant.get("metadata") if isinstance(variant.get("metadata"), dict) else {}
    for key in keys:
        value = variant.get(key)
        if value is None:
            value = metadata.get(key)
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if number == number and number not in {float("inf"), float("-inf")}:
            return number
    return None


def _variant_win_rate(variant: dict[str, Any]) -> float | None:
    explicit = _variant_number(variant, ("win_rate", "shadow_win_rate", "shadowWinRate"))
    if explicit is not None:
        return explicit / 100 if explicit > 1 and explicit <= 100 else explicit
    wins = _variant_number(variant, ("wins",))
    total = _variant_number(variant, ("total", "decisions_evaluated", "shadow_count", "shadowCount", "count"))
    if wins is not None and total and total > 0:
        return wins / total
    return None


def _variant_evaluations(variant: dict[str, Any]) -> int:
    total = _variant_number(variant, ("decisions_evaluated", "shadow_count", "shadowCount", "count", "total"))
    return max(int(total or 0), 0)


def _variant_rejected_reason(variant: dict[str, Any]) -> str | None:
    metadata = variant.get("metadata") if isinstance(variant.get("metadata"), dict) else {}
    reason = (
        variant.get("rejected_reason")
        or variant.get("rejectReason")
        or metadata.get("reject_reason")
        or metadata.get("reason")
    )
    return str(reason) if reason else None


def _variant_date(variant: dict[str, Any], keys: tuple[str, ...], fallback: str) -> str:
    for key in keys:
        value = variant.get(key)
        if value:
            return str(value)
    return fallback


def _generate_lifecycle_events(variant: dict[str, Any], status: str, win_rate: float | None, evaluations: int) -> list[dict[str, Any]]:
    events = [
        {
            "type": "proposed",
            "date": _variant_date(variant, ("proposed_at", "proposedAt"), "2026-04-01"),
            "detail": "Pattern detected from accumulated decisions",
        }
    ]
    if evaluations > 0:
        events.append(
            {
                "type": "shadow_start",
                "date": _variant_date(variant, ("shadow_started", "shadowStarted"), "2026-04-05"),
                "detail": "Shadow-testing against live decisions",
            }
        )
        events.append(
            {
                "type": "shadow_result",
                "date": _variant_date(variant, ("shadow_ended", "shadowEnded"), "2026-04-19"),
                "detail": f"{evaluations} decisions, {int((win_rate or 0.0) * 100)}% win rate",
            }
        )
    if status == "promoted":
        events.append(
            {
                "type": "promoted",
                "date": _variant_date(variant, ("promoted_at", "promotedAt", "timestamp"), "2026-04-20"),
                "detail": "Win rate >= 60%, conservation GREEN",
            }
        )
    elif status == "rejected":
        reason = _variant_rejected_reason(variant) or f"Win rate {int((win_rate or 0.0) * 100)}% below threshold"
        events.append(
            {
                "type": "rejected",
                "date": _variant_date(variant, ("rejected_at", "rejectedAt", "timestamp"), "2026-04-25"),
                "detail": reason,
            }
        )
    elif status == "shadow":
        events.append(
            {
                "type": "shadow_running",
                "date": _variant_date(variant, ("timestamp",), "2026-04-19"),
                "detail": "Rule is still under shadow evaluation",
            }
        )
    return events


def _normalize_rule_lifecycle(variant: dict[str, Any]) -> dict[str, Any]:
    status = _normalize_variant_status(variant)
    win_rate = _variant_win_rate(variant)
    evaluations = _variant_evaluations(variant)
    metadata = variant.get("metadata") if isinstance(variant.get("metadata"), dict) else {}
    rule = {
        "id": variant.get("id"),
        "variant_id": _variant_id(variant),
        "name": variant.get("name") or variant.get("description") or _variant_id(variant),
        "description": variant.get("description"),
        "artifact_type": variant.get("artifact_type") or variant.get("artifactType"),
        "status": status,
        "event_type": variant.get("event_type") or variant.get("eventType"),
        "impact": variant.get("impact"),
        "magnitude": variant.get("magnitude"),
        "win_rate": round(win_rate, 3) if win_rate is not None else None,
        "decisions_evaluated": evaluations,
        "rejected_reason": _variant_rejected_reason(variant),
        "source_copilot": variant.get("source_copilot") or variant.get("sourceCopilot"),
        "source_rule": variant.get("source_rule") or variant.get("sourceRule"),
        "warm_start_prior": variant.get("warm_start_prior") or variant.get("warmStartPrior"),
        "timestamp": variant.get("timestamp"),
        "match": variant.get("match") or {},
        "metadata": metadata,
    }
    rule["lifecycle_events"] = _generate_lifecycle_events(variant, status, win_rate, evaluations)
    return rule


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


def _pattern_genealogy(promoted: list[dict[str, Any]]) -> dict[str, Any]:
    dataops_variant = next(
        (variant for variant in promoted if _variant_id(variant) == "dataops-recurring-impact-v1"),
        promoted[0] if promoted else {},
    )
    dataops_win_rate = _variant_win_rate(dataops_variant) if dataops_variant else None
    dataops_decisions = _variant_evaluations(dataops_variant) if dataops_variant else 0
    dataops_win_rate = dataops_win_rate if dataops_win_rate is not None else 0.83
    dataops_decisions = dataops_decisions or 24
    soc_win_rate = 0.68
    improvement_pp = round((dataops_win_rate - soc_win_rate) * 100)
    return {
        "stages": [
            {"copilot": "soc", "win_rate": soc_win_rate, "decisions": 150},
            {"copilot": "s2p", "win_rate": 0.69, "decisions": 80, "warm_start": soc_win_rate},
            {
                "copilot": "dataops",
                "win_rate": round(dataops_win_rate, 3),
                "decisions": dataops_decisions,
                "warm_start": 0.757,
            },
        ],
        "improvement": f"+{improvement_pp}pp across 3 domains",
    }


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
        "genealogy": _pattern_genealogy(promoted),
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


@router.get("/rule-lifecycle")
def rule_lifecycle(variant_id: str | None = None, status: str | None = None) -> dict[str, Any]:
    normalized_status = status.strip().lower() if status else None
    rules = [_normalize_rule_lifecycle(variant) for variant in _variants()]
    if variant_id:
        rules = [
            rule for rule in rules
            if rule.get("variant_id") == variant_id or rule.get("id") == variant_id
        ]
    if normalized_status:
        rules = [rule for rule in rules if rule.get("status") == normalized_status]
    summary = {"promoted": 0, "rejected": 0, "shadow": 0, "proposed": 0}
    for rule in rules:
        rule_status = str(rule.get("status") or "proposed")
        if rule_status in summary:
            summary[rule_status] += 1
    return {
        "source": "fixture",
        "rules": rules,
        "total": len(rules),
        "summary": summary,
        "engine": ENGINE_EVOLUTION,
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
