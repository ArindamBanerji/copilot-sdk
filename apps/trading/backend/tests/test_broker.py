from __future__ import annotations

import sys
from pathlib import Path

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]

for path in (BACKEND_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.brokers import BrokerError, MockBroker, OrderRequest, OrderSide, get_broker  # noqa: E402
from app.brokers.alpaca import AlpacaBroker, PAPER_BASE_URL  # noqa: E402


def test_mock_market_order_fills_at_100():
    broker = MockBroker()

    order = broker.place_order(OrderRequest(ticker="aapl", side=OrderSide.BUY, qty=10))

    assert order.ticker == "AAPL"
    assert order.filled_qty == 10
    assert order.avg_fill_price == 100.0
    assert order.status.value == "filled"


def test_mock_limit_order_fills_at_limit_price():
    broker = MockBroker()

    order = broker.place_order(
        OrderRequest(ticker="MSFT", side=OrderSide.BUY, qty=2, order_type="limit", limit_price=150.25)
    )

    assert order.avg_fill_price == 150.25


def test_mock_buy_weighted_average_position():
    broker = MockBroker()

    broker.place_order(OrderRequest(ticker="AAPL", side=OrderSide.BUY, qty=1, order_type="limit", limit_price=100))
    broker.place_order(OrderRequest(ticker="AAPL", side=OrderSide.BUY, qty=3, order_type="limit", limit_price=200))

    position = broker.get_positions()[0]
    assert position.qty == 4
    assert position.avg_entry_price == 175.0


def test_mock_sell_reduces_and_removes_position():
    broker = MockBroker()

    broker.place_order(OrderRequest(ticker="AAPL", side=OrderSide.BUY, qty=5))
    broker.place_order(OrderRequest(ticker="AAPL", side=OrderSide.SELL, qty=2))
    assert broker.get_positions()[0].qty == 3

    broker.place_order(OrderRequest(ticker="AAPL", side=OrderSide.SELL, qty=3))
    assert broker.get_positions() == []


def test_mock_get_order_and_filter_orders():
    broker = MockBroker()
    first = broker.place_order(OrderRequest(ticker="AAPL", side=OrderSide.BUY, qty=1))
    broker.place_order(OrderRequest(ticker="MSFT", side=OrderSide.BUY, qty=1))

    assert broker.get_order(first.order_id) == first
    assert all(order.status.value == "filled" for order in broker.get_orders(status="filled"))


def test_mock_account_returns_core_fields():
    broker = MockBroker()
    broker.place_order(OrderRequest(ticker="AAPL", side=OrderSide.BUY, qty=1))

    account = broker.get_account()

    assert set(account) == {"cash", "equity", "buying_power"}
    assert account["equity"] == 100000.0


def test_mock_invalid_qty_raises():
    broker = MockBroker()

    with pytest.raises(BrokerError):
        broker.place_order(OrderRequest(ticker="AAPL", side=OrderSide.BUY, qty=0))


def test_mock_oversell_raises():
    broker = MockBroker()

    with pytest.raises(BrokerError):
        broker.place_order(OrderRequest(ticker="AAPL", side=OrderSide.SELL, qty=1))


def test_alpaca_missing_key_raises(monkeypatch):
    monkeypatch.delenv("APCA_API_KEY_ID", raising=False)
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")

    with pytest.raises(EnvironmentError):
        AlpacaBroker()


def test_alpaca_missing_secret_raises(monkeypatch):
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.delenv("APCA_API_SECRET_KEY", raising=False)

    with pytest.raises(EnvironmentError):
        AlpacaBroker()


def test_alpaca_default_base_url_without_network(monkeypatch):
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.delenv("APCA_API_BASE_URL", raising=False)

    broker = AlpacaBroker(client=object())  # type: ignore[arg-type]

    assert broker.base_url == PAPER_BASE_URL


def test_alpaca_uses_env_base_url_without_network(monkeypatch):
    monkeypatch.setenv("APCA_API_KEY_ID", "key")
    monkeypatch.setenv("APCA_API_SECRET_KEY", "secret")
    monkeypatch.setenv("APCA_API_BASE_URL", "https://broker.invalid")

    broker = AlpacaBroker(client=object())  # type: ignore[arg-type]

    assert broker.base_url == "https://broker.invalid"


def test_get_broker_mock_returns_mock_broker():
    assert isinstance(get_broker("mock"), MockBroker)


def test_get_broker_unknown_raises():
    with pytest.raises(ValueError):
        get_broker("unknown")
