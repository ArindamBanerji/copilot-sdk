"""Trading data import and market-data endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query

from app.connectors.csv_connector import CSVConnector
from app.connectors.yfinance_provider import YFinanceProvider
from app.models.trade import NormalizedTrade


def create_data_import_router() -> tuple[APIRouter, list[NormalizedTrade]]:
    router = APIRouter(prefix="/api/trading", tags=["trading-data"])
    trade_store: list[NormalizedTrade] = []

    # Demo in-memory storage. Production should replace this with SQLite/DecisionStore.
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
        rows = YFinanceProvider().get_ohlcv(ticker, period=period, interval=interval)
        return {"ticker": ticker.upper(), "rows": rows, "count": len(rows)}

    @router.get("/market/vix")
    def get_vix() -> dict[str, Any]:
        provider = YFinanceProvider()
        rows = provider.get_vix()
        current = float(rows[-1]["close"]) if rows else None
        return {"ticker": "^VIX", "current": current, "rows": rows, "count": len(rows)}

    return router, trade_store


router, _trade_store_ref = create_data_import_router()
