"""Self-computation endpoints backed directly by GraphStore."""

from __future__ import annotations

import math
from typing import Any

from fastapi import APIRouter, Query

from copilot_sdk.graph import GraphStore


def create_self_computation_router(graph_store: GraphStore) -> APIRouter:
    """Create GraphStore-backed self-computation endpoints for one app instance."""
    router = APIRouter(prefix="/api/self", tags=["self-computation"])

    def _gs() -> GraphStore:
        return graph_store

    def _domain() -> str:
        return str(getattr(graph_store, "domain", "") or "")

    @router.get("/centroid-history")
    def centroid_history(
        limit: int = Query(50, ge=1, le=500),
        checkpoint_time_start: str | None = None,
        checkpoint_time_end: str | None = None,
        decision_time_start: str | None = None,
        decision_time_end: str | None = None,
        category: str | None = None,
    ) -> dict[str, Any]:
        filters = {
            "checkpoint_time_start": checkpoint_time_start,
            "checkpoint_time_end": checkpoint_time_end,
            "decision_time_start": decision_time_start,
            "decision_time_end": decision_time_end,
            "category": category,
        }
        active_filters = {key: value for key, value in filters.items() if value is not None}
        checkpoints = _gs().get_centroid_checkpoints(_domain(), limit=limit, **active_filters)
        normalized = [_json_safe(checkpoint) for checkpoint in checkpoints]
        return {"checkpoints": normalized, "total": len(normalized)}

    @router.get("/accuracy-by-category")
    def accuracy_by_category(
        threshold: float = Query(0.70, ge=0.0, le=1.0),
    ) -> dict[str, Any]:
        verified = _gs().get_verified_decisions(_domain())
        grouped: dict[str, dict[str, int]] = {}
        for decision in verified:
            category = str(decision.get("category") or "uncategorized")
            bucket = grouped.setdefault(category, {"total": 0, "correct": 0})
            bucket["total"] += 1
            if decision.get("is_correct") is True:
                bucket["correct"] += 1

        categories = []
        for category in sorted(grouped):
            total = grouped[category]["total"]
            correct = grouped[category]["correct"]
            accuracy = round(correct / total, 4) if total else 0.0
            categories.append(
                {
                    "category": category,
                    "accuracy": accuracy,
                    "total": total,
                    "correct": correct,
                    "alert": accuracy < threshold,
                }
            )

        return {
            "categories": categories,
            "threshold": threshold,
            "overall_verified": len(verified),
        }

    @router.get("/decisions")
    def decisions(
        category: str | None = None,
        action: str | None = None,
        limit: int = Query(50, ge=1, le=500),
        verified_only: bool = False,
    ) -> dict[str, Any]:
        store = _gs()
        source = (
            store.get_verified_decisions(_domain())
            if verified_only
            else _merge_verified_fields(
                store.get_all_decisions(_domain()),
                store.get_verified_decisions(_domain()),
            )
        )
        filtered = [
            decision
            for decision in source
            if _matches_decision(decision, category=category, action=action)
        ]
        return {"decisions": filtered[:limit], "total": len(filtered)}

    @router.get("/audit-trail")
    def audit_trail(
        decision_id: str | None = None,
        limit: int = Query(20, ge=1, le=100),
    ) -> dict[str, Any]:
        store = _gs()
        if decision_id:
            decision = store.get_decision(decision_id)
            if decision is None:
                return {"error": f"Decision {decision_id} not found"}
            outcome = next(
                (
                    verified
                    for verified in store.get_verified_decisions(_domain())
                    if verified.get("decision_id") == decision_id
                ),
                None,
            )
            return {
                "decision": decision,
                "outcome": outcome,
                "chain_complete": outcome is not None,
            }

        verified = store.get_verified_decisions(_domain())[:limit]
        return {"trails": verified, "total": len(verified)}

    @router.get("/decision-flow")
    def decision_flow(limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
        store = _gs()
        domain = _domain()
        all_decisions = _get_all_decisions(store, domain)
        verified = _get_verified_decisions(store, domain)
        merged = _merge_verified_fields(all_decisions, verified)
        ordered = sorted(merged, key=_decision_sort_key, reverse=True)
        recent = ordered[:limit]
        checkpoints = _get_centroid_checkpoints(store, domain, limit=20)

        verified_count = _count_verified(store, domain, verified)
        correct_count = _count_correct(store, domain, verified)
        total_count = len(all_decisions)
        checkpoint_ids = {
            str(checkpoint.get("decision_id"))
            for checkpoint in checkpoints
            if checkpoint.get("decision_id") is not None
        }

        return _json_safe(
            {
                "domain": domain,
                "total_decisions": total_count,
                "verified_decisions": verified_count,
                "accuracy": _ratio(correct_count, verified_count),
                "by_category": _category_flow_stats(all_decisions, verified),
                "recent_decisions": [_normalize_decision(decision) for decision in recent],
                "centroid_evolution": [
                    _normalize_checkpoint(checkpoint)
                    for checkpoint in checkpoints[-20:]
                ],
                "decision_chain": _decision_chain(recent, checkpoint_ids),
                "flow_statistics": _flow_statistics(all_decisions, verified),
            }
        )

    return router


def mount_self_computation_router(app: Any, graph_store: GraphStore) -> None:
    """Mount GraphStore-backed self-computation endpoints on a FastAPI app."""
    app.include_router(create_self_computation_router(graph_store))


def _matches_decision(
    decision: dict[str, Any],
    *,
    category: str | None,
    action: str | None,
) -> bool:
    if category is not None and decision.get("category") != category:
        return False
    if action is None:
        return True
    return action in {
        decision.get("recommended_action"),
        decision.get("actual_action"),
        decision.get("action"),
    }


def _merge_verified_fields(
    decisions: list[dict[str, Any]],
    verified: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    verified_by_id = {
        item.get("decision_id"): item
        for item in verified
        if item.get("decision_id")
    }
    merged = []
    for decision in decisions:
        decision_id = decision.get("decision_id")
        verified_decision = verified_by_id.get(decision_id)
        if verified_decision is None:
            merged.append(decision)
        else:
            merged.append({**decision, **verified_decision})
    return merged


def _get_all_decisions(store: GraphStore, domain: str) -> list[dict[str, Any]]:
    get_all = getattr(store, "get_all_decisions", None)
    if callable(get_all):
        return list(get_all(domain))
    get_verified = getattr(store, "get_verified_decisions", None)
    return list(get_verified(domain)) if callable(get_verified) else []


def _get_verified_decisions(store: GraphStore, domain: str) -> list[dict[str, Any]]:
    get_verified = getattr(store, "get_verified_decisions", None)
    return list(get_verified(domain)) if callable(get_verified) else []


def _count_verified(
    store: GraphStore,
    domain: str,
    verified: list[dict[str, Any]],
) -> int:
    count_verified = getattr(store, "count_verified", None)
    if callable(count_verified):
        return int(count_verified(domain))
    return len(verified)


def _count_correct(
    store: GraphStore,
    domain: str,
    verified: list[dict[str, Any]],
) -> int:
    count_correct = getattr(store, "count_correct", None)
    if callable(count_correct):
        return int(count_correct(domain))
    return sum(1 for decision in verified if decision.get("is_correct") is True)


def _get_centroid_checkpoints(
    store: GraphStore,
    domain: str,
    *,
    limit: int,
) -> list[dict[str, Any]]:
    get_checkpoints = getattr(store, "get_centroid_checkpoints", None)
    if not callable(get_checkpoints):
        return []
    return list(get_checkpoints(domain, limit=limit))


def _category_flow_stats(
    decisions: list[dict[str, Any]],
    verified: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, int]] = {}
    for decision in decisions:
        category = str(decision.get("category") or "uncategorized")
        grouped.setdefault(
            category,
            {"total_decisions": 0, "verified_decisions": 0, "correct_decisions": 0},
        )["total_decisions"] += 1

    for decision in verified:
        category = str(decision.get("category") or "uncategorized")
        bucket = grouped.setdefault(
            category,
            {"total_decisions": 0, "verified_decisions": 0, "correct_decisions": 0},
        )
        bucket["verified_decisions"] += 1
        if decision.get("is_correct") is True:
            bucket["correct_decisions"] += 1

    return {
        category: {
            **bucket,
            "accuracy": _ratio(bucket["correct_decisions"], bucket["verified_decisions"]),
        }
        for category, bucket in sorted(grouped.items())
    }


def _normalize_decision(decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision_id": _string_or_none(decision.get("decision_id")),
        "entity_id": _string_or_none(decision.get("entity_id")),
        "category": decision.get("category"),
        "action": decision.get("recommended_action") or decision.get("action"),
        "confidence": _safe_float(decision.get("confidence")),
        "factors": decision.get("factors"),
        "outcome": decision.get("actual_action"),
        "is_correct": _bool_or_none(decision.get("is_correct")),
        "timestamp": _timestamp(decision),
    }


def _normalize_checkpoint(checkpoint: dict[str, Any]) -> dict[str, Any]:
    metadata = checkpoint.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    return {
        "timestamp": (
            checkpoint.get("checkpoint_time")
            or checkpoint.get("created_at")
            or checkpoint.get("timestamp")
        ),
        "iks": _safe_float(checkpoint.get("iks")) if "iks" in checkpoint else None,
        "category": checkpoint.get("category"),
        "action": metadata.get("action") or metadata.get("recommended_action"),
        "metadata": metadata,
    }


def _decision_chain(
    decisions: list[dict[str, Any]],
    checkpoint_ids: set[str],
) -> list[dict[str, Any]]:
    chain = []
    for index, decision in enumerate(decisions):
        decision_id = _string_or_none(decision.get("decision_id")) or ""
        next_decision = decisions[index + 1] if index + 1 < len(decisions) else None
        chain.append(
            {
                "decision_id": decision_id,
                "outcome": decision.get("actual_action"),
                "centroid_update": (
                    decision_id in checkpoint_ids
                    or decision.get("is_correct") is not None
                ),
                "next": (
                    _string_or_none(next_decision.get("decision_id"))
                    if next_decision is not None
                    else None
                ),
            }
        )
    return chain


def _flow_statistics(
    decisions: list[dict[str, Any]],
    verified: list[dict[str, Any]],
) -> dict[str, Any]:
    total = len(decisions)
    verified_count = len(verified)
    rewards = [_reward_value(decision) for decision in verified]
    rewards = [reward for reward in rewards if reward is not None]
    return {
        "avg_confidence": _safe_mean(
            _safe_float(decision.get("confidence"))
            for decision in decisions
        ),
        "confirmation_rate": _ratio(verified_count, total),
        "override_rate": _override_rate(verified),
        "mean_reward": _safe_mean(rewards) if rewards else None,
    }


def _override_rate(verified: list[dict[str, Any]]) -> float:
    if not verified:
        return 0.0
    overrides = sum(
        1
        for decision in verified
        if decision.get("actual_action") not in (None, decision.get("recommended_action"), decision.get("action"))
    )
    return _ratio(overrides, len(verified))


def _reward_value(decision: dict[str, Any]) -> float | None:
    for source in (
        decision,
        decision.get("context") if isinstance(decision.get("context"), dict) else {},
        decision.get("outcome_metadata") if isinstance(decision.get("outcome_metadata"), dict) else {},
        decision.get("metadata") if isinstance(decision.get("metadata"), dict) else {},
    ):
        if not isinstance(source, dict):
            continue
        for key in ("reward", "signed_reward", "score_reward"):
            if key in source:
                return _safe_float(source.get(key))
    return None


def _decision_sort_key(decision: dict[str, Any]) -> tuple[float, str]:
    timestamp = _safe_float(
        decision.get("created_at")
        if decision.get("created_at") is not None
        else decision.get("verified_at")
    )
    return (timestamp or 0.0, str(decision.get("decision_id") or ""))


def _timestamp(decision: dict[str, Any]) -> str | int | float | None:
    return (
        decision.get("created_at")
        if decision.get("created_at") is not None
        else decision.get("verified_at")
    )


def _safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _safe_mean(values: Any) -> float:
    numbers = [number for value in values if (number := _safe_float(value)) is not None]
    return round(sum(numbers) / len(numbers), 6) if numbers else 0.0


def _ratio(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 0.0
    return round(float(numerator) / float(denominator), 6)


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _bool_or_none(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if value is None or isinstance(value, (str, int, bool)):
        return value

    if not isinstance(value, (str, bytes)):
        tolist = getattr(value, "tolist", None)
        if callable(tolist):
            try:
                converted = tolist()
            except Exception:
                converted = None
            else:
                if converted is not value:
                    return _json_safe(converted)

        item = getattr(value, "item", None)
        if callable(item):
            try:
                return _json_safe(item())
            except Exception:
                pass

    return str(value)
