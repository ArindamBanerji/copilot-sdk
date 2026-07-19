"""Trading VIX timing analysis endpoint."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Callable

from fastapi import APIRouter, Request

from app.routers.journal import _journal_records
from app.services.vix_timing import VIXTimingService
from copilot_sdk.state.cached_static import cached_static


GraphStoreFactory = Callable[[], Any]
_provider: Any | None = None


def _market_provider() -> Any:
    global _provider
    if _provider is None:
        from app.connectors.market_source import YFinanceSource
        from app.services.market_data_provider import MarketDataProvider

        _provider = MarketDataProvider(source=YFinanceSource())
    return _provider


def create_vix_timing_router(
    graph_store_factory: GraphStoreFactory | None = None,
    *,
    domain: str = "trading",
) -> APIRouter:
    router = APIRouter(prefix="/api/trading", tags=["trading-vix-timing"])

    @router.get("/vix-timing")
    @cached_static("vix")
    def vix_timing(request: Request) -> dict[str, Any]:
        trades = _journal_records(graph_store_factory, domain)
        vix_data = _vix_history_for_trades(trades)
        return VIXTimingService().analyze(trades, vix_data)

    return router


def _vix_history_for_trades(trades: list[dict[str, Any]]) -> dict[str, float] | None:
    dates = sorted({_trade_date(trade) for trade in trades if _trade_date(trade)})
    if not dates:
        return {}
    start = datetime.fromisoformat(dates[0]).date() - timedelta(days=7)
    end = datetime.fromisoformat(dates[-1]).date() + timedelta(days=1)
    result = _market_provider().get_vix_history(start.isoformat(), end.isoformat())
    value = result.value if result is not None else None
    return value if isinstance(value, dict) else None


def _trade_date(trade: dict[str, Any]) -> str | None:
    metadata = trade.get("metadata") if isinstance(trade.get("metadata"), dict) else {}
    value = trade.get("entry_time") or trade.get("date") or metadata.get("entry_time") or metadata.get("date")
    if not value:
        return None
    text = str(value)
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(text).date().isoformat()
    except ValueError:
        return text[:10] if len(text) >= 10 else None
