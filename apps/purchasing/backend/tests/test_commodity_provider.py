from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from apps.purchasing.backend.app.connectors.commodity_provider import CommodityDataProvider


class LiveCommoditySource:
    provenance_tier = "scraped_external"

    def __init__(self) -> None:
        self.enabled = True
        self.calls = 0

    def fetch_category_prices(self, category: str) -> list[dict] | None:
        self.calls += 1
        if not self.enabled:
            return None
        return [
            {"date": "2026-06", "item": category, "price": 10.0, "unit": "per lb"}
        ]


class FailCommoditySource:
    provenance_tier = "scraped_external"

    def __init__(self) -> None:
        self.calls = 0

    def fetch_category_prices(self, category: str) -> list[dict] | None:
        self.calls += 1
        return None


class SlowCountingCommoditySource:
    provenance_tier = "scraped_external"

    def __init__(self) -> None:
        self.calls = 0
        self._lock = threading.Lock()

    def fetch_category_prices(self, category: str) -> list[dict] | None:
        with self._lock:
            self.calls += 1
        time.sleep(0.5)
        return [
            {"date": "2026-06", "item": category, "price": 10.0, "unit": "per lb"}
        ]


def test_live_returns_scraped_external():
    provider = CommodityDataProvider(source=LiveCommoditySource())

    result = provider.get_commodity_prices("protein")

    assert result["provenance"] == "scraped_external"
    assert result["source"] == "live"
    assert result["prices"]


def test_cache_returns_cached():
    source = LiveCommoditySource()
    provider = CommodityDataProvider(source=source)

    provider.get_commodity_prices("protein")
    source.enabled = False
    result = provider.get_commodity_prices("protein")

    assert result["provenance"] == "scraped_external"
    assert result["source"] == "live"
    assert result["cache_age_hours"] >= 0
    assert source.calls == 1


def test_fixture_returns_sample():
    source = FailCommoditySource()
    provider = CommodityDataProvider(source=source)

    result = provider.get_commodity_prices("protein")

    assert result["provenance"] == "sample"
    assert result["source"] == "fixture"
    assert result["prices"]
    assert source.calls == 1


def test_fixture_fallback_is_cached():
    source = FailCommoditySource()
    provider = CommodityDataProvider(source=source)

    first = provider.get_commodity_prices("protein")
    second = provider.get_commodity_prices("protein")

    assert first["provenance"] == "sample"
    assert second["provenance"] == "sample"
    assert source.calls == 1


def test_cache_ttl_expires():
    source = LiveCommoditySource()
    provider = CommodityDataProvider(source=source, cache_ttl_hours=0)

    provider.get_commodity_prices("protein")
    source.enabled = False
    result = provider.get_commodity_prices("protein")

    assert result["provenance"] == "scraped_external_cached"
    assert result["source"] == "live_cached"


def test_fixture_has_expected_shape():
    provider = CommodityDataProvider(source=FailCommoditySource())

    result = provider.get_commodity_prices("dairy")

    assert result["category"] == "dairy"
    assert isinstance(result["prices"], list)
    assert {"date", "item", "price", "unit"}.issubset(result["prices"][0])


def test_provider_wired_in_main():
    src = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")

    assert "connectors.commodity_provider import CommodityDataProvider" in src


def test_provenance_cascade_order():
    source = LiveCommoditySource()
    provider = CommodityDataProvider(source=source)

    live = provider.get_commodity_prices("produce")
    source.enabled = False
    fresh_cached = provider.get_commodity_prices("produce")
    provider._cache_time["produce"] = time.time() - (25 * 3600)
    stale_cached = provider.get_commodity_prices("produce")
    provider.refresh("produce")
    fixture = provider.get_commodity_prices("produce")

    assert live["provenance"] == "scraped_external"
    assert fresh_cached["provenance"] == "scraped_external"
    assert stale_cached["provenance"] == "scraped_external_cached"
    assert fixture["provenance"] == "sample"


def test_commodity_cache_first():
    source = LiveCommoditySource()
    provider = CommodityDataProvider(source=source)

    first = provider.get_commodity_prices("protein")
    calls_after_first = source.calls
    second = provider.get_commodity_prices("protein")

    assert calls_after_first == 1
    assert source.calls == calls_after_first
    assert first["prices"] == second["prices"]
    assert second["provenance"] == "scraped_external"


def test_commodity_single_flight():
    source = SlowCountingCommoditySource()
    provider = CommodityDataProvider(source=source)

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(
            executor.map(
                lambda _: provider.get_commodity_prices("protein"),
                range(4),
            )
        )

    assert source.calls == 1
    assert all(result["prices"] == results[0]["prices"] for result in results)
    assert all(result["provenance"] == "scraped_external" for result in results)


def test_commodity_stale_fallback():
    source = LiveCommoditySource()
    provider = CommodityDataProvider(source=source, cache_ttl_hours=0)

    live = provider.get_commodity_prices("protein")
    source.enabled = False
    stale = provider.get_commodity_prices("protein")

    assert live["prices"] == stale["prices"]
    assert stale["provenance"] == "scraped_external_cached"
    assert stale["source"] == "live_cached"


def test_stale_fallback_refreshes_cache_time():
    source = LiveCommoditySource()
    provider = CommodityDataProvider(source=source)

    provider.get_commodity_prices("protein")
    source.enabled = False
    old_time = time.time() - (25 * 3600)
    provider._cache_time["protein"] = old_time

    stale = provider.get_commodity_prices("protein")

    assert stale["provenance"] == "scraped_external_cached"
    assert provider._cache_time["protein"] > old_time
