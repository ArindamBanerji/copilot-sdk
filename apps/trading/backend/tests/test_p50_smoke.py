from __future__ import annotations

from app import context_router
from app.routers import correlation as correlation_router
from app.routers import data_import
from app.routers import regime as regime_router
from app.routers import vix_timing as vix_timing_router
from apps.trading.backend.app.connectors.market_source import MockMarketSource
from apps.trading.backend.app.services.market_data_provider import MarketDataProvider
from copilot_sdk.evidence.provenance import Provenanced


def _provider() -> MarketDataProvider:
    return MarketDataProvider(source=MockMarketSource())


def _seed_trade_store() -> None:
    data_import._trade_store_ref.clear()
    data_import._trade_store_ref.extend(
        [
            {
                "trade_id": "p50-smoke-1",
                "ticker": "SPY",
                "category": "trend_following",
                "entry_time": "2026-06-10T09:30:00",
                "exit_time": "2026-06-10T15:30:00",
                "pnl": 100.0,
                "metadata": {},
            },
            {
                "trade_id": "p50-smoke-2",
                "ticker": "QQQ",
                "category": "trend_following",
                "entry_time": "2026-06-11T09:30:00",
                "exit_time": "2026-06-12T15:30:00",
                "pnl": -25.0,
                "metadata": {},
            },
        ]
    )


def test_smoke_market_snapshot_returns_provenance(client, monkeypatch):
    """GET /api/context/market-snapshot has provenance in response."""
    monkeypatch.setattr(context_router, "_provider", _provider())

    response = client.get("/api/context/market-snapshot")

    assert response.status_code == 200
    payload = response.json()
    assert "provenance" in payload
    assert payload["provenance"]["source"] in {"scraped_external", "sample", "cached", "fixture"}
    assert "as_of" in payload["provenance"]


def test_smoke_market_snapshot_spy_field(client, monkeypatch):
    """GET /api/context/market-snapshot has spy with price."""
    monkeypatch.setattr(context_router, "_provider", _provider())

    response = client.get("/api/context/market-snapshot")

    assert response.status_code == 200
    spy = response.json()["spy"]
    assert "price" in spy
    assert "change30dPct" in spy
    assert isinstance(spy["price"], (int, float))


def test_smoke_ticker_returns_provenance(client, monkeypatch):
    """GET /api/context/ticker/SPY has provenance in response."""
    monkeypatch.setattr(context_router, "_provider", _provider())

    response = client.get("/api/context/ticker/SPY")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "SPY"
    assert payload["provenance"]["source"] in {"scraped_external", "sample", "cached", "fixture"}


def test_smoke_ticker_camelcase_fields(client, monkeypatch):
    """GET /api/context/ticker/SPY has camelCase field names."""
    monkeypatch.setattr(context_router, "_provider", _provider())

    response = client.get("/api/context/ticker/SPY")

    assert response.status_code == 200
    payload = response.json()
    for field in ("change30dPct", "marketCapB", "above50ma", "volRankPctl"):
        assert field in payload


def test_smoke_regime_still_works(client, monkeypatch):
    """GET /api/trading/regime returns regime data."""
    monkeypatch.setattr(regime_router, "_provider", _provider())

    response = client.get("/api/trading/regime")

    assert response.status_code == 200
    payload = response.json()
    assert "current" in payload
    assert "regime" in payload["current"]


def test_smoke_correlation_still_works(client, monkeypatch):
    """GET /api/trading/correlation returns correlation data."""
    _seed_trade_store()
    monkeypatch.setattr(correlation_router, "_provider", _provider())

    response = client.get("/api/trading/correlation")

    assert response.status_code == 200
    payload = response.json()
    assert "tickers" in payload
    assert "matrix" in payload
    assert payload["source"] in {"yfinance", "insufficient_data"}


def test_smoke_vix_timing_still_works(client, monkeypatch):
    """GET /api/trading/vix-timing returns timing data."""
    _seed_trade_store()
    monkeypatch.setattr(vix_timing_router, "_provider", _provider())

    response = client.get("/api/trading/vix-timing")

    assert response.status_code == 200
    payload = response.json()
    assert "matrix" in payload
    assert "total_analyzed" in payload
    assert "total_skipped" in payload


def test_smoke_market_ohlcv_still_works(client, monkeypatch):
    """GET /api/trading/market/ohlcv?ticker=SPY returns rows."""
    monkeypatch.setattr(data_import, "_provider", _provider())

    response = client.get("/api/trading/market/ohlcv?ticker=SPY")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "SPY"
    assert isinstance(payload["rows"], list)
    assert payload["count"] == len(payload["rows"])


def test_smoke_market_vix_still_works(client, monkeypatch):
    """GET /api/trading/market/vix returns VIX data."""
    monkeypatch.setattr(data_import, "_provider", _provider())

    response = client.get("/api/trading/market/vix")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "^VIX"
    assert isinstance(payload["rows"], list)
    assert payload["count"] == len(payload["rows"])


def test_smoke_refresh_returns_provenance(client, monkeypatch):
    """POST /api/trading/market/refresh returns refreshed + provenance."""
    monkeypatch.setattr(data_import, "_provider", _provider())

    response = client.post("/api/trading/market/refresh")

    assert response.status_code == 200
    payload = response.json()
    assert payload["refreshed"] is True
    assert payload["provenance"]["source"] in {"scraped_external", "sample", "cached", "fixture", "local"}


def test_smoke_all_sources_labeled():
    """Every public MarketDataProvider method returns labeled Provenanced values."""
    provider = MarketDataProvider(source=MockMarketSource())
    methods = [
        ("get_vix_current", []),
        ("get_ohlcv", ["SPY"]),
        ("get_market_snapshot", []),
        ("get_ticker_snapshot", ["SPY"]),
        ("get_batch_returns", [["SPY"], "2026-01-01", "2026-06-01"]),
        ("get_vix_history", ["2026-01-01", "2026-06-01"]),
    ]
    for name, args in methods:
        result = getattr(provider, name)(*args)
        assert isinstance(result, Provenanced), f"{name} not Provenanced"
        assert result.source in ("scraped_external", "sample", "cached", "fixture"), f"{name} source={result.source}"
