"""Broker execution protocol for Trading CLI commands."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class BrokerError(Exception):
    """Raised for broker configuration, validation, or execution failures."""


@dataclass(frozen=True)
class OrderRequest:
    ticker: str
    side: OrderSide
    qty: float
    order_type: str = "market"
    time_in_force: str = "day"
    limit_price: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OrderResult:
    order_id: str
    ticker: str
    side: OrderSide
    qty: float
    status: OrderStatus
    order_type: str = "market"
    limit_price: float | None = None
    filled_qty: float = 0.0
    avg_fill_price: float | None = None
    submitted_at: str | None = None
    filled_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Position:
    ticker: str
    qty: float
    avg_entry_price: float
    current_price: float
    unrealized_pnl: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class BrokerProtocol(Protocol):
    def place_order(self, request: OrderRequest) -> OrderResult: ...

    def get_order(self, order_id: str) -> OrderResult: ...

    def get_orders(self, status: str | None = None, limit: int = 50) -> list[OrderResult]: ...

    def get_positions(self) -> list[Position]: ...

    def get_account(self) -> dict[str, Any]: ...

    def cancel_order(self, order_id: str) -> bool: ...
