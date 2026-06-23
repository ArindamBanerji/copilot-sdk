from __future__ import annotations

import time

from apps.purchasing.backend.app.connectors.commodity_provider import CommodityDataProvider


class LiveCommoditySource:
    provenance_tier = "scraped_external"

    def __init__(self) -> None:
        self.enabled = True

    def fetch_category_prices(self, category: str) -> list[dict] | None:
        if not self.enabled:
            return None
        return [
            {"date": "2026-06", "item": category, "price": 10.0, "unit": "per lb"}
        ]


class FailCommoditySource:
    provenance_tier = "scraped_external"

    def fetch_category_prices(self, category: str) -> list[dict] | None:
        return None


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

    assert result["provenance"] == "scraped_external_cached"
    assert result["source"] == "live_cached"
    assert result["cache_age_hours"] >= 0


def test_fixture_returns_sample():
    provider = CommodityDataProvider(source=FailCommoditySource())

    result = provider.get_commodity_prices("protein")

    assert result["provenance"] == "sample"
    assert result["source"] == "fixture"
    assert result["prices"]


def test_cache_ttl_expires():
    source = LiveCommoditySource()
    provider = CommodityDataProvider(source=source, cache_ttl_hours=0)

    provider.get_commodity_prices("protein")
    source.enabled = False
    result = provider.get_commodity_prices("protein")

    assert result["provenance"] == "sample"
    assert result["source"] == "fixture"


def test_fixture_has_expected_shape():
    provider = CommodityDataProvider(source=FailCommoditySource())

    result = provider.get_commodity_prices("dairy")

    assert result["category"] == "dairy"
    assert isinstance(result["prices"], list)
    assert {"date", "item", "price", "unit"}.issubset(result["prices"][0])


def test_provider_wired_in_main():
    src = open("apps/purchasing/backend/app/main.py", encoding="utf-8").read()

    assert "connectors.commodity_provider import CommodityDataProvider" in src


def test_provenance_cascade_order():
    source = LiveCommoditySource()
    provider = CommodityDataProvider(source=source)

    live = provider.get_commodity_prices("produce")
    source.enabled = False
    cached = provider.get_commodity_prices("produce")
    provider._cache_time["produce"] = time.time() - (25 * 3600)
    fixture = provider.get_commodity_prices("produce")

    assert live["provenance"] == "scraped_external"
    assert cached["provenance"] == "scraped_external_cached"
    assert fixture["provenance"] == "sample"
