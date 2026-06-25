"""Multi-unit purchasing endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.services.multi_unit import MultiUnitManager, demo_locations


def create_multi_unit_router() -> APIRouter:
    router = APIRouter(prefix="/api/purchasing/multi-unit", tags=["purchasing-multi-unit"])
    service = MultiUnitManager()

    @router.get("/dashboard")
    def dashboard() -> dict:
        return service.dashboard(demo_locations()).to_dict()

    @router.get("/compare")
    def compare(metric: str = "accuracy") -> dict:
        return {"locations": service.compare(demo_locations(), metric), "metric": metric, "provenance": "demo"}

    @router.get("/transfer-opportunities")
    def transfer_opportunities() -> dict:
        return {"opportunities": service.find_transfer_opportunities(demo_locations()), "provenance": "demo"}

    return router
