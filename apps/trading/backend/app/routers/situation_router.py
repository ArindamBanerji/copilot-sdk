"""Situation-conditioned Trading demo endpoints."""

from __future__ import annotations

from typing import Any, Callable, cast

from fastapi import APIRouter

from app.routers.regime_analytics import _read_decisions
from app.services.situation_analyzer import (
    check_regime_data_sufficiency,
    compute_regime_conditioned_stats,
    compute_regime_rejections,
    compute_sharpe_adjustment,
    detect_regime,
)


GraphStoreFactory = Callable[[], Any]


def create_situation_router(
    graph_store_factory: GraphStoreFactory | None = None,
    *,
    domain: str = "trading",
) -> APIRouter:
    router = APIRouter(prefix="/api/trading/situation", tags=["trading-situation"])

    def decisions() -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], _read_decisions(graph_store_factory, domain))

    @router.get("/regime")
    def current_regime() -> dict[str, Any]:
        rows = decisions()
        regime = detect_regime(rows)
        conditioned = compute_regime_conditioned_stats(rows, regime)
        regime_break = _regime_break(rows)
        return {
            "regime": regime,
            "previous_regime": regime_break["previous_regime"],
            "regime_break": regime_break["active"],
            "detected_by": "synthetic preseed regime tags",
            "hurst": 0.62 if regime == "trending" else 0.48,
            "vol_state": "elevated" if regime == "volatile" else "normal",
            "conservation_status": "AMBER" if regime_break["active"] else "GREEN",
            "autonomy": "throttled" if regime_break["active"] else "normal",
            "autonomy_multiplier": 0.5 if regime_break["active"] else 1.0,
            "message": "Observation: regime break detected; conservation is AMBER and autonomy state is reduced." if regime_break["active"] else f"Current illustrative regime: {regime}.",
            "provenance": conditioned["provenance"],
            "substantiation": conditioned["substantiation"],
        }

    @router.get("/conditioned-stats")
    def conditioned_stats(regime: str | None = None) -> dict[str, Any]:
        rows = decisions()
        return cast(dict[str, Any], compute_regime_conditioned_stats(rows, regime))

    @router.get("/sharpe-adjustment")
    def sharpe_adjustment() -> dict[str, Any]:
        return cast(dict[str, Any], compute_sharpe_adjustment(decisions()))

    @router.get("/abstention")
    def abstention_check() -> dict[str, Any]:
        rows = decisions()
        return cast(dict[str, Any], check_regime_data_sufficiency(rows, detect_regime(rows)))

    @router.get("/regime-rejections")
    def regime_rejections() -> dict[str, Any]:
        return cast(dict[str, Any], compute_regime_rejections(decisions()))

    return router


def _regime_break(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    regimes = []
    for decision in decisions:
        value = decision.get("regime") or decision.get("current_regime")
        if value:
            regimes.append(str(value).lower())
    if len(regimes) < 2:
        return {"active": False, "previous_regime": None}
    active = regimes[-1] != regimes[-2] and len(regimes) >= 10
    return {"active": active, "previous_regime": regimes[-2]}
