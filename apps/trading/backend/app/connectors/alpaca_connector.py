"""Optional Alpaca data connector."""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any

from app.models.trade import NormalizedTrade


class AlpacaConnector:
    def __init__(self, api_key: str | None = None, secret_key: str | None = None):
        self.api_key = api_key or os.environ.get("APCA_API_KEY_ID")
        self.secret_key = secret_key or os.environ.get("APCA_API_SECRET_KEY")
        self._client = None

    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        if not self.api_key or not self.secret_key:
            raise RuntimeError("Alpaca credentials are not configured")
        try:
            from alpaca.trading.client import TradingClient
        except ImportError as exc:
            raise RuntimeError("alpaca-py is not installed") from exc
        self._client = TradingClient(self.api_key, self.secret_key)
        return self._client

    def test_connection(self) -> dict[str, Any]:
        try:
            client = self._ensure_client()
            account = client.get_account()
            return {"connected": True, "account": str(getattr(account, "id", ""))}
        except Exception as exc:
            return {"connected": False, "error": str(exc)}

    def import_trades(self, days: int = 365) -> list[NormalizedTrade]:
        client = self._ensure_client()
        after = datetime.now() - timedelta(days=days)
        try:
            from alpaca.trading.requests import GetOrdersRequest
            from alpaca.trading.enums import QueryOrderStatus

            request = GetOrdersRequest(status=QueryOrderStatus.FILLED, after=after)
            orders = client.get_orders(filter=request)
        except ImportError as exc:
            raise RuntimeError("alpaca-py is not installed") from exc
        return self.normalize_orders(orders)

    @staticmethod
    def normalize_orders(orders: list[Any]) -> list[NormalizedTrade]:
        trades: list[NormalizedTrade] = []
        for index, order in enumerate(orders):
            symbol = _get(order, "symbol")
            price = _get(order, "filled_avg_price") or _get(order, "limit_price")
            if not symbol or price in (None, ""):
                continue
            side = str(_get(order, "side") or "buy").lower()
            filled_at = _parse_datetime(_get(order, "filled_at")) or datetime.now()
            trades.append(
                NormalizedTrade(
                    trade_id=str(_get(order, "id") or f"alpaca-{index + 1}"),
                    broker="alpaca",
                    ticker=str(symbol).upper(),
                    direction="short" if side in {"sell", "short"} else "long",
                    entry_price=float(price),
                    size=float(_get(order, "filled_qty") or _get(order, "qty") or 0.0),
                    entry_time=filled_at,
                    asset_type=str(_get(order, "asset_class") or "equity"),
                )
            )
        return trades


def _get(source: Any, name: str) -> Any:
    if isinstance(source, dict):
        return source.get(name)
    return getattr(source, name, None)


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None
