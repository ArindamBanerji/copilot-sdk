"""Auto-order router for conservation-gated purchasing automation."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.auto_order import AutoOrderGate
from copilot_sdk.backend.conservation_utils import compute_conservation_status_payload
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset


DOMAIN = "purchasing"
_PENALTY_RATIO = float(PurchasingPreset().penalty_ratio)
ScorerProvider = Callable[[], Any] | Any


class EvaluateRequest(BaseModel):
    category: str
    confidence: float = Field(ge=0.0, le=1.0)
    order_id: str | None = None
    decision_id: str | None = None
    action: str = "order_as_planned"


def create_auto_order_router(
    gate: AutoOrderGate,
    scorer_provider: ScorerProvider | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/purchasing/auto-order", tags=["auto-order"])

    @router.get("/status")
    def get_status() -> dict[str, Any]:
        conservation = _conservation(scorer_provider)
        return {
            **gate.status,
            "conservation_status": conservation["status"],
            "verified_count": conservation["verified_count"],
        }

    @router.post("/enable")
    def enable() -> dict[str, Any]:
        conservation = _conservation(scorer_provider)
        return gate.enable(str(conservation["status"]))

    @router.post("/disable")
    def disable() -> dict[str, Any]:
        return gate.disable()

    @router.get("/audit")
    def get_audit() -> list[dict[str, Any]]:
        return gate.audit()

    @router.post("/evaluate")
    def evaluate_order(request: EvaluateRequest) -> dict[str, Any]:
        conservation = _category_conservation(scorer_provider, request.category)
        result = gate.evaluate(
            category=request.category,
            confidence=request.confidence,
            conservation_status=str(conservation["status"]),
            verified_count=int(conservation["verified_count"]),
            order_id=request.order_id,
            decision_id=request.decision_id,
            action=request.action,
        )
        result["conservation_status"] = conservation["status"]
        result["verified_count"] = conservation["verified_count"]
        result["conservation_source"] = conservation.get("source")
        result["learning_applied"] = False
        if result["auto_order"] and request.decision_id:
            try:
                _learn_auto_order(
                    scorer_provider,
                    decision_id=request.decision_id,
                    actual_action=request.action,
                    context={
                        "source": "auto_order",
                        "category": request.category,
                        "confidence": request.confidence,
                        "order_id": request.order_id,
                        "spot_check": result["spot_check"],
                    },
                )
            except (KeyError, AssertionError, ValueError) as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            result["learning_applied"] = True
        return result

    return router


def _conservation(provider: ScorerProvider | None) -> dict[str, Any]:
    if provider is None:
        return {"status": "RED", "verified_count": 0, "source": "not_configured"}
    state = provider() if callable(provider) else provider
    payload = compute_conservation_status_payload(DOMAIN, state)
    return {
        "status": str(payload.get("status") or "RED"),
        "verified_count": int(payload.get("verified_count") or 0),
        "source": "global",
    }


def _category_conservation(provider: ScorerProvider | None, category: str) -> dict[str, Any]:
    if provider is None:
        return {"status": "RED", "verified_count": 0, "source": "not_configured"}
    state = provider() if callable(provider) else provider
    decisions = _category_verified_decisions(_store_for_state(state), category)
    if decisions is None:
        fallback = _conservation(provider)
        fallback["source"] = "global_fallback"
        return fallback
    verified_count = len(decisions)
    correct_count = sum(1 for decision in decisions if _is_correct_decision(decision))
    payload = compute_conservation_status_payload(
        DOMAIN,
        {
            "verified_count": verified_count,
            "correct_count": correct_count,
            "penalty_ratio": _PENALTY_RATIO,
        },
    )
    return {
        "status": str(payload.get("status") or "RED"),
        "verified_count": verified_count,
        "correct_count": correct_count,
        "source": "category",
    }


def _store_for_state(state: Any) -> Any | None:
    if state is None:
        return None
    if callable(getattr(state, "get_verified_decisions", None)) or callable(getattr(state, "get_decisions", None)):
        return state
    return getattr(state, "graph_store", None) or getattr(state, "_graph_store", None)


def _category_verified_decisions(store: Any | None, category: str) -> list[dict[str, Any]] | None:
    if store is None:
        return None
    get_verified = getattr(store, "get_verified_decisions", None)
    if callable(get_verified):
        try:
            decisions = list(get_verified(DOMAIN) or [])
        except TypeError:
            decisions = list(get_verified() or [])
        return [
            decision
            for decision in decisions
            if _decision_category(decision) == category and _is_verified_decision(decision)
        ]
    get_decisions = getattr(store, "get_decisions", None)
    if callable(get_decisions):
        try:
            decisions = list(get_decisions(DOMAIN, category=category, limit=10**12) or [])
        except TypeError:
            decisions = list(get_decisions(DOMAIN, category, 10**12) or [])
        return [decision for decision in decisions if _is_verified_decision(decision)]
    return None


def _decision_category(decision: dict[str, Any]) -> str:
    metadata = decision.get("metadata") if isinstance(decision.get("metadata"), dict) else {}
    context = decision.get("context") if isinstance(decision.get("context"), dict) else {}
    return str(decision.get("category") or metadata.get("category") or context.get("category") or "")


def _is_verified_decision(decision: dict[str, Any]) -> bool:
    status = str(decision.get("status") or decision.get("outcome") or "").strip().lower()
    return status in {"confirmed", "overridden"} or decision.get("is_correct") is not None


def _is_correct_decision(decision: dict[str, Any]) -> bool:
    if decision.get("is_correct") is not None:
        return bool(decision.get("is_correct"))
    status = str(decision.get("status") or decision.get("outcome") or "").strip().lower()
    return status == "confirmed"


def _learn_auto_order(
    provider: ScorerProvider | None,
    *,
    decision_id: str,
    actual_action: str,
    context: dict[str, Any],
) -> Any:
    if provider is None:
        raise ValueError("auto-order learning requires a scorer provider")
    state = provider() if callable(provider) else provider
    scorer_factory = getattr(state, "_scorer", None)
    if callable(scorer_factory):
        scorer = scorer_factory()
        return scorer.learn(decision_id, actual_action, "confirmed", context=context)
    learn = getattr(state, "learn", None)
    if not callable(learn):
        raise ValueError("auto-order learning requires learn()")
    try:
        return learn(decision_id, actual_action, "confirmed", context=context)
    except TypeError:
        return learn(decision_id, actual_action, "confirmed")
