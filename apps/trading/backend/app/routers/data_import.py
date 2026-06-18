"""Trading data import and market-data endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import JSONResponse

from app.brokers import get_broker
from app.connectors.alpaca_connector import AlpacaConnector
from app.connectors.csv_connector import CSVConnector
from app.models.trade import NormalizedTrade

_provider: Any | None = None
VALID_CSV_PRESETS = {"alpaca", "robinhood", "thinkorswim", "webull"}


def _market_provider() -> Any:
    global _provider
    if _provider is None:
        from app.connectors.market_source import YFinanceSource
        from app.services.market_data_provider import MarketDataProvider

        _provider = MarketDataProvider(source=YFinanceSource())
    return _provider


def _trade_value(trade: Any, field: str) -> Any:
    if isinstance(trade, dict):
        return trade.get(field)
    return getattr(trade, field, None)


def _trade_to_dict(trade: Any) -> dict[str, Any]:
    if isinstance(trade, dict):
        data = dict(trade)
    elif hasattr(trade, "to_dict"):
        data = trade.to_dict()
    else:
        data = dict(trade)
    for field in ("strike", "expiry", "option_type", "multiplier"):
        value = _trade_value(trade, field)
        if value is not None:
            data[field] = value
    return data


def _trade_key(trade: Any) -> tuple[str, str, float, str]:
    ticker = str(_trade_value(trade, "ticker") or "").upper()
    entry_time = _trade_value(trade, "entry_time")
    if hasattr(entry_time, "date"):
        date_key = entry_time.date().isoformat()
    else:
        date_key = str(entry_time or "")[:10]
    size = abs(float(_trade_value(trade, "size") or 0.0))
    direction = str(_trade_value(trade, "direction") or _trade_value(trade, "side") or "unknown").lower()
    return (ticker, date_key, size, direction)


def _decode_csv_payload(payload: Any) -> tuple[str, dict[str, Any]]:
    if isinstance(payload, (bytes, bytearray)):
        return bytes(payload).decode("utf-8-sig"), {}
    if isinstance(payload, str):
        return payload, {}
    if isinstance(payload, dict):
        text = payload.get("csv_content", payload.get("content", payload.get("csv", "")))
        if isinstance(text, (bytes, bytearray)):
            text = bytes(text).decode("utf-8-sig")
        return str(text or ""), payload
    raise HTTPException(status_code=400, detail="CSV import expects text/csv or a JSON body.")


def _broker_import_connector(broker: str) -> Any:
    if broker == "alpaca":
        return AlpacaConnector()
    return get_broker(broker)


def create_data_import_router() -> tuple[APIRouter, list[NormalizedTrade]]:
    router = APIRouter(prefix="/api/trading", tags=["trading-data"])
    trade_store: list[NormalizedTrade] = []

    # Demo in-memory storage. Production should replace this with GraphStore-backed persistence.
    @router.post("/import/csv")
    def import_csv(payload: Any = Body(..., media_type="text/csv")) -> dict[str, Any]:
        text, options = _decode_csv_payload(payload)
        preset = options.get("preset") or options.get("broker_preset")
        if preset:
            normalized_preset = str(preset).lower().strip()
            if normalized_preset not in VALID_CSV_PRESETS:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": f"Unknown preset: {preset}",
                        "valid_presets": sorted(VALID_CSV_PRESETS),
                    },
                )
        else:
            normalized_preset = None
        trades = CSVConnector().import_from_string(
            text,
            broker_preset=normalized_preset,
            column_map=options.get("column_map"),
            date_format=options.get("date_format"),
            delimiter=options.get("delimiter"),
        )
        trade_store.extend(trades)
        return {
            "imported": len(trades),
            "total": len(trade_store),
            "trades": [_trade_to_dict(trade) for trade in trades],
        }

    @router.post("/import/broker")
    def import_broker(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
        broker_name = str(payload.get("broker") or "").strip().lower()
        if broker_name not in {"ibkr", "alpaca"}:
            raise HTTPException(status_code=400, detail="broker must be 'ibkr' or 'alpaca'")
        try:
            days = int(payload.get("days", 365))
            connector = _broker_import_connector(broker_name)
            import_trades = getattr(connector, "import_trades", None)
            if not callable(import_trades):
                raise RuntimeError(f"{broker_name} connector does not support trade import")
            trades = list(import_trades(days=days) or [])
        except (TypeError, ValueError):
            return JSONResponse(status_code=400, content={"error": "Invalid days parameter"})
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"{broker_name} import failed: {exc}") from exc

        existing = {_trade_key(trade) for trade in trade_store}
        imported: list[Any] = []
        skipped = 0
        for trade in trades:
            key = _trade_key(trade)
            if key in existing:
                skipped += 1
                continue
            trade_store.append(trade)
            imported.append(trade)
            existing.add(key)
        return {
            "broker": broker_name,
            "imported": len(imported),
            "skipped": skipped,
            "errors": 0,
            "total": len(trade_store),
            "trades": [_trade_to_dict(trade) for trade in imported],
        }

    @router.get("/trades")
    def list_trades(ticker: str | None = None) -> dict[str, Any]:
        trades = trade_store
        if ticker:
            normalized = ticker.upper()
            trades = [trade for trade in trade_store if str(_trade_value(trade, "ticker") or "").upper() == normalized]
        return {"trades": [_trade_to_dict(trade) for trade in trades], "count": len(trades)}

    @router.get("/trades/{trade_id}")
    def get_trade(trade_id: str) -> dict[str, Any]:
        for trade in trade_store:
            if _trade_value(trade, "trade_id") == trade_id:
                return _trade_to_dict(trade)
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
