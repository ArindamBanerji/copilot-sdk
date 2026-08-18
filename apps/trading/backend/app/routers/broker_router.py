"""Broker HTTP endpoints for the Trading backend."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
from math import isfinite
from typing import Any, Callable, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator, model_validator

from app.brokers import BrokerError, BrokerProtocol, OrderRequest, OrderSide, get_broker
from app.settings import settings
from copilot_sdk.scoring.mutation_lock import serialize_mutation


BrokerFactory = Callable[[str], BrokerProtocol]


class BrokerOrderRequest(BaseModel):
    ticker: str = Field(..., min_length=1)
    side: Literal["buy", "sell"]
    qty: float = Field(..., gt=0)
    order_type: Literal["market", "limit"] = "market"
    time_in_force: str = Field(default="day", min_length=1)
    limit_price: float | None = Field(default=None, gt=0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("ticker")
    def normalize_ticker(cls, value: str) -> str:
        ticker = str(value or "").strip().upper()
        if not ticker:
            raise ValueError("ticker is required")
        return ticker

    @field_validator("time_in_force")
    def normalize_time_in_force(cls, value: str) -> str:
        time_in_force = str(value or "").strip().lower()
        if not time_in_force:
            raise ValueError("time_in_force is required")
        return time_in_force

    @model_validator(mode="after")
    def validate_limit_order(self) -> "BrokerOrderRequest":
        if self.order_type == "limit" and self.limit_price is None:
            raise ValueError("limit_price is required for limit orders")
        return self


def _safe_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if isfinite(parsed) else None


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float):
        return value if isfinite(value) else None
    if value is None or isinstance(value, (str, int, bool)):
        return value
    return str(value)


def _broker_name(value: str | None) -> str:
    # Mirrors apps/trading/backend/cli.py _broker_name: default broker is Alpaca.
    return str(value or "alpaca").lower().strip()


def _safe_error(exc: BaseException) -> str:
    return str(exc)[:300] or exc.__class__.__name__


def _disconnected_payload(
    broker: str,
    *,
    field: str,
    empty_value: Any,
    error: str,
    status: str = "disconnected",
) -> dict[str, Any]:
    return {
        "broker": broker,
        "connected": False,
        "status": status,
        field: empty_value,
        "error": error,
    }


def _resolve_broker(broker: str, broker_factory: BrokerFactory) -> tuple[BrokerProtocol | None, str | None]:
    try:
        return broker_factory(broker), None
    except (BrokerError, EnvironmentError, ValueError) as exc:
        return None, _safe_error(exc)


def _broker_http_error(
    status_code: int,
    broker: str,
    *,
    status: str,
    error: str,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "broker": broker,
            "connected": False,
            "status": status,
            "order": None,
            "error": error,
        },
    )


def create_broker_router(broker_factory: BrokerFactory = get_broker) -> APIRouter:
    router = APIRouter()

    @router.get("/status")
    def broker_status(broker: str | None = None) -> dict[str, Any]:
        broker_name = _broker_name(broker)
        resolved, error = _resolve_broker(broker_name, broker_factory)
        if resolved is None:
            return {
                "broker": broker_name,
                "connected": False,
                "status": "disconnected",
                "error": error,
            }
        return {
            "broker": broker_name,
            "connected": True,
            "status": "connected",
            "connector": resolved.__class__.__name__,
        }

    @router.get("/account")
    def broker_account(broker: str | None = None) -> dict[str, Any]:
        broker_name = _broker_name(broker)
        resolved, error = _resolve_broker(broker_name, broker_factory)
        if resolved is None:
            return _disconnected_payload(broker_name, field="account", empty_value=None, error=error or "")
        try:
            account = resolved.get_account()
        except (BrokerError, EnvironmentError, ValueError) as exc:
            return _disconnected_payload(broker_name, field="account", empty_value=None, error=_safe_error(exc), status="error")
        return {
            "broker": broker_name,
            "connected": True,
            "status": "connected",
            "account": _json_safe(account),
        }

    @router.get("/positions")
    def broker_positions(broker: str | None = None) -> dict[str, Any]:
        broker_name = _broker_name(broker)
        resolved, error = _resolve_broker(broker_name, broker_factory)
        if resolved is None:
            return _disconnected_payload(broker_name, field="positions", empty_value=[], error=error or "")
        try:
            positions = resolved.get_positions()
        except (BrokerError, EnvironmentError, ValueError) as exc:
            return _disconnected_payload(broker_name, field="positions", empty_value=[], error=_safe_error(exc), status="error")
        safe_positions = _json_safe(positions)
        return {
            "broker": broker_name,
            "connected": True,
            "status": "connected",
            "positions": safe_positions,
            "count": len(safe_positions),
        }

    @router.get("/orders")
    def broker_orders(
        broker: str | None = None,
        status: str | None = None,
        limit: int = Query(default=50, ge=1, le=200),
    ) -> dict[str, Any]:
        broker_name = _broker_name(broker)
        resolved, error = _resolve_broker(broker_name, broker_factory)
        if resolved is None:
            return _disconnected_payload(broker_name, field="orders", empty_value=[], error=error or "")
        try:
            orders = resolved.get_orders(status=status, limit=limit)
        except (BrokerError, EnvironmentError, ValueError) as exc:
            return _disconnected_payload(broker_name, field="orders", empty_value=[], error=_safe_error(exc), status="error")
        safe_orders = _json_safe(orders)
        return {
            "broker": broker_name,
            "connected": True,
            "status": "connected",
            "orders": safe_orders,
            "count": len(safe_orders),
        }

    @router.post("/orders")
    @serialize_mutation("trading", event="market_data_refresh")
    def broker_place_order(request: BrokerOrderRequest, broker: str | None = None) -> dict[str, Any]:
        if not settings.TRADING_EXECUTION_ENABLED:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "observation_only",
                    "message": "Trading copilot operates in observation-only mode.",
                },
            )
        broker_name = _broker_name(broker)
        resolved, error = _resolve_broker(broker_name, broker_factory)
        if resolved is None:
            raise _broker_http_error(503, broker_name, status="disconnected", error=error or "")

        place_order = getattr(resolved, "place_order", None)
        if not callable(place_order):
            raise _broker_http_error(
                501,
                broker_name,
                status="unsupported",
                error="Broker connector does not support order placement.",
            )

        order_request = OrderRequest(
            ticker=request.ticker,
            side=OrderSide(request.side),
            qty=request.qty,
            order_type=request.order_type,
            time_in_force=request.time_in_force,
            limit_price=request.limit_price,
            metadata=dict(request.metadata),
        )
        try:
            order = place_order(order_request)
        except (BrokerError, EnvironmentError, ValueError) as exc:
            raise _broker_http_error(503, broker_name, status="error", error=_safe_error(exc)) from exc

        return {
            "broker": broker_name,
            "connected": True,
            "status": "submitted",
            "order": _json_safe(order),
        }

    @router.get("/orders/{order_id}")
    def broker_order(order_id: str, broker: str | None = None) -> dict[str, Any]:
        broker_name = _broker_name(broker)
        resolved, error = _resolve_broker(broker_name, broker_factory)
        if resolved is None:
            return _disconnected_payload(broker_name, field="order", empty_value=None, error=error or "")
        try:
            order = resolved.get_order(order_id)
        except (BrokerError, EnvironmentError, ValueError) as exc:
            return _disconnected_payload(broker_name, field="order", empty_value=None, error=_safe_error(exc), status="error")
        return {
            "broker": broker_name,
            "connected": True,
            "status": "connected",
            "order": _json_safe(order),
        }

    @router.post("/sync")
    @serialize_mutation("trading", event="market_data_refresh")
    def broker_sync(broker: str | None = None) -> dict[str, Any]:
        broker_name = _broker_name(broker)
        return {
            "broker": broker_name,
            "connected": False,
            "status": "unsupported",
            "sync": {"supported": False, "synced": 0},
            "error": "Broker sync is not exposed by the connector protocol.",
        }

    return router


router = create_broker_router()
