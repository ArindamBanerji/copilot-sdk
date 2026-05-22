from __future__ import annotations

import builtins

from app.connectors.alpaca_connector import AlpacaConnector
from app.connectors.csv_connector import CSVConnector
from app.connectors.yfinance_provider import YFinanceProvider


def test_basic_csv_import():
    trades = CSVConnector().import_from_string(
        "ticker,direction,entry_price,size,entry_time\n"
        "msft,buy,100,3,2026-01-01\n"
    )

    assert len(trades) == 1
    assert trades[0].ticker == "MSFT"
    assert trades[0].direction == "long"
    assert trades[0].entry_price == 100.0


def test_sell_becomes_short():
    trades = CSVConnector().import_from_string(
        "ticker,side,price,qty,date\n"
        "SPY,sell,450,2,2026-01-01\n"
    )

    assert trades[0].direction == "short"


def test_column_alias_detection():
    trades = CSVConnector().import_from_string(
        "symbol,action,fill_price,quantity,timestamp\n"
        "NVDA,buy,900,1,2026-01-01T09:30:00\n"
    )

    assert trades[0].ticker == "NVDA"
    assert trades[0].size == 1.0


def test_dollar_signs_stripped():
    trades = CSVConnector().import_from_string(
        "ticker,direction,entry_price,size,entry_time\n"
        "MSFT,buy,$412.50,2,2026-01-01\n"
    )

    assert trades[0].entry_price == 412.50


def test_empty_csv():
    assert CSVConnector().import_from_string("") == []


def test_missing_ticker_skipped():
    trades = CSVConnector().import_from_string(
        "ticker,direction,entry_price,size,entry_time\n"
        ",buy,100,1,2026-01-01\n"
        "SPY,buy,450,1,2026-01-02\n"
    )

    assert len(trades) == 1
    assert trades[0].ticker == "SPY"


def test_trade_ids_sequential():
    trades = CSVConnector().import_from_string(
        "ticker,direction,entry_price,size,entry_time\n"
        "SPY,buy,450,1,2026-01-01\n"
        "MSFT,buy,400,1,2026-01-02\n"
    )

    assert [trade.trade_id for trade in trades] == ["csv-1", "csv-2"]


def test_multiple_date_formats():
    trades = CSVConnector().import_from_string(
        "ticker,direction,entry_price,size,entry_time\n"
        "SPY,buy,450,1,01/02/2026\n"
        "MSFT,buy,400,1,2026/01/03\n"
    )

    assert trades[0].entry_time.year == 2026
    assert trades[1].entry_time.month == 1


def test_commas_in_numbers():
    trades = CSVConnector().import_from_string(
        'ticker,direction,entry_price,size,entry_time\n'
        'SPY,buy,"$1,234.50","1,000",2026-01-01\n'
    )

    assert trades[0].entry_price == 1234.50
    assert trades[0].size == 1000.0


def test_normalize_buy_order():
    trades = AlpacaConnector.normalize_orders(
        [
            {
                "id": "o-1",
                "symbol": "msft",
                "side": "buy",
                "filled_avg_price": "100",
                "filled_qty": "2",
                "filled_at": "2026-01-01T09:30:00Z",
            }
        ]
    )

    assert len(trades) == 1
    assert trades[0].broker == "alpaca"
    assert trades[0].ticker == "MSFT"
    assert trades[0].direction == "long"


def test_normalize_sell_order():
    trades = AlpacaConnector.normalize_orders(
        [
            {
                "id": "o-1",
                "symbol": "spy",
                "side": "sell",
                "filled_avg_price": "450",
                "qty": "1",
                "filled_at": "2026-01-01T09:30:00",
            }
        ]
    )

    assert trades[0].direction == "short"


def test_normalize_empty_list():
    assert AlpacaConnector.normalize_orders([]) == []


def test_connection_fails_without_credentials(monkeypatch):
    monkeypatch.delenv("APCA_API_KEY_ID", raising=False)
    monkeypatch.delenv("APCA_API_SECRET_KEY", raising=False)

    result = AlpacaConnector().test_connection()

    assert result["connected"] is False
    assert "credentials" in result["error"].lower()


def test_mock_ohlcv_shape():
    rows = YFinanceProvider.mock_ohlcv("spy", days=3)

    assert len(rows) == 3
    assert {"ticker", "date", "open", "high", "low", "close", "volume"} <= set(rows[0])


def test_mock_ohlcv_values_increase():
    rows = YFinanceProvider.mock_ohlcv("spy", days=3)

    assert [row["close"] for row in rows] == [100.0, 101.0, 102.0]


def test_provider_returns_empty_without_network_dependency(monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "yfinance":
            raise ImportError("missing yfinance")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    assert YFinanceProvider().get_ohlcv("SPY") == []
