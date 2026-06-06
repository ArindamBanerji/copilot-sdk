"""Operational AgentEvolver endpoints for DataOps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter

from .graph_queries import DataOpsGraphClient


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
ENGINE_EVOLUTION = {"gae": "gae.evolution"}
ENGINE_CONSERVATION = {"gae": "gae.calibration"}
EvolutionStoreFactory = Callable[[], Any]
S2P_SOURCE_RULES = {"s2p_invoice_quality_scheduling_signal"}


def _graph_client() -> DataOpsGraphClient:
    return DataOpsGraphClient(fallback_dir=DATA_DIR / "fallback")


def reset_ae_fixtures() -> None:
    """Backward-compatible no-op for tests that reset old fixture caches."""

    return None


def _factor(alert: dict[str, Any], name: str) -> float:
    factors = alert.get("factors") or {}
    try:
        return float(factors.get(name, 0.0))
    except (TypeError, ValueError):
        return 0.0


def _events(evolution_store_factory: EvolutionStoreFactory | None, domain: str) -> list[dict[str, Any]]:
    if evolution_store_factory is None:
        return []
    try:
        store = evolution_store_factory()
        events = store.get_evolution_events(domain=domain, limit=500)
    except Exception:
        return []
    return [event for event in events if isinstance(event, dict)]


def _event_to_variant(event: dict[str, Any]) -> dict[str, Any]:
    metadata = event.get("metadata") if isinstance(event.get("metadata"), dict) else {}
    variant = dict(metadata)
    event_type = str(variant.get("event_type") or event.get("event_type") or "")
    rule_name = str(event.get("rule_name") or variant.get("rule_name") or "")
    variant_id = str(event.get("variant_id") or variant.get("variant_id") or variant.get("variantId") or rule_name)
    variant.setdefault("id", variant.get("id") or variant_id or rule_name)
    variant.setdefault("variant_id", variant_id)
    variant.setdefault("rule_name", rule_name)
    variant.setdefault("name", variant.get("description") or rule_name or variant_id)
    variant.setdefault("description", rule_name or variant_id)
    variant["event_type"] = event_type
    variant.setdefault("timestamp", event.get("timestamp"))
    variant["metadata"] = metadata
    return variant


def _variants(evolution_store_factory: EvolutionStoreFactory | None, domain: str) -> list[dict[str, Any]]:
    return [_event_to_variant(event) for event in _events(evolution_store_factory, domain)]


def _load_json(filename: str, default: Any) -> Any:
    path = DATA_DIR / filename
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _variant_id(variant: dict[str, Any]) -> str:
    return str(variant.get("variant_id") or variant.get("variantId") or variant.get("id") or "")


def _normalize_variant_status(variant: dict[str, Any]) -> str:
    event_type = str(variant.get("event_type") or variant.get("eventType") or "").lower()
    status = str(variant.get("status") or "").lower()
    artifact_type = str(variant.get("artifact_type") or variant.get("artifactType") or "").lower()
    if status in {"promoted", "approved"} or event_type in {"promotion_approved", "promoted"}:
        return "promoted"
    if status in {"rejected", "promotion_rejected"} or event_type in {"promotion_rejected", "rejected"}:
        return "rejected"
    if status in {"shadow", "shadow_testing"} or event_type.startswith("shadow") or "shadow" in artifact_type:
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


def _source_rule(variant: dict[str, Any]) -> str | None:
    value = variant.get("source_rule") or variant.get("sourceRule")
    return str(value) if value else None


def _canonical_copilot(value: str) -> str:
    normalized = value.strip().lower().replace("-", "_")
    if normalized == "s2p":
        return "S2P"
    if normalized == "soc":
        return "SOC"
    if normalized == "dataops":
        return "dataops"
    return value


def _explicit_source_copilot(variant: dict[str, Any]) -> str | None:
    metadata = variant.get("metadata") if isinstance(variant.get("metadata"), dict) else {}
    for key in ("source_copilot", "sourceCopilot", "source_domain", "sourceDomain", "source"):
        value = variant.get(key)
        if value is None:
            value = metadata.get(key)
        if value:
            return _canonical_copilot(str(value))
    return None


def _is_known_s2p_source_rule(source_rule: str | None) -> bool:
    return bool(source_rule and source_rule.strip().lower() in S2P_SOURCE_RULES)


def _source_copilot(variant: dict[str, Any], domain: str = "dataops") -> str | None:
    source_rule = _source_rule(variant)
    if _is_known_s2p_source_rule(source_rule):
        return "S2P"
    return _explicit_source_copilot(variant)


def _variant_date(variant: dict[str, Any], keys: tuple[str, ...], fallback: str) -> str:
    for key in keys:
        value = variant.get(key)
        if value:
            return str(value)
    return fallback


def _rule_identifier(variant: dict[str, Any]) -> str:
    return str(variant.get("id") or _variant_id(variant) or variant.get("rule_name") or "")


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
        "source_copilot": _source_copilot(variant),
        "source_rule": _source_rule(variant),
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


def _pattern_genealogy(promoted: list[dict[str, Any]]) -> dict[str, Any]:
    if not promoted:
        return {"stages": [], "improvement": None}
    dataops_variant = promoted[0]
    dataops_win_rate = _variant_win_rate(dataops_variant) or 0.0
    dataops_decisions = _variant_evaluations(dataops_variant)
    stages = []
    lineage = dataops_variant.get("lineage")
    if isinstance(lineage, list):
        for item in lineage:
            if isinstance(item, dict):
                stages.append(dict(item))
    if not stages:
        source_copilot = _source_copilot(dataops_variant)
        source_rule = _source_rule(dataops_variant)
        if source_copilot or source_rule:
            stages.append(
                {
                    "copilot": source_copilot or "unknown",
                    "rule_id": source_rule,
                    "win_rate": dataops_variant.get("source_win_rate"),
                    "decisions": dataops_variant.get("source_decisions"),
                }
            )
    stages.append(
        {
            "copilot": "dataops",
            "win_rate": round(dataops_win_rate, 3),
            "decisions": dataops_decisions,
            "warm_start": dataops_variant.get("warm_start_prior") or dataops_variant.get("warmStartPrior"),
        }
    )
    return {
        "stages": stages,
        "improvement": dataops_variant.get("improvement"),
    }


def _impact_payload(variants: list[dict[str, Any]]) -> dict[str, Any]:
    promoted = [variant for variant in variants if _normalize_variant_status(variant) == "promoted"]
    rejected = [variant for variant in variants if _normalize_variant_status(variant) == "rejected"]
    evaluations = sum(_variant_evaluations(variant) for variant in promoted)
    wins = sum(int(_variant_number(variant, ("wins",)) or 0) for variant in promoted)
    accuracy = round(wins / evaluations, 3) if evaluations else 0.0
    breakdown: dict[str, dict[str, float | int]] = {}
    for variant in promoted:
        impact_key = str(variant.get("impact") or "evolution_event")
        prevented = int(_variant_number(variant, ("wins", "alerts_prevented")) or 0)
        hours = _variant_number(variant, ("estimated_hours_saved", "hours_saved")) or 0.0
        bucket = breakdown.setdefault(impact_key, {"alerts_prevented": 0, "estimated_hours_saved": 0.0})
        bucket["alerts_prevented"] = int(bucket["alerts_prevented"]) + prevented
        bucket["estimated_hours_saved"] = round(float(bucket["estimated_hours_saved"]) + hours, 3)
    rejected_example = None
    if rejected:
        rejected_example = {
            "variant_id": _rule_identifier(rejected[0]),
            "reason": _variant_rejected_reason(rejected[0]),
        }
    return {
        "auto_resolved_count": wins,
        "accuracy": accuracy,
        "active_rules": [_rule_identifier(variant) for variant in promoted],
        "rejected_rules": [_rule_identifier(variant) for variant in rejected],
        "breakdown": breakdown,
        "rejected_example": rejected_example,
        "engine": ENGINE_EVOLUTION,
    }


def create_ae_router(
    evolution_store_factory: EvolutionStoreFactory | None = None,
    domain: str = "dataops",
) -> APIRouter:
    router = APIRouter()

    def store_variants() -> list[dict[str, Any]]:
        return _variants(evolution_store_factory, domain)

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
                "source": "evolution_store",
                "engine": ENGINE_EVOLUTION,
            }

        recommendations = []
        for variant in store_variants():
            if _normalize_variant_status(variant) != "promoted":
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
            "source": "evolution_store",
            "engine": ENGINE_EVOLUTION,
        }

    @router.get("/impact")
    def impact() -> dict[str, Any]:
        return _impact_payload(store_variants())

    @router.get("/pattern-origin")
    def pattern_origin() -> dict[str, Any]:
        variants = store_variants()
        promoted = [variant for variant in variants if _normalize_variant_status(variant) == "promoted"]
        rejected = [variant for variant in variants if _normalize_variant_status(variant) == "rejected"]
        source_backed = [
            variant for variant in variants
            if _source_copilot(variant, domain) or _source_rule(variant)
        ]
        origin_variants = promoted or source_backed
        chain = []
        for variant in origin_variants:
            chain.append(
                {
                    "copilot": _source_copilot(variant, domain) or domain,
                    "rule_id": _source_rule(variant) or _rule_identifier(variant),
                    "description": variant.get("description"),
                    "contribution": variant.get("contribution"),
                    "warm_start_prior": variant.get("warm_start_prior") or variant.get("warmStartPrior"),
                }
            )
        narrative = (
            f"{len(origin_variants)} evolution pattern origin(s) available from persisted {domain} events."
            if origin_variants else
            "No evolution data yet."
        )
        return {
            "engine": ENGINE_EVOLUTION,
            "source": "evolution_store",
            "narrative": narrative,
            "chain": chain,
            "genealogy": _pattern_genealogy(origin_variants),
            "patterns": [
                {
                    "id": variant.get("id"),
                    "variant_id": variant.get("variant_id"),
                    "source_copilot": _source_copilot(variant, domain),
                    "source_rule": _source_rule(variant),
                    "match": variant.get("match") or {},
                }
                for variant in origin_variants
            ],
            "rejected": [
                {
                    "id": variant.get("id"),
                    "variant_id": variant.get("variant_id"),
                    "reason": _variant_rejected_reason(variant),
                }
                for variant in rejected
            ],
        }

    @router.get("/rule-lifecycle")
    def rule_lifecycle(variant_id: str | None = None, status: str | None = None) -> dict[str, Any]:
        normalized_status = status.strip().lower() if status else None
        rules = [_normalize_rule_lifecycle(variant) for variant in store_variants()]
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
            "source": "evolution_store",
            "rules": rules,
            "total": len(rules),
            "summary": summary,
            "engine": ENGINE_EVOLUTION,
        }

    @router.get("/operational-rules")
    def operational_rules() -> dict[str, Any]:
        rules = [
            {
                "id": _rule_identifier(variant),
                "name": variant.get("name") or variant.get("description") or _rule_identifier(variant),
                "type": variant.get("artifact_type") or variant.get("artifactType"),
                "status": _normalize_variant_status(variant),
                "system": variant.get("system"),
                "trigger": variant.get("trigger"),
                "recommendation": variant.get("recommendation") or variant.get("description"),
                "expected_impact": variant.get("expected_impact") or variant.get("impact"),
            }
            for variant in store_variants()
        ]
        summary = {"proposed": 0, "shadow": 0, "promoted": 0, "rejected": 0}
        for rule in rules:
            status = str(rule.get("status") or "proposed")
            if status in summary:
                summary[status] += 1
        return {
            "source": "evolution_store",
            "rules": rules,
            "summary": summary,
            "total": len(rules),
            "engine": ENGINE_EVOLUTION,
        }

    @router.get("/incident")
    def incident() -> dict[str, Any]:
        return {
            "incident_id": None,
            "title": None,
            "estimated_cost": 0,
            "primary_alert_id": None,
            "affected_systems": [],
            "affected_datasets": [],
            "fingerprint_insight": {},
            "engine": ENGINE_EVOLUTION,
        }

    @router.get("/conservation-history")
    def conservation_history() -> dict[str, Any]:
        return {"events": [], "engine": ENGINE_CONSERVATION}

    @router.get("/transfer-status")
    def transfer_status() -> dict[str, Any]:
        """Act 5: Pattern transfer status across systems."""

        payload = _load_json("transfer_status.json", None)
        if isinstance(payload, dict) and isinstance(payload.get("transfers"), list):
            return payload
        return {
            "transfers": [],
            "summary": {
                "total_transfers": 0,
                "active": 0,
                "monitoring": 0,
                "pending": 0,
                "cumulative_savings": 0,
            },
        }

    return router


router = create_ae_router()
