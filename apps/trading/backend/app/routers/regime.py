"""Trading market regime endpoint."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter

from app.routers.journal import _journal_records
from app.services.regime import RegimeService


GraphStoreFactory = Callable[[], Any]
ServiceFactory = Callable[[], RegimeService]


def create_regime_router(
    graph_store_factory: GraphStoreFactory | None = None,
    *,
    domain: str = "trading",
    service_factory: ServiceFactory = RegimeService,
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
