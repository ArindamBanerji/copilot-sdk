"""Purchasing economic value endpoints."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter

from app.services.economic_model import PurchasingEconomicModel, demo_cost_impacts


def create_economic_router(service_factory: Callable[[str], PurchasingEconomicModel] | None = None) -> APIRouter:
    router = APIRouter(prefix="/api/purchasing/economic", tags=["purchasing-economic"])

    @router.get("/model")
    def model(tier: str = "food_service_medium") -> dict:
        service = service_factory(tier) if service_factory else PurchasingEconomicModel(tier=tier)
        result = service.compute(1000, demo_cost_impacts() if service_factory is None else None)
        return {
            **result.to_dict(),
            "annual_benchmark": service.annual_benchmark(),
            "summary": service.roi_summary(result),
        }

    @router.get("/roi-summary")
    def roi_summary(tier: str = "food_service_medium") -> dict:
        service = service_factory(tier) if service_factory else PurchasingEconomicModel(tier=tier)
        result = service.compute(1000, demo_cost_impacts() if service_factory is None else None)
        return {
            "summary": service.roi_summary(result),
            "tier": service.tier,
            "provenance": result.provenance,
        }

    return router
