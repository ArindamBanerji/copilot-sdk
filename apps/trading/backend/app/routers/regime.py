"""Trading market regime endpoint."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter

from app.routers.journal import _journal_records
from app.services.regime import RegimeService
from app.services.regime_recommender import RegimeRecommender
from copilot_sdk.backend.conservation_router import _check_payload, _state_counts


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
) -> APIRouter:
    router = APIRouter(prefix="/api/trading", tags=["trading-regime"])

    @router.get("/regime")
    def current_regime() -> dict[str, Any]:
        service = service_factory()
        trades = _journal_records(graph_store_factory, domain)
        current = service.get_current_regime()
        accuracy = service.get_regime_accuracy(trades)
        return {
            "current": current,
            "accuracy_by_category": accuracy,
            "recommendations": _regime_recommendations(str(current.get("regime") or "ranging"), accuracy),
        }

    @router.get("/regime/detail")
    def regime_detail(previous_regime: str | None = None) -> dict[str, Any]:
        service = service_factory()
        trades = _journal_records(graph_store_factory, domain)
        current = service.get_current_regime()
        accuracy = service.get_regime_accuracy(trades)
        conservation = _conservation_status(graph_store_factory)
        return RegimeRecommender().recommend(
            str(current.get("regime") or "ranging"),
            accuracy,
            conservation_status=conservation,
            trades=trades,
            current=current,
            previous_regime=previous_regime,
        )

    return router


def _regime_recommendations(
    current_regime: str,
    accuracy: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    for category, regimes in accuracy.items():
        values = [float(value) for value in regimes.values()]
        baseline = sum(values) / len(values) if values else 0.5
        current_accuracy = float(regimes.get(current_regime, 0.5))
        delta = current_accuracy - baseline
        if delta > 0.05:
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
