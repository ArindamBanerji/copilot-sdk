"""Trading correlation monitoring endpoint."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Query, Request

from app.routers.journal import _journal_records
from app.services.correlation import DEFAULT_WINDOW, CorrelationService


GraphStoreFactory = Callable[[], Any]
_provider: Any | None = None


def _correlation_service(window_days: int) -> CorrelationService:
    global _provider
    if _provider is None:
        from app.connectors.market_source import YFinanceSource
        from app.services.market_data_provider import MarketDataProvider

        _provider = MarketDataProvider(source=YFinanceSource())
    return CorrelationService(window_days=window_days, provider=_provider)


def create_correlation_router(
    graph_store_factory: GraphStoreFactory | None = None,
    *,
    domain: str = "trading",
) -> APIRouter:
    router = APIRouter(prefix="/api/trading", tags=["trading-correlation"])

    @router.get("/correlation")
    def correlation(request: Request, window: int = Query(default=DEFAULT_WINDOW, ge=2, le=252)) -> dict[str, Any]:
        trades = _journal_records(graph_store_factory, domain)
        return _correlation_service(window).compute(trades)

    return router
