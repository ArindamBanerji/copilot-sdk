from __future__ import annotations

import builtins

from app.connectors.alpaca_connector import AlpacaConnector
from app.connectors.csv_connector import CSVConnector
from app.connectors.yfinance_provider import YFinanceProvider
from app.routers import data_import


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


def test_delimiter_auto_detect_tab():
    trades = CSVConnector().import_from_string(
        "ticker\tdirection\tentry_price\tsize\tentry_time\n"
        "MSFT\tbuy\t100\t2\t2026-01-01\n"
    )

    assert len(trades) == 1
    assert trades[0].ticker == "MSFT"
    assert trades[0].size == 2.0


def test_delimiter_auto_detect_pipe():
    trades = CSVConnector().import_from_string(
        "ticker|direction|entry_price|size|entry_time\n"
        "SPY|sell|450|1|2026-01-01\n"
    )

    assert len(trades) == 1
    assert trades[0].ticker == "SPY"
    assert trades[0].direction == "short"


def test_delimiter_semicolon():
    trades = CSVConnector().import_from_string(
        "ticker;direction;entry_price;size;entry_time\n"
        "QQQ;buy;390;3;2026-01-01\n"
    )

    assert len(trades) == 1
    assert trades[0].ticker == "QQQ"
    assert trades[0].size == 3.0


def test_alpaca_preset():
    trades = CSVConnector().import_from_string(
        "id,symbol,side,qty,avg_entry_price,avg_exit_price,commission,filled_at\n"
        "a1,AAPL,buy,3,180.5,184.5,1.25,2026-01-01T09:30:00\n",
        broker_preset="alpaca",
    )

    assert len(trades) == 1
    assert trades[0].trade_id == "a1"
    assert trades[0].ticker == "AAPL"
    assert trades[0].entry_price == 180.5
    assert trades[0].exit_price == 184.5
    assert trades[0].fees == 1.25


def test_european_date_day_first():
    trades = CSVConnector().import_from_string(
        "ticker,direction,entry_price,size,entry_time\n"
        "MSFT,buy,100,1,15-03-2025\n"
    )

    assert trades[0].entry_time.year == 2025
    assert trades[0].entry_time.month == 3
    assert trades[0].entry_time.day == 15


def test_european_date_dot_separated():
    trades = CSVConnector().import_from_string(
        "ticker,direction,entry_price,size,entry_time\n"
        "MSFT,buy,100,1,15.03.2025\n"
    )

    assert trades[0].entry_time.year == 2025
    assert trades[0].entry_time.month == 3
    assert trades[0].entry_time.day == 15


def test_european_date_slash():
    trades = CSVConnector().import_from_string(
        "ticker,direction,entry_price,size,entry_time\n"
        "MSFT,buy,100,1,15/03/2025\n"
    )

    assert trades[0].entry_time.year == 2025
    assert trades[0].entry_time.month == 3
    assert trades[0].entry_time.day == 15


def test_flexible_csv_endpoint(client):
    data_import._trade_store_ref.clear()

    response = client.post(
        "/api/trading/import/csv",
        json={
            "preset": "thinkorswim",
            "csv_content": "Exec ID,Symbol,Side,Price,Qty,Exec Time\n1,AAPL,BOT,200,3,01/02/2026\n",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["imported"] == 1
    assert payload["trades"][0]["trade_id"] == "1"
    assert payload["trades"][0]["ticker"] == "AAPL"


def test_csv_unknown_preset_returns_400(client):
    data_import._trade_store_ref.clear()

    response = client.post(
        "/api/trading/import/csv",
        json={
            "preset": "thinkorswin",
            "csv_content": "Exec ID,Symbol,Side,Price,Qty,Exec Time\n1,AAPL,BOT,200,3,01/02/2026\n",
        },
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["error"] == "Unknown preset: thinkorswin"
    assert "thinkorswim" in payload["valid_presets"]


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
