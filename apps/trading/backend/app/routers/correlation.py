"""Trading correlation monitoring endpoint."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Query

from app.routers.journal import _journal_records
from app.services.correlation import DEFAULT_WINDOW, CorrelationService


GraphStoreFactory = Callable[[], Any]


def create_correlation_router(
    graph_store_factory: GraphStoreFactory | None = None,
    *,
    domain: str = "trading",
) -> APIRouter:
    router = APIRouter(prefix="/api/trading", tags=["trading-correlation"])

    @router.get("/correlation")
    def correlation(window: int = Query(default=DEFAULT_WINDOW, ge=2, le=252)) -> dict[str, Any]:
        trades = _journal_records(graph_store_factory, domain)
        return CorrelationService(window_days=window).compute(trades)

    return router
