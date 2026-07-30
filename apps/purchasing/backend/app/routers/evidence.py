"""Purchasing evidence endpoints."""

from __future__ import annotations

import math
from typing import Any

from fastapi import APIRouter

from app.factors import compute_factors
from copilot_sdk.scoring.presets import PurchasingPreset


DOMAIN = "purchasing"
_SHAPE = PurchasingPreset().shape
VALID_CATEGORIES = set(_SHAPE.category_names)
VALID_ACTIONS = set(_SHAPE.action_names)
FACTOR_NAMES = tuple(_SHAPE.factor_names)


def create_evidence_router(state_provider: Any) -> APIRouter:
    router = APIRouter(prefix="/api/purchasing", tags=["purchasing-evidence"])

    @router.get("/evidence/summary")
    def evidence_summary() -> dict[str, Any]:
        graph_store = _graph_store(state_provider)
        decisions = _all_decisions(graph_store)
        verified = _verified_decisions(graph_store)
        verified_count = len(verified)
        decision_count = len(decisions)
        correct_count = sum(1 for decision in verified if decision.get("is_correct") is True)
        trajectory = _trajectory(state_provider)

        return _json_safe(
            {
                "domain": DOMAIN,
                "iks_score": _trajectory_iks(trajectory),
                "conservation_status": _conservation_status(verified_count, correct_count),
                "decision_count": decision_count,
                "verified_count": verified_count,
                "verification_rate": _ratio(verified_count, decision_count),
                "top_contributing_factors": _top_factors(verified or decisions),
                "accuracy_trajectory": {
                    "decision_count": decision_count,
                    "verified_count": verified_count,
                    "correct_count": correct_count,
                    "accuracy": _ratio(correct_count, verified_count),
                },
                "source": "graphstore",
            }
        )

    @router.get("/evidence/decisions")
    def evidence_decisions() -> dict[str, Any]:
        graph_store = _graph_store(state_provider)
        verified = [
            decision for decision in _verified_decisions(graph_store)
            if _valid_decision_terms(decision)
        ]
        rows = [_decision_payload(decision) for decision in verified[-25:]]
        return _json_safe(
            {
                "domain": DOMAIN,
                "decisions": rows,
                "count": len(rows),
                "source": "graphstore",
            }
        )

    @router.get("/evidence/audit-trail")
    def audit_trail() -> dict[str, Any]:
        graph_store = _graph_store(state_provider)
        verified = [
            decision for decision in _verified_decisions(graph_store)
            if _valid_decision_terms(decision)
        ]
        chain = [
            {
                "index": index,
                "decision_id": str(decision.get("decision_id") or ""),
                "hash": None,
                "previous_hash": None,
                "timestamp": _timestamp(decision.get("verified_at") or decision.get("created_at")),
                "integrity": "fixture",
            }
            for index, decision in enumerate(verified[-25:])
        ]
        return {
            "domain": DOMAIN,
            "integrity_status": "fixture" if chain else "unavailable",
            "hash_chain_available": False,
            "chain": chain,
            "source": "fixture",
        }

    @router.get("/evidence/conservation-proof")
    def conservation_proof() -> dict[str, Any]:
        graph_store = _graph_store(state_provider)
        verified_count = _count(graph_store, "count_verified")
        correct_count = _count(graph_store, "count_correct")
        q = _ratio(correct_count, verified_count) if verified_count else None
        checkpoints = _centroid_checkpoints(graph_store)
        return _json_safe(
            {
                "domain": DOMAIN,
                "status": _conservation_status(verified_count, correct_count),
                "q": q,
                "theta_min": 0.5,
                "days_in_green": None,
                "trajectory": [
                    {
                        "checkpoint_id": checkpoint.get("id"),
                        "decision_id": checkpoint.get("decision_id"),
                        "category": checkpoint.get("category"),
                        "iks": _finite_float(checkpoint.get("iks")),
                        "created_at": _timestamp(checkpoint.get("created_at")),
                    }
                    for checkpoint in checkpoints
                ],
                "status_transitions": [],
                "source": "computed" if verified_count else "graphstore",
            }
        )

    @router.get("/health")
    def purchasing_health() -> dict[str, Any]:
        summary = evidence_summary()
        return {
            "status": "ok",
            "domain": DOMAIN,
            "conservation": {
                "status": summary["conservation_status"],
                "verified_count": summary["verified_count"],
            },
            "evidence": {
                "decision_count": summary["decision_count"],
                "verification_rate": summary["verification_rate"],
            },
        }

    @router.get("/status")
    def purchasing_status() -> dict[str, Any]:
        summary = evidence_summary()
        proof = conservation_proof()
        return {
            "domain": DOMAIN,
            "status": summary["conservation_status"],
            "evidence": summary,
            "conservation": proof,
            "source": "computed",
        }

    return router


def _graph_store(state_provider: Any):
    graph_store = getattr(state_provider, "graph_store", None)
    if graph_store is not None:
        return graph_store
    if callable(state_provider):
        candidate = state_provider()
        return getattr(candidate, "graph_store", candidate)
    return None


def _all_decisions(graph_store: Any) -> list[dict[str, Any]]:
    get_all = getattr(graph_store, "get_all_decisions", None)
    if not callable(get_all):
        return []
    try:
        return [row for row in get_all(DOMAIN) if isinstance(row, dict)]
    except Exception:
        return []


def _verified_decisions(graph_store: Any) -> list[dict[str, Any]]:
    get_verified = getattr(graph_store, "get_verified_decisions", None)
    if not callable(get_verified):
        return []
    try:
        return [row for row in get_verified(DOMAIN) if isinstance(row, dict)]
    except Exception:
        return []


def _centroid_checkpoints(graph_store: Any) -> list[dict[str, Any]]:
    try:
        return [
            row
            for row in graph_store.get_centroid_checkpoints(DOMAIN, limit=25)
            if isinstance(row, dict)
        ]
    except Exception:
        return []


def _trajectory(state_provider: Any) -> Any | None:
    trajectory = getattr(state_provider, "trajectory", None)
    if not callable(trajectory):
        return None
    try:
        return trajectory()
    except Exception:
        return None


def _trajectory_iks(trajectory: Any | None) -> float | None:
    if trajectory is None:
        return None
    value = trajectory.get("current_iks") if isinstance(trajectory, dict) else getattr(trajectory, "current_iks", None)
    return _finite_float(value)


def _count(graph_store: Any, method_name: str) -> int:
    method = getattr(graph_store, method_name, None)
    if not callable(method):
        return 0
    try:
        return max(int(method(DOMAIN)), 0)
    except Exception:
        return 0


def _conservation_status(verified_count: int, correct_count: int) -> str:
    if verified_count <= 0:
        return "BOOTSTRAP"
    return "GREEN" if _ratio(correct_count, verified_count) >= 0.5 else "AMBER"


def _top_factors(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    totals = {factor: 0.0 for factor in FACTOR_NAMES}
    counts = {factor: 0 for factor in FACTOR_NAMES}
    for decision in decisions:
        factors = _decision_factors(decision)
        for factor in FACTOR_NAMES:
            value = _finite_float(factors.get(factor))
            if value is None:
                continue
            totals[factor] += value
            counts[factor] += 1
    rows = [
        {"factor": factor, "score": round(totals[factor] / counts[factor], 4)}
        for factor in FACTOR_NAMES
        if counts[factor] > 0
    ]
    return sorted(rows, key=lambda row: (-row["score"], row["factor"]))[:5]


def _decision_payload(decision: dict[str, Any]) -> dict[str, Any]:
    action = _recommended_action(decision)
    is_correct = decision.get("is_correct")
    return {
        "decision_id": str(decision.get("decision_id") or ""),
        "category": str(decision.get("category") or ""),
        "action": action,
        "factors": _decision_factors(decision),
        "confidence": _finite_float(decision.get("confidence")),
        "outcome": decision.get("actual_action"),
        "is_correct": bool(is_correct) if is_correct is not None else None,
        "reasoning": _reasoning(decision),
    }


def _valid_decision_terms(decision: dict[str, Any]) -> bool:
    return str(decision.get("category") or "") in VALID_CATEGORIES and _recommended_action(decision) in VALID_ACTIONS


def _recommended_action(decision: dict[str, Any]) -> str:
    return str(decision.get("recommended_action") or decision.get("action") or "")


def _decision_factors(decision: dict[str, Any]) -> dict[str, float]:
    factors = decision.get("factors") if isinstance(decision.get("factors"), dict) else {}
    metadata = factors.get("metadata") if isinstance(factors.get("metadata"), dict) else {}
    decision_metadata = decision.get("metadata") if isinstance(decision.get("metadata"), dict) else {}
    scored = metadata.get("scored_factors") if isinstance(metadata.get("scored_factors"), dict) else {}
    vector = decision.get("factor_vector") if isinstance(decision.get("factor_vector"), list) else []
    result: dict[str, float] = {}
    for index, factor in enumerate(FACTOR_NAMES):
        raw = factors.get(factor)
        if raw is None:
            raw = scored.get(factor)
        if raw is None and index < len(vector):
            raw = vector[index]
        value = _finite_float(raw)
        if value is not None:
            result[factor] = value
    if len(result) < len(FACTOR_NAMES):
        recomputed = compute_factors(_factor_context(decision, decision_metadata, metadata))
        for factor in FACTOR_NAMES:
            if factor not in result and factor in recomputed:
                result[factor] = recomputed[factor]
    return result


def _factor_context(
    decision: dict[str, Any],
    decision_metadata: dict[str, Any],
    factor_metadata: dict[str, Any],
) -> dict[str, Any]:
    context: dict[str, Any] = {}
    for source in (decision, decision_metadata, factor_metadata):
        context.update({key: value for key, value in source.items() if value is not None})

    outcome = context.get("outcome") if isinstance(context.get("outcome"), dict) else {}
    mapped = {
        "forecast_demand": context.get("forecast_demand") or context.get("expected_demand"),
        "par_level": context.get("par_level"),
        "day_of_week": _day_index(context.get("day_of_week")),
        "weather_score": context.get("weather_score") or context.get("weather_forecast"),
        "weather": context.get("weather"),
        "event_flag": context.get("event_flag"),
        "event_covers": context.get("event_covers"),
        "normal_covers": context.get("normal_covers"),
        "waste_pct": context.get("waste_pct") or context.get("historical_waste") or outcome.get("waste_pct"),
        "lead_time_days": context.get("lead_time_days") or context.get("supplier_lead_time"),
        "price_change_count": context.get("price_change_count"),
        "months_tracked": context.get("months_tracked"),
    }
    return {key: value for key, value in mapped.items() if value is not None}


def _day_index(value: Any) -> Any:
    if isinstance(value, str):
        lookup = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }
        return lookup.get(value.strip().lower())
    return value


def _reasoning(decision: dict[str, Any]) -> str:
    category = str(decision.get("category") or "unknown category")
    action = _recommended_action(decision) or "unknown action"
    confidence = _finite_float(decision.get("confidence"))
    if confidence is None:
        return f"Purchasing scorer recommended {action} for {category}."
    return f"Purchasing scorer recommended {action} for {category} with {confidence:.0%} confidence."


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(float(numerator) / float(denominator), 4)


def _finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _timestamp(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    number = _finite_float(value)
    return str(number) if number is not None else None


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "tolist"):
        try:
            return _json_safe(value.tolist())
        except Exception:
            pass
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value
