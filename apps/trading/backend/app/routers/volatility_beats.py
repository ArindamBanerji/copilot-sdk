"""Observation-only Trading volatility demo-beat endpoints."""

from __future__ import annotations

from typing import Any, Callable, cast

from fastapi import APIRouter, Query

from app.analytics.vrp_attribution import TAIL_THRESHOLD
from app.routers.analytics import _verified_decisions
from app.services.regime_analytics import RegimeAnalytics
from app.services.situation_analyzer import (
    check_regime_data_sufficiency,
    compute_regime_conditioned_stats,
    detect_regime,
)
from app.services.volatility_analytics import VolatilityAnalytics


GraphStoreFactory = Callable[[], Any]


def create_volatility_beats_router(
    graph_store_factory: GraphStoreFactory | None = None,
    *,
    domain: str = "trading",
) -> APIRouter:
    router = APIRouter(prefix="/api/trading/vol", tags=["trading-volatility-beats"])
    analytics = VolatilityAnalytics()

    def decisions() -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], _verified_decisions(graph_store_factory, domain))

    @router.get("/short-vol-illusion")
    def short_vol_illusion() -> dict[str, Any]:
        rows = decisions()
        sharpe = analytics.clustering_adjusted_sharpe(rows)
        high_tail = sum(
            1
            for row in rows
            if (_number(row, "tail_dependence", "tail_dep", "tail_gap") or 0.0) > TAIL_THRESHOLD
        )
        naive = _number(sharpe, "naive_quality_score")
        adjusted = _number(sharpe, "quality_adjusted_score")
        detected = high_tail > 0 and naive is not None and adjusted is not None and adjusted < naive
        return {
            **sharpe,
            "clustering_adjustment_factor": round(adjusted / naive, 4) if naive and adjusted is not None else None,
            "tail_risk_indicator": {
                "high_tail_decisions": high_tail,
                "threshold": TAIL_THRESHOLD,
                "status": "observed" if high_tail else "insufficient_data",
            },
            "short_vol_illusion": detected,
            "warning": "Clustering-adjusted quality is lower in tail-linked decisions." if detected else None,
        }

    @router.get("/vrp-edge")
    def vrp_edge() -> dict[str, Any]:
        payload = analytics.vrp_analysis(decisions())
        tail = payload.get("tail_attribution", {})
        return {
            **payload,
            "vrp_edge": payload.get("vrp_spread_mean"),
            "insurance_cost": payload.get("high_tail_loss_ratio"),
            "tail_dependence": tail,
            "selling_insurance": payload.get("classification") == "edge",
        }

    @router.get("/situational-abstention")
    def situational_abstention() -> dict[str, Any]:
        rows = decisions()
        regime = detect_regime(rows)
        result = dict(check_regime_data_sufficiency(rows, regime))
        conditioned = compute_regime_conditioned_stats(rows, regime)
        result.update(
            {
                "current_regime": regime,
                "per_regime_decisions": {
                    str(key): int(value.get("decision_count", 0))
                    for key, value in conditioned.get("regimes", {}).items()
                    if isinstance(value, dict)
                },
                "vol_context": True,
                "alias_of": "/api/trading/regime/abstention",
                "observation_only": True,
            }
        )
        return result

    @router.get("/rich-cheap")
    def rich_cheap(regime: str | None = Query(default=None)) -> dict[str, Any]:
        return cast(dict[str, Any], analytics.rich_cheap_regime(decisions(), regime))

    @router.get("/dispersion-follow")
    def dispersion_follow() -> dict[str, Any]:
        payload = analytics.dispersion_follow_rate(decisions())
        return {**payload, "skipped_signal_dollar_impact": payload.get("skipped_value")}

    @router.get("/effective-bets")
    def effective_bets(vix_threshold: float = Query(default=30.0, gt=0.0)) -> dict[str, Any]:
        return cast(dict[str, Any], analytics.effective_bets_in_tail(decisions(), vix_threshold))

    return router


def _number(payload: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        raw = payload.get(key)
        if raw is None:
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        return value
    return None
