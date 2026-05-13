"""Self-computation endpoints backed directly by GraphStore."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from copilot_sdk.graph import GraphStore


def create_self_computation_router(graph_store: GraphStore) -> APIRouter:
    """Create GraphStore-backed self-computation endpoints for one app instance."""
    router = APIRouter(prefix="/api/self", tags=["self-computation"])

    def _gs() -> GraphStore:
        return graph_store

    @router.get("/centroid-history")
    def centroid_history(limit: int = Query(50, ge=1, le=500)) -> dict[str, Any]:
        checkpoints = _gs().get_centroid_checkpoints(limit=limit)
        normalized = [_json_safe(checkpoint) for checkpoint in checkpoints]
        return {"checkpoints": normalized, "total": len(normalized)}

    @router.get("/accuracy-by-category")
    def accuracy_by_category(
        threshold: float = Query(0.70, ge=0.0, le=1.0),
    ) -> dict[str, Any]:
        verified = _gs().get_verified_decisions()
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
            store.get_verified_decisions()
            if verified_only
            else _merge_verified_fields(
                store.get_all_decisions(),
                store.get_verified_decisions(),
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
                    for verified in store.get_verified_decisions()
                    if verified.get("decision_id") == decision_id
                ),
                None,
            )
            return {
                "decision": decision,
                "outcome": outcome,
                "chain_complete": outcome is not None,
            }

        verified = store.get_verified_decisions()[:limit]
        return {"trails": verified, "total": len(verified)}

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


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
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
