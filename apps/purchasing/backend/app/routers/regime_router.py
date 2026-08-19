"""Purchasing situation endpoint backed by the shared regime architecture."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter

from copilot_sdk.regime import PurchasingRegimePolicy, RegimeConditioner, RegimeDetector, RegimeState


def create_regime_router(scorer_provider: Callable[[], Any]) -> APIRouter:
    router = APIRouter(prefix="/api/purchasing", tags=["purchasing-regime"])
    policy = PurchasingRegimePolicy()
    detector = RegimeDetector(policy)
    conditioner = RegimeConditioner(policy)

    @router.get("/situation")
    def situation(
        demand_variance: float = 0.0,
        stock_days: float = 14.0,
        supply_fill_rate: float = 1.0,
        seasonality: float = 0.0,
    ) -> dict[str, Any]:
        state = detector.detect({
            "demand_variance": demand_variance,
            "stock_days": stock_days,
            "supply_fill_rate": supply_fill_rate,
            "seasonality": seasonality,
        })
        return _payload(state.to_dict(), conditioner, scorer_provider)

    return router


def _payload(
    state: dict[str, Any],
    conditioner: RegimeConditioner,
    scorer_provider: Callable[[], Any],
) -> dict[str, Any]:
    decisions: list[dict[str, Any]] = []
    try:
        store = getattr(scorer_provider(), "graph_store", None)
        getter = getattr(store, "get_verified_decisions", None)
        if callable(getter):
            decisions = list(getter("purchasing"))
    except (AttributeError, TypeError, ValueError):
        decisions = []
    conditioned = conditioner.condition(
        {"verified_decisions": decisions},
        RegimeState(**state),
    )
    return {
        **state,
        "conditioned_context": conditioned.to_dict(),
        "observation_only": True,
    }
