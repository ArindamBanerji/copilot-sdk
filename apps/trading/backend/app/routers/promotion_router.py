"""Category-level Trading promotion engine endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.promotion_engine import PromotionEngine
from app.services.promotion_state import PromotionStateStore
from copilot_sdk.backend.conservation_router import _check_payload, _state_counts
from copilot_sdk.scoring.presets.trading import TradingPreset


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
    def dashboard() -> list[dict[str, Any]]:
        return _engine().dashboard()

    @router.get("/{category}")
    def category_evaluation(category: str) -> dict[str, Any]:
        _ensure_category(category, categories)
        return _engine().evaluate(category)

    @router.post("/{category}/promote")
    def promote(category: str, request: PromoteRequest) -> dict[str, Any]:
        _ensure_category(category, categories)
        try:
            return _engine().promote(category, confirmed_by=request.confirmed_by)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.post("/{category}/demote")
    def demote(category: str, request: DemoteRequest) -> dict[str, Any]:
        _ensure_category(category, categories)
        return _engine().demote(category, reason=request.reason)

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
        )
        return {**counts, **_check_payload(check)}
    except Exception:
        return {"status": "UNKNOWN", "conservation_status": "UNKNOWN", "domain": domain}
