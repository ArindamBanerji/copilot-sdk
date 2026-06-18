from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]

for path in (BACKEND_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.brokers import BrokerError, MockBroker, OrderRequest, OrderSide, get_broker  # noqa: E402
from app.brokers.alpaca import AlpacaBroker, PAPER_BASE_URL  # noqa: E402
from app.connectors import ibkr_connector  # noqa: E402
from app.connectors.ibkr_connector import IBKRConnector  # noqa: E402
from app.models.trade import NormalizedTrade  # noqa: E402
from app.routers import data_import  # noqa: E402


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


def test_ibkr_factory_wiring(monkeypatch):
    class FakeIB:
        pass

    monkeypatch.setattr(ibkr_connector, "IB_AVAILABLE", True)
    monkeypatch.setattr(ibkr_connector, "IB", FakeIB)

    assert isinstance(get_broker("ibkr"), IBKRConnector)


def test_ibkr_historical_mock():
    rows = IBKRConnector.mock_historical("SPY")

    assert len(rows) == 60
    assert {"date", "open", "high", "low", "close", "volume"} <= set(rows[0])


def test_ibkr_options_normalization():
    execution = SimpleNamespace(
        execId="opt-1",
        side="BOT",
        price=2.5,
        shares=1,
        time=datetime(2026, 1, 1, 9, 30).isoformat(),
    )
    contract = SimpleNamespace(
        symbol="AAPL",
        secType="OPT",
        strike=200,
        lastTradeDateOrContractMonth="20260320",
        right="C",
    )

    trade, _executed_at = IBKRConnector._fill_to_trade(
        SimpleNamespace(execution=execution, contract=contract, commissionReport=None),
        0,
    )

    assert trade is not None
    assert trade.asset_type == "option"
    assert trade.strike == 200.0
    assert trade.expiry == "20260320"
    assert trade.option_type == "call"


def test_ibkr_import_endpoint(client, monkeypatch):
    data_import._trade_store_ref.clear()

    class FakeConnector:
        def import_trades(self, days=365):
            return [
                NormalizedTrade(
                    trade_id="ibkr-1",
                    broker="ibkr",
                    ticker="MSFT",
                    direction="long",
                    entry_price=100,
                    size=2,
                    entry_time=datetime(2026, 1, 1, 9, 30),
                )
            ]

    monkeypatch.setattr(data_import, "get_broker", lambda _name: FakeConnector())

    response = client.post("/api/trading/import/broker", json={"broker": "ibkr", "days": 30})

    assert response.status_code == 200
    payload = response.json()
    assert payload["imported"] == 1
    assert payload["skipped"] == 0
    assert payload["errors"] == 0
    assert payload["trades"][0]["ticker"] == "MSFT"


def test_ibkr_import_connection_refused_returns_400(client, monkeypatch):
    data_import._trade_store_ref.clear()

    class FakeConnector:
        def import_trades(self, days=365):
            raise ConnectionError("Failed to connect to IBKR TWS/Gateway")

    monkeypatch.setattr(data_import, "get_broker", lambda _name: FakeConnector())

    response = client.post("/api/trading/import/broker", json={"broker": "ibkr"})

    assert response.status_code == 400
    assert "Failed to connect to IBKR TWS/Gateway" in response.json()["detail"]


def test_ibkr_import_dedup(client, monkeypatch):
    data_import._trade_store_ref.clear()

    class FakeConnector:
        def import_trades(self, days=365):
            return [
                NormalizedTrade(
                    trade_id="ibkr-1",
                    broker="ibkr",
                    ticker="MSFT",
                    direction="long",
                    entry_price=100,
                    size=2,
                    entry_time=datetime(2026, 1, 1, 9, 30),
                )
            ]

    monkeypatch.setattr(data_import, "get_broker", lambda _name: FakeConnector())

    first = client.post("/api/trading/import/broker", json={"broker": "ibkr"})
    second = client.post("/api/trading/import/broker", json={"broker": "ibkr"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["imported"] == 1
    assert second.json()["imported"] == 0
    assert second.json()["skipped"] == 1


def test_broker_import_dedup_different_direction(client, monkeypatch):
    data_import._trade_store_ref.clear()

    class FakeConnector:
        def import_trades(self, days=365):
            return [
                NormalizedTrade(
                    trade_id="ibkr-long",
                    broker="ibkr",
                    ticker="MSFT",
                    direction="long",
                    entry_price=100,
                    size=2,
                    entry_time=datetime(2026, 1, 1, 9, 30),
                ),
                NormalizedTrade(
                    trade_id="ibkr-short",
                    broker="ibkr",
                    ticker="MSFT",
                    direction="short",
                    entry_price=100,
                    size=2,
                    entry_time=datetime(2026, 1, 1, 10, 30),
                ),
            ]

    monkeypatch.setattr(data_import, "get_broker", lambda _name: FakeConnector())

    response = client.post("/api/trading/import/broker", json={"broker": "ibkr"})

    assert response.status_code == 200
    assert response.json()["imported"] == 2
    assert response.json()["skipped"] == 0


def test_broker_import_invalid_days_returns_400(client):
    data_import._trade_store_ref.clear()

    response = client.post("/api/trading/import/broker", json={"broker": "ibkr", "days": "abc"})

    assert response.status_code == 400
    assert response.json()["error"] == "Invalid days parameter"


def test_ibkr_futures_normalization():
    execution = SimpleNamespace(
        execId="fut-1",
        side="BOT",
        price=5000,
        shares=1,
        time=datetime(2026, 1, 1, 9, 30).isoformat(),
    )
    contract = SimpleNamespace(
        symbol="ES",
        secType="FUT",
        lastTradeDateOrContractMonth="202603",
        multiplier="50",
    )

    trade, _executed_at = IBKRConnector._fill_to_trade(
        SimpleNamespace(execution=execution, contract=contract, commissionReport=None),
        0,
    )

    assert trade is not None
    assert trade.asset_type == "future"
    assert trade.expiry == "202603"
    assert trade.multiplier == 50.0


def test_get_broker_unknown_raises():
    with pytest.raises(ValueError):
        get_broker("unknown")
