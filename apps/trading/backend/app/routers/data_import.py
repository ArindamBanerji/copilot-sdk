"""Trading data import and market-data endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query

from app.connectors.csv_connector import CSVConnector
from app.models.trade import NormalizedTrade

_provider: Any | None = None


def _market_provider() -> Any:
    global _provider
    if _provider is None:
        from app.connectors.market_source import YFinanceSource
        from app.services.market_data_provider import MarketDataProvider

        _provider = MarketDataProvider(source=YFinanceSource())
    return _provider


def create_data_import_router() -> tuple[APIRouter, list[NormalizedTrade]]:
    router = APIRouter(prefix="/api/trading", tags=["trading-data"])
    trade_store: list[NormalizedTrade] = []

    # Demo in-memory storage. Production should replace this with GraphStore-backed persistence.
    @router.post("/import/csv")
    def import_csv(csv_content: bytes = Body(..., media_type="text/csv")) -> dict[str, Any]:
        text = csv_content.decode("utf-8-sig")
        trades = CSVConnector().import_from_string(text)
        trade_store.extend(trades)
        return {
            "imported": len(trades),
            "total": len(trade_store),
            "trades": [trade.to_dict() for trade in trades],
        }

    @router.get("/trades")
    def list_trades(ticker: str | None = None) -> dict[str, Any]:
        trades = trade_store
        if ticker:
            normalized = ticker.upper()
            trades = [trade for trade in trade_store if trade.ticker == normalized]
        return {"trades": [trade.to_dict() for trade in trades], "count": len(trades)}

    @router.get("/trades/{trade_id}")
    def get_trade(trade_id: str) -> dict[str, Any]:
        for trade in trade_store:
            if trade.trade_id == trade_id:
                return trade.to_dict()
        raise HTTPException(status_code=404, detail=f"Trade not found: {trade_id}")

    @router.get("/market/ohlcv")
    def get_ohlcv(
        ticker: str = Query(..., min_length=1),
        period: str = "1mo",
        interval: str = "1d",
    ) -> dict[str, Any]:
        result = _market_provider().get_ohlcv(ticker.upper(), period=period)
        rows = result.value or []
        return {
            "ticker": ticker.upper(),
            "rows": rows,
            "count": len(rows),
        }

    @router.get("/market/vix")
    def get_vix() -> dict[str, Any]:
        rows_result = _market_provider().get_ohlcv("^VIX")
        current_result = _market_provider().get_vix_current()
        rows = rows_result.value or []
        current = float(rows[-1]["close"]) if rows else None
        if current_result.value is not None:
            current = float(current_result.value)
        return {
            "ticker": "^VIX",
            "current": current,
            "rows": rows,
            "count": len(rows),
        }

    @router.post("/market/refresh")
    def refresh_market() -> dict[str, Any]:
        provider = _market_provider()
        provider.refresh()
        result = provider.get_market_snapshot()
        return {
            "refreshed": True,
            "provenance": {
                "source": result.source,
                "as_of": result.as_of,
            },
        }

    return router, trade_store


router, _trade_store_ref = create_data_import_router()
