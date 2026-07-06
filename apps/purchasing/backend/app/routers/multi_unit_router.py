"""Multi-unit purchasing endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.services.multi_unit import MultiUnitManager, chain_demo_locations


def create_multi_unit_router() -> APIRouter:
    router = APIRouter(prefix="/api/purchasing/multi-unit", tags=["purchasing-multi-unit"])
    service = MultiUnitManager()

    @router.get("/dashboard")
    def dashboard(request: Request) -> dict:
        return service.dashboard(_locations(request)).to_dict()

    @router.get("/compare")
    def compare(request: Request, metric: str = "accuracy") -> dict:
        return {"locations": service.compare(_locations(request), metric), "metric": metric, "provenance": "demo"}

    @router.get("/transfer-opportunities")
    def transfer_opportunities(request: Request) -> dict:
        return {"opportunities": service.find_transfer_opportunities(_locations(request)), "provenance": "demo"}

    return router


def _locations(request: Request) -> list[dict]:
    return chain_demo_locations(getattr(request.app.state, "purchasing_chain_demo", None))
