"""Alpaca broker execution adapter using httpx directly."""

from __future__ import annotations

import os
from typing import Any

import httpx

from .protocol import BrokerError, BrokerProtocol, OrderRequest, OrderResult, OrderSide, OrderStatus, Position


PAPER_BASE_URL = "https://paper-api.alpaca.markets"


class AlpacaBroker(BrokerProtocol):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        secret_key: str | None = None,
        base_url: str | None = None,
        client: httpx.Client | None = None,
    ):
        self.api_key = api_key or os.getenv("APCA_API_KEY_ID")
        self.secret_key = secret_key or os.getenv("APCA_API_SECRET_KEY")
        if not self.api_key or not self.secret_key:
            raise EnvironmentError("Alpaca credentials are not configured. Set APCA_API_KEY_ID and APCA_API_SECRET_KEY.")
        self.base_url = (base_url or os.getenv("APCA_API_BASE_URL") or PAPER_BASE_URL).rstrip("/")
        self._client = client or httpx.Client(
            base_url=self.base_url,
            headers={
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key,
                "Content-Type": "application/json",
            },
            timeout=10.0,
        )

    def place_order(self, request: OrderRequest) -> OrderResult:
        payload: dict[str, Any] = {
            "symbol": request.ticker.upper(),
            "side": request.side.value,
            "qty": str(request.qty),
            "type": request.order_type,
            "time_in_force": request.time_in_force,
        }
        if request.limit_price is not None:
            payload["limit_price"] = str(request.limit_price)
        data = self._request("POST", "/v2/orders", json=payload)
        return _order_from_alpaca(data)

    def get_order(self, order_id: str) -> OrderResult:
        return _order_from_alpaca(self._request("GET", f"/v2/orders/{order_id}"))

    def get_orders(self, status: str | None = None, limit: int = 50) -> list[OrderResult]:
        params = {"status": status or "all", "limit": max(int(limit), 1), "nested": "false"}
        data = self._request("GET", "/v2/orders", params=params)
        if not isinstance(data, list):
            raise BrokerError("Alpaca returned an unexpected orders response.")
        return [_order_from_alpaca(item) for item in data]

    def get_positions(self) -> list[Position]:
        data = self._request("GET", "/v2/positions")
        if not isinstance(data, list):
            raise BrokerError("Alpaca returned an unexpected positions response.")
        return [_position_from_alpaca(item) for item in data]

    def get_account(self) -> dict[str, Any]:
        data = self._request("GET", "/v2/account")
        if not isinstance(data, dict):
            raise BrokerError("Alpaca returned an unexpected account response.")
        return {
            "cash": _float(data.get("cash")),
            "equity": _float(data.get("equity")),
            "buying_power": _float(data.get("buying_power")),
            "status": data.get("status"),
            "currency": data.get("currency"),
        }

    def cancel_order(self, order_id: str) -> bool:
        self._request("DELETE", f"/v2/orders/{order_id}", allow_empty=True)
        return True

    def _request(self, method: str, path: str, *, allow_empty: bool = False, **kwargs: Any) -> Any:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.TimeoutException as exc:
            raise BrokerError("Broker request timed out.") from exc
        except httpx.HTTPError as exc:
            raise BrokerError("Broker request failed. Check network connectivity and broker status.") from exc

        if 200 <= response.status_code < 300:
            if allow_empty or not response.content:
                return {}
            return response.json()

        message = _safe_error_message(response)
        if response.status_code == 403:
            raise BrokerError(f"Alpaca rejected the request as forbidden: {message}")
        if response.status_code == 422:
            raise BrokerError(f"Alpaca rejected the order as invalid: {message}")
        raise BrokerError(f"Alpaca request failed with HTTP {response.status_code}: {message}")


def _order_from_alpaca(data: dict[str, Any]) -> OrderResult:
    side = OrderSide.SELL if str(data.get("side") or "").lower() == "sell" else OrderSide.BUY
    return OrderResult(
        order_id=str(data.get("id") or ""),
        ticker=str(data.get("symbol") or "").upper(),
        side=side,
        qty=_float(data.get("qty")),
        status=_status(str(data.get("status") or "")),
        order_type=str(data.get("type") or "market"),
        limit_price=_optional_float(data.get("limit_price")),
        filled_qty=_float(data.get("filled_qty")),
        avg_fill_price=_optional_float(data.get("filled_avg_price") or data.get("limit_price")),
        submitted_at=_string_or_none(data.get("submitted_at") or data.get("created_at")),
        filled_at=_string_or_none(data.get("filled_at")),
        metadata={"raw_status": data.get("status"), "asset_class": data.get("asset_class")},
    )


def _position_from_alpaca(data: dict[str, Any]) -> Position:
    return Position(
        ticker=str(data.get("symbol") or "").upper(),
        qty=_float(data.get("qty")),
        avg_entry_price=_float(data.get("avg_entry_price")),
        current_price=_float(data.get("current_price")),
        unrealized_pnl=_float(data.get("unrealized_pl")),
        metadata={"asset_class": data.get("asset_class")},
    )


def _status(value: str) -> OrderStatus:
    normalized = value.lower()
    if normalized == "filled":
        return OrderStatus.FILLED
    if normalized in {"partially_filled", "partial"}:
        return OrderStatus.PARTIAL
    if normalized in {"canceled", "cancelled", "expired"}:
        return OrderStatus.CANCELLED
    if normalized in {"rejected", "stopped", "suspended"}:
        return OrderStatus.REJECTED
    return OrderStatus.PENDING


def _float(value: Any) -> float:
    parsed = _optional_float(value)
    return 0.0 if parsed is None else parsed


def _optional_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _string_or_none(value: Any) -> str | None:
    return None if value in (None, "") else str(value)


def _safe_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text[:200] or "no response body"
    if isinstance(payload, dict):
        for key in ("message", "error", "code"):
            if payload.get(key):
                return str(payload[key])[:200]
    return "broker rejected the request"
