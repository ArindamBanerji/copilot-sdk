"""Deterministic in-memory broker for CLI tests and local dry runs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .protocol import BrokerError, BrokerProtocol, OrderRequest, OrderResult, OrderSide, OrderStatus, Position


class MockBroker(BrokerProtocol):
    def __init__(self, *, cash: float = 100_000.0):
        self.cash = float(cash)
        self._orders: list[OrderResult] = []
        self._positions: dict[str, Position] = {}
        self._next_id = 1

    def place_order(self, request: OrderRequest) -> OrderResult:
        ticker = request.ticker.upper()
        qty = float(request.qty)
        if qty <= 0:
            raise BrokerError("Order quantity must be positive.")
        if request.order_type == "limit" and request.limit_price is None:
            raise BrokerError("Limit orders require --limit-price.")

        fill_price = float(request.limit_price) if request.limit_price is not None else 100.0
        now = datetime.now(timezone.utc).isoformat()
        order = OrderResult(
            order_id=f"mock-{self._next_id}",
            ticker=ticker,
            side=request.side,
            qty=qty,
            status=OrderStatus.FILLED,
            order_type=request.order_type,
            limit_price=request.limit_price,
            filled_qty=qty,
            avg_fill_price=fill_price,
            submitted_at=now,
            filled_at=now,
            metadata=dict(request.metadata),
        )
        self._next_id += 1
        self._apply_fill(order)
        self._orders.append(order)
        return order

    def get_order(self, order_id: str) -> OrderResult:
        for order in self._orders:
            if order.order_id == order_id:
                return order
        raise BrokerError(f"Order not found: {order_id}")

    def get_orders(self, status: str | None = None, limit: int = 50) -> list[OrderResult]:
        wanted = (status or "all").lower()
        orders = list(reversed(self._orders))
        if wanted not in {"all", ""}:
            orders = [order for order in orders if order.status.value == wanted]
        return orders[: max(int(limit), 0)]

    def get_positions(self) -> list[Position]:
        return [self._positions[ticker] for ticker in sorted(self._positions)]

    def get_account(self) -> dict[str, Any]:
        position_value = sum(position.qty * position.current_price for position in self._positions.values())
        equity = self.cash + position_value
        return {
            "cash": round(self.cash, 2),
            "equity": round(equity, 2),
            "buying_power": round(self.cash, 2),
        }

    def cancel_order(self, order_id: str) -> bool:
        for order in self._orders:
            if order.order_id == order_id and order.status == OrderStatus.PENDING:
                cancelled = OrderResult(
                    **{**order.__dict__, "status": OrderStatus.CANCELLED}
                )
                self._orders[self._orders.index(order)] = cancelled
                return True
        return False

    def _apply_fill(self, order: OrderResult) -> None:
        price = float(order.avg_fill_price or 0.0)
        qty = float(order.filled_qty or order.qty)
        ticker = order.ticker.upper()
        existing = self._positions.get(ticker)
        if order.side == OrderSide.BUY:
            self.cash -= qty * price
            if existing is None:
                self._positions[ticker] = Position(ticker, qty, price, price, 0.0)
                return
            total_qty = existing.qty + qty
            avg = ((existing.qty * existing.avg_entry_price) + (qty * price)) / total_qty
            self._positions[ticker] = Position(ticker, total_qty, avg, avg, 0.0)
            return

        if existing is None or existing.qty < qty:
            raise BrokerError(f"Insufficient position to sell {qty:g} {ticker}.")
        self.cash += qty * price
        remaining = existing.qty - qty
        if remaining <= 0:
            self._positions.pop(ticker, None)
        else:
            self._positions[ticker] = Position(ticker, remaining, existing.avg_entry_price, existing.avg_entry_price, 0.0)
