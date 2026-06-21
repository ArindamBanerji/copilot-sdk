from __future__ import annotations

import json
import time
from pathlib import Path

from apps.trading.backend.app.connectors.market_source import MockMarketSource
from apps.trading.backend.app.services.market_data_provider import (
    LIVE_TIMEOUT_SECONDS,
    MarketDataProvider,
)
from copilot_sdk.evidence.provenance import Provenanced


class FailSource:
    def fetch_ohlcv(self, *args, **kwargs):
        return None

    def fetch_vix(self):
        return None

    def fetch_info(self, *args):
        return None

    def fetch_batch_history(self, *args, **kwargs):
        return None


def test_source_returns_declared_provenance_tier():
    """When source returns data, result uses the source-declared provenance tier."""
    provider = MarketDataProvider(source=MockMarketSource())
    result = provider.get_vix_current()
    assert isinstance(result, Provenanced)
    assert result.source == "sample"
    assert result.value is not None
    assert result.as_of is not None


def test_failed_source_falls_to_fixture():
    """When source returns None, result is Provenanced(source='fixture')."""
    provider = MarketDataProvider(source=FailSource(), fixture_data={"vix_current": 20.0})
    result = provider.get_vix_current()
    assert result.source == "fixture"
    assert result.value == 20.0


def test_cached_after_live():
    """Second call returns cached before TTL expires."""
    provider = MarketDataProvider(source=MockMarketSource())
    first = provider.get_vix_current()
    assert first.source == "sample"
    second = provider.get_vix_current()
    assert second.source == "cached"
    assert second.value == first.value


def test_no_data_still_provenanced():
    """Even with no source and no fixture, returns Provenanced."""
    provider = MarketDataProvider(source=FailSource())
    result = provider.get_vix_current()
    assert isinstance(result, Provenanced)
    assert result.source == "fixture"
    assert result.label == "no data available"


def test_slow_source_times_out():
    """Source that takes 10s times out in less than 5s total."""

    class SlowSource(FailSource):
        def fetch_vix(self):
            time.sleep(10)
            return 20.0

    provider = MarketDataProvider(source=SlowSource(), fixture_data={"vix_current": 15.0})
    start = time.time()
    result = provider.get_vix_current()
    elapsed = time.time() - start
    assert elapsed < LIVE_TIMEOUT_SECONDS + 2
    assert result.source in ("cached", "fixture")


def test_backoff_prevents_immediate_retry():
    """After failure, live is not retried within backoff period."""
    call_count = 0

    class CountSource(FailSource):
        def fetch_vix(self):
            nonlocal call_count
            call_count += 1
            return None

    provider = MarketDataProvider(source=CountSource(), fixture_data={"vix_current": 16.0})
    provider.get_vix_current()
    provider.get_vix_current()
    assert call_count == 1


def test_refresh_clears_cache():
    """After refresh(), next call hits live source again."""
    provider = MarketDataProvider(source=MockMarketSource())
    first = provider.get_vix_current()
    assert first.source == "sample"
    second = provider.get_vix_current()
    assert second.source == "cached"
    refresh_result = provider.refresh()
    assert isinstance(refresh_result, Provenanced)
    third = provider.get_vix_current()
    assert third.source == "sample"


def test_market_snapshot_has_enriched_fields():
    """Snapshot includes RSI, above_50ma, volume_rank."""
    provider = MarketDataProvider(source=MockMarketSource())
    result = provider.get_market_snapshot()
    assert result.source == "sample"
    snap = result.value
    assert "spy" in snap
    assert "vix" in snap
    assert "rsi" in snap
    assert "above_50ma" in snap
    assert "volume_rank" in snap


def test_ticker_snapshot_has_enriched_fields():
    """Ticker snapshot includes RSI, vol_rank, sector."""
    provider = MarketDataProvider(source=MockMarketSource())
    result = provider.get_ticker_snapshot("SPY")
    assert result.source == "sample"
    snap = result.value
    assert snap["ticker"] == "SPY"
    assert "price" in snap
    assert "rsi" in snap
    assert "sector" in snap


def test_batch_returns():
    """Batch history returns data for multiple tickers."""
    provider = MarketDataProvider(source=MockMarketSource())
    result = provider.get_batch_returns(["SPY", "QQQ"], "2026-01-01", "2026-06-01")
    assert result.source == "sample"
    assert "SPY" in result.value
    assert "QQQ" in result.value


def test_vix_history_returns_date_keyed_dict():
    """VIX history returns {date: close} for vix_timing compatibility."""
    provider = MarketDataProvider(source=MockMarketSource())
    result = provider.get_vix_history("2026-01-01", "2026-06-01")
    assert result.source == "sample"
    assert isinstance(result.value, dict)
    for key, value in result.value.items():
        assert isinstance(key, str)
        assert isinstance(value, (int, float))


def test_every_public_method_returns_provenanced():
    """No public method can return a raw value."""
    provider = MarketDataProvider(source=MockMarketSource())
    methods = [
        provider.get_vix_current(),
        provider.get_ohlcv("SPY"),
        provider.get_market_snapshot(),
        provider.get_ticker_snapshot("SPY"),
        provider.get_batch_returns(["SPY"], "2026-01-01", "2026-06-01"),
        provider.get_vix_history("2026-01-01", "2026-06-01"),
        provider.refresh(),
    ]
    for result in methods:
        assert isinstance(result, Provenanced), f"Not Provenanced: {result}"


def test_ttl_returns_timedelta():
    """TTL is a positive timedelta."""
    provider = MarketDataProvider(source=MockMarketSource())
    ttl = provider._ttl_duration()
    assert ttl.total_seconds() > 0


def test_fixture_file_falls_back_with_as_of():
    """Frozen fixture can provide data with captured_at freshness."""
    path = Path(__file__).parent / "fixtures" / "frozen_market_snapshot.json"
    fixture_data = json.loads(path.read_text(encoding="utf-8"))
    provider = MarketDataProvider(source=FailSource(), fixture_data=fixture_data)
    result = provider.get_vix_current()
    assert result.source == "fixture"
    assert result.value == fixture_data["vix_current"]
    assert result.as_of == "2026-06-14T16:00:00Z"


def test_fixture_ohlcv_fallback():
    """Fixture data can satisfy OHLCV when live source fails."""
    fixture_data = MockMarketSource._defaults()
    provider = MarketDataProvider(source=FailSource(), fixture_data=fixture_data)
    result = provider.get_ohlcv("SPY")
    assert result.source == "fixture"
    assert isinstance(result.value, list)
    assert result.value[0]["date"].startswith("2026-06-")


def test_shared_market_provider_fixture(market_provider):
    """Shared fixture provides a MarketDataProvider with mock source."""
    result = market_provider.get_vix_current()
    assert isinstance(result, Provenanced)
    assert result.source == "sample"


def test_market_snapshot_field_names_match_frontend():
    """Snapshot has raw fields the context router maps for the frontend."""
    provider = MarketDataProvider(source=MockMarketSource())
    result = provider.get_market_snapshot()
    snap = result.value
    assert "spy" in snap
    assert "vix" in snap
    assert "rsi" in snap
    assert "above_50ma" in snap
    assert "volume_rank" in snap


def test_ticker_snapshot_field_names():
    """Ticker snapshot has expected fields."""
    provider = MarketDataProvider(source=MockMarketSource())
    result = provider.get_ticker_snapshot("SPY")
    snap = result.value
    assert snap["ticker"] == "SPY"
    assert "price" in snap
    assert snap["price"] is not None


def test_vix_history_used_by_vix_timing():
    """VIX history returns shape compatible with VIXTimingService."""
    provider = MarketDataProvider(source=MockMarketSource())
    result = provider.get_vix_history("2026-01-01", "2026-06-01")
    if result.value is not None:
        assert isinstance(result.value, dict)
        for key, value in result.value.items():
            assert isinstance(key, str), f"Key not str: {key}"
            assert isinstance(value, (int, float)), f"Value not numeric: {value}"


def test_ohlcv_returns_list_of_dicts():
    """OHLCV returns list of dicts with expected fields."""
    provider = MarketDataProvider(source=MockMarketSource())
    result = provider.get_ohlcv("SPY")
    assert result.source == "sample"
    assert isinstance(result.value, list)
    for row in result.value:
        assert "date" in row
        assert "close" in row
        assert "volume" in row


def test_provenanced_source_never_none():
    """Source field is always a string, never None."""
    provider = MarketDataProvider(source=MockMarketSource())
    for method_call in [
        provider.get_vix_current(),
        provider.get_ohlcv("SPY"),
        provider.get_market_snapshot(),
        provider.get_ticker_snapshot("SPY"),
    ]:
        assert isinstance(method_call.source, str)
        assert method_call.source in ("scraped_external", "sample", "cached", "fixture")


def test_f25_no_mock_labeled_live():
    provider = MarketDataProvider(source=MockMarketSource())

    result = provider.get_vix_current()

    assert result.source != "live"
    assert result.source == "sample"


def test_provenanced_as_of_iso_format():
    """as_of field is ISO format when present."""
    provider = MarketDataProvider(source=MockMarketSource())
    result = provider.get_vix_current()
    if result.as_of:
        from datetime import datetime

        datetime.fromisoformat(result.as_of.replace("Z", "+00:00"))


def test_concurrent_calls_safe():
    """Multiple calls don't corrupt cache."""
    import threading

    provider = MarketDataProvider(source=MockMarketSource())
    results = []

    def call():
        result = provider.get_vix_current()
        results.append(result)

    threads = [threading.Thread(target=call) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(results) == 10
    assert all(isinstance(result, Provenanced) for result in results)
