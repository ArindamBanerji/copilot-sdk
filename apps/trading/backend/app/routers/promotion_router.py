"""Category-level Trading promotion engine endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, cast

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.services.promotion_engine import PromotionEngine
from app.services.promotion_state import PromotionStateStore
from copilot_sdk.backend.conservation_router import _check_payload, _state_counts
from copilot_sdk.scoring.mutation_lock import serialize_mutation
from copilot_sdk.scoring.presets.trading import TradingPreset
from copilot_sdk.state.cached_static import cached_static
from app.services.claim_gate import TradingPromotionGuard


GraphStoreFactory = Callable[[], Any]
ConservationStatusFactory = Callable[[], dict[str, Any]]
DEFAULT_STATE_PATH = Path(__file__).resolve().parents[2] / "data" / "promotion_state.json"


class PromoteRequest(BaseModel):
    confirmed_by: str = Field(default="trader")


class DemoteRequest(BaseModel):
    reason: str = Field(default="trader requested demotion")


_STATE_STORE = PromotionStateStore(DEFAULT_STATE_PATH)


def create_promotion_engine_router(
    graph_store_factory: GraphStoreFactory,
    *,
    conservation_status_factory: ConservationStatusFactory | None = None,
    state_store: PromotionStateStore | None = None,
    preset: TradingPreset | None = None,
    domain: str = "trading",
    promotion_guard: TradingPromotionGuard | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/trading/promotion", tags=["trading-promotion-engine"])
    trading_preset = preset or TradingPreset()
    states = state_store or _STATE_STORE
    categories = set(trading_preset.shape.category_names)

    def _engine() -> PromotionEngine:
        conservation = (
            conservation_status_factory()
            if conservation_status_factory is not None
            else _conservation_status(graph_store_factory, domain)
        )
        return PromotionEngine(
            graph_store_factory(),
            trading_preset,
            conservation,
            state_store=states,
            domain=domain,
        )

    @router.get("/dashboard")
    @cached_static("promotion")
    def dashboard(request: Request) -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], _engine().dashboard())

    @router.get("/{category}")
    def category_evaluation(category: str) -> dict[str, Any]:
        _ensure_category(category, categories)
        return cast(dict[str, Any], _engine().evaluate(category))

    @router.post("/{category}/promote")
    @serialize_mutation(domain, event="evolution")
    def promote(category: str, request: PromoteRequest) -> dict[str, Any]:
        _ensure_category(category, categories)
        try:
            if promotion_guard is not None:
                decision = promotion_guard.authorize(
                    category,
                    _conservation_status(graph_store_factory, domain),
                )
                if not decision.allowed:
                    raise HTTPException(
                        status_code=409,
                        detail={
                            "error": "promotion_claim_gate_blocked",
                            "reason": decision.reason,
                            "evidence_tier": decision.evidence_tier,
                            "evidence_label": decision.evidence_label,
                        },
                    )
            payload = _engine().promote(category, confirmed_by=request.confirmed_by)
            if promotion_guard is not None:
                payload = {
                    **payload,
                    "promotion_state_machine": promotion_guard.advance_observed(
                        category,
                        _conservation_status(graph_store_factory, domain),
                    ),
                }
            return cast(dict[str, Any], payload)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.post("/{category}/demote")
    @serialize_mutation(domain, event="evolution")
    def demote(category: str, request: DemoteRequest) -> dict[str, Any]:
        _ensure_category(category, categories)
        return cast(dict[str, Any], _engine().demote(category, reason=request.reason))

    return router


def _ensure_category(category: str, categories: set[str]) -> None:
    if category not in categories:
        raise HTTPException(status_code=404, detail=f"unknown category: {category}")


def _conservation_status(
    graph_store_factory: GraphStoreFactory,
    domain: str,
) -> dict[str, Any]:
    try:
        store = graph_store_factory()
        counts = _state_counts(store)
        from gae.calibration import conservation_status

        check = conservation_status(
            verified_count=counts["verified_count"],
            correct_count=counts["correct_count"],
            total_decisions=counts["total_decisions"],
            penalty_ratio=counts["penalty_ratio"],
            categories_with_data=store.count_categories_with_n(domain, 1),
            total_categories=len(TradingPreset().shape.category_names),
        )
        return {**counts, **_check_payload(check)}
    except Exception:
        return {"status": "UNKNOWN", "conservation_status": "UNKNOWN", "domain": domain}
