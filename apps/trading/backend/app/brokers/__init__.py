"""Broker execution adapters for the Trading CLI."""

from __future__ import annotations

from .alpaca import AlpacaBroker
from .mock import MockBroker
from .protocol import BrokerError, BrokerProtocol, OrderRequest, OrderResult, OrderSide, OrderStatus, Position


def get_broker(broker_name: str = "alpaca") -> BrokerProtocol:
    name = broker_name.lower().strip()
    if name == "mock":
        return MockBroker()
    if name == "alpaca":
        return AlpacaBroker()
    raise ValueError(f"Unsupported broker: {broker_name}")


__all__ = [
    "AlpacaBroker",
    "BrokerError",
    "BrokerProtocol",
    "MockBroker",
    "OrderRequest",
    "OrderResult",
    "OrderSide",
    "OrderStatus",
    "Position",
    "get_broker",
]
