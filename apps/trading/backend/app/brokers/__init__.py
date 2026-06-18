"""Broker execution adapters for the Trading CLI."""

from __future__ import annotations

from typing import Any

from .alpaca import AlpacaBroker
from .mock import MockBroker
from .protocol import BrokerError, BrokerProtocol, OrderRequest, OrderResult, OrderSide, OrderStatus, Position


def get_broker(broker_name: str = "alpaca", **kwargs: Any) -> BrokerProtocol:
    name = broker_name.lower().strip()
    if name == "mock":
        return MockBroker()
    if name == "alpaca":
        return AlpacaBroker()
    if name == "ibkr":
        from app.connectors.ibkr_connector import IBKRConnector

        return IBKRConnector(
            host=kwargs.get("host", "127.0.0.1"),
            port=kwargs.get("port", 7497),
            client_id=kwargs.get("client_id", 10),
        )  # type: ignore[return-value]
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
