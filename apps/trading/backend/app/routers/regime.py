"""Trading market regime endpoint."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Request

from app.routers.journal import _journal_records
from app.services.regime import RegimeService
from app.services.regime_recommender import RegimeRecommender
from copilot_sdk.backend.conservation_router import _check_payload, _state_counts
from copilot_sdk.state.cached_static import cached_static


GraphStoreFactory = Callable[[], Any]
ServiceFactory = Callable[[], RegimeService]
_provider: Any | None = None


def _regime_service() -> RegimeService:
    global _provider
    if _provider is None:
        from app.connectors.market_source import YFinanceSource
        from app.services.market_data_provider import MarketDataProvider

        _provider = MarketDataProvider(source=YFinanceSource())
    return RegimeService(provider=_provider)


def create_regime_router(
    graph_store_factory: GraphStoreFactory | None = None,
    *,
    domain: str = "trading",
    service_factory: ServiceFactory = _regime_service,
    regime_break_provider: Callable[[], bool] | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/trading", tags=["trading-regime"])

    @router.get("/regime")
    @cached_static("regime")
    def current_regime(request: Request) -> dict[str, Any]:
        service = service_factory()
        trades = _journal_records(graph_store_factory, domain)
        current = service.get_current_regime()
        accuracy = service.get_regime_accuracy(trades)
        return {
            "current": current,
            "accuracy_by_category": accuracy,
            "recommendations": _regime_recommendations(
                str(current.get("regime") or "ranging"),
                accuracy,
                regime_break_active=_regime_break_active(regime_break_provider),
            ),
        }

    @router.get("/regime/detail")
    def regime_detail(previous_regime: str | None = None) -> dict[str, Any]:
        service = service_factory()
        trades = _journal_records(graph_store_factory, domain)
        current = service.get_current_regime()
        accuracy = service.get_regime_accuracy(trades)
        conservation = _conservation_status(graph_store_factory)
        payload = RegimeRecommender().recommend(
            str(current.get("regime") or "ranging"),
            accuracy,
            conservation_status=conservation,
            trades=trades,
            current=current,
            previous_regime=previous_regime,
        )
        if _regime_break_active(regime_break_provider):
            payload = dict(payload)
            sizing = payload.get("sizing_recommendation")
            if isinstance(sizing, dict):
                payload["sizing_recommendation"] = {
                    **sizing,
                    "action": "paused",
                    "suggested_size_multiplier": 0.0,
                    "max_size_multiplier": 0.0,
                    "paused": True,
                    "reason": "regime_break_active",
                }
        return payload

    return router


def _regime_recommendations(
    current_regime: str,
    accuracy: dict[str, dict[str, float]],
    *,
    regime_break_active: bool = False,
) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    for category, regimes in accuracy.items():
        values = [float(value) for value in regimes.values()]
        baseline = sum(values) / len(values) if values else 0.5
        current_accuracy = float(regimes.get(current_regime, 0.5))
        delta = current_accuracy - baseline
        if regime_break_active:
            action = "hold"
        elif delta > 0.05:
            action = "increase"
        elif delta < -0.10:
            action = "reduce"
        else:
            action = "hold"
        recommendations.append(
            {
                "category": category,
                "current_regime": current_regime,
                "accuracy": round(current_accuracy, 4),
                "baseline": round(baseline, 4),
                "delta": round(delta, 4),
                "action": action,
            }
        )
    return sorted(recommendations, key=lambda item: item["accuracy"], reverse=True)


def _regime_break_active(provider: Callable[[], bool] | None) -> bool:
    if provider is None:
        return False
    try:
        return bool(provider())
    except Exception:
        return False


def _conservation_status(graph_store_factory: GraphStoreFactory | None) -> dict[str, Any] | None:
    if graph_store_factory is None:
        return None
    store = None
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
        return None
    finally:
        close = getattr(store, "close", None)
        if callable(close):
            close()
