from __future__ import annotations

import sys
from types import ModuleType

from apps.trading.backend.app.connectors.market_source import MockMarketSource, YFinanceSource


def test_mock_source_fetch_ohlcv_returns_list():
    """MockMarketSource.fetch_ohlcv returns list of OHLCV dicts."""
    source = MockMarketSource()
    data = source.fetch_ohlcv("SPY")
    assert isinstance(data, list)
    assert len(data) > 0
    assert "close" in data[0]
    assert "volume" in data[0]
    assert "date" in data[0]


def test_yfinance_provenance_tier():
    assert YFinanceSource().provenance_tier == "scraped_external"


def test_mock_provenance_tier():
    assert MockMarketSource().provenance_tier == "sample"


def test_mock_source_fetch_vix_returns_float():
    """MockMarketSource.fetch_vix returns a float."""
    source = MockMarketSource()
    vix = source.fetch_vix()
    assert isinstance(vix, float)
    assert 10 <= vix <= 40


def test_mock_source_fetch_info_returns_dict():
    """MockMarketSource.fetch_info returns ticker metadata."""
    source = MockMarketSource()
    info = source.fetch_info("SPY")
    assert isinstance(info, dict)
    assert "shortName" in info
    assert "sector" in info
    assert "marketCap" in info
    assert info["marketCap"] > 0


def test_mock_source_fetch_batch_history():
    """MockMarketSource.fetch_batch_history returns {ticker: [records]}."""
    source = MockMarketSource()
    data = source.fetch_batch_history(["SPY", "QQQ"], "2026-01-01", "2026-06-01")
    assert isinstance(data, dict)
    assert "SPY" in data
    assert "QQQ" in data
    assert len(data["SPY"]) > 0


def test_mock_source_unknown_ticker_returns_none():
    """Unknown ticker returns None from ohlcv."""
    source = MockMarketSource()
    data = source.fetch_ohlcv("UNKNOWN_TICKER_XYZ")
    assert data is None


def test_mock_source_info_unknown_ticker():
    """Unknown ticker returns None from info."""
    source = MockMarketSource()
    info = source.fetch_info("UNKNOWN_TICKER_XYZ")
    assert info is None


def test_yfinance_source_graceful_without_network(monkeypatch):
    """YFinanceSource returns None when yfinance fails, without network."""

    class _FailingTicker:
        def __init__(self, *_args, **_kwargs):
            raise RuntimeError("simulated yfinance failure")

    fake_yfinance = ModuleType("yfinance")
    fake_yfinance.Ticker = _FailingTicker
    monkeypatch.setitem(sys.modules, "yfinance", fake_yfinance)

    result = YFinanceSource().fetch_vix()

    assert result is None


def test_mock_source_ohlcv_prices_realistic():
    """SPY prices are in realistic range."""
    source = MockMarketSource()
    data = source.fetch_ohlcv("SPY")
    for row in data:
        assert 400 <= row["close"] <= 700, f"Unrealistic SPY: {row['close']}"
        assert row["volume"] > 0


def test_mock_source_vix_prices_realistic():
    """VIX values in realistic range."""
    source = MockMarketSource()
    data = source.fetch_ohlcv("^VIX")
    for row in data:
        assert 8 <= row["close"] <= 50, f"Unrealistic VIX: {row['close']}"


def test_mock_source_deterministic():
    """Two calls return identical data."""
    first = MockMarketSource()
    second = MockMarketSource()
    assert first.fetch_ohlcv("SPY") == second.fetch_ohlcv("SPY")
    assert first.fetch_vix() == second.fetch_vix()
