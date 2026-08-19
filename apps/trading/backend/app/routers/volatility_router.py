"""Unified observation-only volatility scenario endpoints."""

from __future__ import annotations

from typing import Any, Callable, cast

from fastapi import APIRouter, Query

from app.routers.analytics import _verified_decisions
from app.services.volatility_analytics import VolatilityAnalytics


GraphStoreFactory = Callable[[], Any]


def create_volatility_router(
    graph_store_factory: GraphStoreFactory | None = None,
    *,
    domain: str = "trading",
) -> APIRouter:
    router = APIRouter(prefix="/api/trading/volatility", tags=["trading-volatility"])
    analytics = VolatilityAnalytics()

    def trades() -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], _verified_decisions(graph_store_factory, domain))

    @router.get("/sharpe")
    def sharpe(regime: str | None = Query(default=None)) -> dict[str, Any]:
        return cast(dict[str, Any], analytics.clustering_adjusted_sharpe(trades(), regime))

    @router.get("/vrp")
    def vrp() -> dict[str, Any]:
        return cast(dict[str, Any], analytics.vrp_analysis(trades()))

    @router.get("/rich-cheap")
    def rich_cheap(regime: str | None = Query(default=None)) -> dict[str, Any]:
        return cast(dict[str, Any], analytics.rich_cheap_regime(trades(), regime))

    @router.get("/dispersion")
    def dispersion() -> dict[str, Any]:
        return cast(dict[str, Any], analytics.dispersion_follow_rate(trades()))

    @router.get("/tail-bets")
    def tail_bets(vix_threshold: float = Query(default=30.0, gt=0.0)) -> dict[str, Any]:
        return cast(dict[str, Any], analytics.effective_bets_in_tail(trades(), vix_threshold))

    return router
