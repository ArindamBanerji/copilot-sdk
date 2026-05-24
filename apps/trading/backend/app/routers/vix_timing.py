"""Trading VIX timing analysis endpoint."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter

from app.routers.journal import _journal_records
from app.services.regime import RegimeService
from app.services.vix_timing import VIXTimingService


GraphStoreFactory = Callable[[], Any]


def create_vix_timing_router(
    graph_store_factory: GraphStoreFactory | None = None,
    *,
    domain: str = "trading",
) -> APIRouter:
    router = APIRouter(prefix="/api/trading", tags=["trading-vix-timing"])

    @router.get("/vix-timing")
    def vix_timing() -> dict[str, Any]:
        trades = _journal_records(graph_store_factory, domain)
        vix_data = RegimeService().get_historical_vix(trades)
        return VIXTimingService().analyze(trades, vix_data)

    return router
