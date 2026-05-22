from __future__ import annotations

from app.connectors.yfinance_provider import YFinanceProvider
from app.routers import data_import


CSV_BODY = (
    "ticker,direction,entry_price,size,entry_time\n"
    "MSFT,buy,400,2,2026-01-01\n"
)


def test_list_trades_empty(client):
    data_import._trade_store_ref.clear()

    response = client.get("/api/trading/trades")

    assert response.status_code == 200
    assert response.json() == {"trades": [], "count": 0}


def test_import_csv(client):
    data_import._trade_store_ref.clear()

    response = client.post(
        "/api/trading/import/csv",
        content=CSV_BODY.encode("utf-8-sig"),
        headers={"content-type": "text/csv"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["imported"] == 1
    assert payload["trades"][0]["ticker"] == "MSFT"


def test_import_then_list(client):
    data_import._trade_store_ref.clear()
    client.post("/api/trading/import/csv", content=CSV_BODY, headers={"content-type": "text/csv"})

    response = client.get("/api/trading/trades")

    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_filter_by_ticker(client):
    data_import._trade_store_ref.clear()
    csv_body = (
        "ticker,direction,entry_price,size,entry_time\n"
        "MSFT,buy,400,2,2026-01-01\n"
        "SPY,buy,450,1,2026-01-01\n"
    )
    client.post("/api/trading/import/csv", content=csv_body, headers={"content-type": "text/csv"})

    response = client.get("/api/trading/trades?ticker=spy")

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["trades"][0]["ticker"] == "SPY"


def test_get_trade_by_id(client):
    data_import._trade_store_ref.clear()
    client.post("/api/trading/import/csv", content=CSV_BODY, headers={"content-type": "text/csv"})

    response = client.get("/api/trading/trades/csv-1")

    assert response.status_code == 200
    assert response.json()["trade_id"] == "csv-1"


def test_get_trade_not_found(client):
    data_import._trade_store_ref.clear()

    response = client.get("/api/trading/trades/missing")

    assert response.status_code == 404


def test_import_multiple_batches(client):
    data_import._trade_store_ref.clear()
    client.post("/api/trading/import/csv", content=CSV_BODY, headers={"content-type": "text/csv"})
    response = client.post(
        "/api/trading/import/csv",
        content=CSV_BODY.replace("MSFT", "SPY"),
        headers={"content-type": "text/csv"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_data_router_mounted(client):
    paths = {route.path for route in client.app.routes}

    assert "/api/trading/import/csv" in paths
    assert "/api/trading/trades" in paths
    assert "/api/trading/trades/{trade_id}" in paths


def test_ohlcv_endpoint_exists(client, monkeypatch):
    monkeypatch.setattr(YFinanceProvider, "get_ohlcv", lambda self, ticker, period="1mo", interval="1d": [])

    response = client.get("/api/trading/market/ohlcv?ticker=SPY")

    assert response.status_code == 200
    assert response.json() == {"ticker": "SPY", "rows": [], "count": 0}


def test_vix_endpoint_exists(client, monkeypatch):
    monkeypatch.setattr(YFinanceProvider, "get_vix", lambda self: [])

    response = client.get("/api/trading/market/vix")

    assert response.status_code == 200
    assert response.json() == {"ticker": "^VIX", "current": None, "rows": [], "count": 0}
