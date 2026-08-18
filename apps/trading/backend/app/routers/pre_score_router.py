"""Read-only pre-trade scorer endpoint."""

from __future__ import annotations

from dataclasses import asdict
import math
from typing import Any, Callable

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.routers.regime_router import _current_market, _market_provider
from app.services.pre_scorer import PreScorer
from app.services.regime_classifier import RegimeClassifier
from copilot_sdk.scoring.presets.trading import TradingPreset


GraphStoreFactory = Callable[[], Any]
RegimeContextFactory = Callable[[], Any]


class PreScoreRequest(BaseModel):
    category: str
    factors: dict[str, Any] = Field(default_factory=dict)


class CurrentRegimeContext:
    """Small adapter exposing current_regime() for PreScorer."""

    def current_regime(self) -> dict[str, Any]:
        return _current_market(_market_provider(), RegimeClassifier())


def create_pre_score_router(
    scorer: Any,
    graph_store_factory: GraphStoreFactory,
    *,
    regime_context_factory: RegimeContextFactory | None = CurrentRegimeContext,
    preset: TradingPreset | None = None,
    domain: str = "trading",
) -> APIRouter:
    router = APIRouter(prefix="/api/trading", tags=["trading-pre-score"])
    trading_preset = preset or TradingPreset()
    shape = trading_preset.shape
    categories = tuple(shape.category_names)
    factor_names = tuple(shape.factor_names)

    @router.post("/pre-score")
    def pre_score(request: PreScoreRequest) -> dict[str, Any]:
        category = str(request.category or "").strip()
        if category not in categories:
            raise HTTPException(status_code=400, detail=f"unknown category: {category}")

        clean_factors = _validate_factors(request.factors, factor_names)
        store = graph_store_factory()
        regime_context = regime_context_factory() if regime_context_factory is not None else None
        service = PreScorer(
            scorer,
            store,
            regime_context,
            preset=trading_preset,
            domain=domain,
        )
        payload = asdict(service.pre_score(category, clean_factors))
        payload["preview"] = True
        payload["observation_only"] = True
        payload["message"] = "preview - no decision recorded"
        return payload

    return router


def _validate_factors(
    factors: dict[str, Any],
    factor_names: tuple[str, ...],
) -> dict[str, float]:
    missing = [name for name in factor_names if name not in factors]
    if missing:
        raise HTTPException(status_code=400, detail=f"missing factors: {', '.join(missing)}")

    clean: dict[str, float] = {}
    for name in factor_names:
        try:
            value = float(factors[name])
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=f"factor {name} must be numeric") from exc
        if not math.isfinite(value):
            raise HTTPException(status_code=400, detail=f"factor {name} must be numeric")
        clean[name] = value
    return clean
