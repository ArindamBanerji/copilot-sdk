"""Commodity data provider with live -> cached -> fixture provenance cascade."""

from __future__ import annotations

import time
from typing import Any

from app.connectors.mock_commodity import MockCommoditySource
from copilot_sdk.evidence.provenance import Provenanced

COMMODITY_CATEGORIES = ("protein", "produce", "dairy", "dry_goods", "beverages")


class CommodityDataProvider:
    """Real commodity prices with cache cascade.

    Cascade:
      live -> cached -> fixture

    Provenance:
      live: scraped_external
      cached: scraped_external_cached
      fixture: sample
    """

    def __init__(
        self,
        source: Any | None = None,
        fixture_data: dict[str, Any] | None = None,
        cache_ttl_hours: int = 24,
    ) -> None:
        self._source = source or MockCommoditySource()
        self._live_source = source
        self._fixture = fixture_data or MockCommoditySource.MOCK_PRICES
        self._cache: dict[str, Any] = {}
        self._cache_time: dict[str, float] = {}
        self._ttl = max(float(cache_ttl_hours), 0.0) * 3600.0

    def get_commodity_prices(self, category: str = "all") -> dict[str, Any]:
        """Return commodity price rows with explicit provenance labels."""
        live = self._fetch_live(category)
        if live:
            self._cache[category] = live
            self._cache_time[category] = time.time()
            return {
                **live,
                "provenance": "scraped_external",
                "source": _source_name(self._source),
            }

        cached = self._cached(category)
        if cached is not None:
            age_hours = (time.time() - self._cache_time[category]) / 3600.0
            return {
                **cached,
                "provenance": "scraped_external_cached",
                "source": f"{_source_name(self._source)}_cached",
                "cache_age_hours": age_hours,
            }

        return self._load_fixture(category)

    def get_category_prices(self, category: str) -> Provenanced[list[dict] | None]:
        """Router-compatible commodity prices for one food category."""
        payload = self.get_commodity_prices(category)
        return Provenanced(
            value=payload.get("prices"),
            source=str(payload.get("provenance")),
            label=str(payload.get("source")),
            as_of=payload.get("as_of"),
        )

    def get_price_index(self, category: str) -> Provenanced[float | None]:
        payload = self._get_price_index_payload(category)
        return Provenanced(
            value=payload.get("index"),
            source=str(payload.get("provenance")),
            label=str(payload.get("source")),
            as_of=payload.get("as_of"),
        )

    def get_all_indices(self) -> Provenanced[dict[str, float] | None]:
        values: dict[str, float] = {}
        provenance = "sample"
        source = "fixture"
        for category in COMMODITY_CATEGORIES:
            payload = self._get_price_index_payload(category)
            index = payload.get("index")
            if index is not None:
                values[category] = float(index)
            if payload.get("provenance") == "scraped_external":
                provenance = "scraped_external"
                source = str(payload.get("source"))
            elif (
                payload.get("provenance") == "scraped_external_cached"
                and provenance == "sample"
            ):
                provenance = "scraped_external_cached"
                source = str(payload.get("source"))
        return Provenanced(value=values or None, source=provenance, label=source)

    def refresh(self, category: str | None = None) -> Provenanced[bool]:
        if category:
            self._cache.pop(category, None)
            self._cache_time.pop(category, None)
        else:
            self._cache.clear()
            self._cache_time.clear()
        return Provenanced(value=True, source="local", label="cache refreshed")

    def _get_price_index_payload(self, category: str) -> dict[str, Any]:
        payload = self.get_commodity_prices(category)
        prices = [
            float(row["price"])
            for row in payload.get("prices", [])
            if isinstance(row, dict) and row.get("price") is not None
        ]
        index = None
        if prices:
            avg = sum(prices) / len(prices)
            index = round(prices[-1] / avg, 3) if avg else None
        return {
            "index": index,
            "category": category,
            "provenance": payload.get("provenance"),
            "source": payload.get("source"),
            "as_of": payload.get("as_of"),
        }

    def _fetch_live(self, category: str) -> dict[str, Any] | None:
        if self._live_source is None:
            return None
        if category == "all":
            prices = []
            for item in COMMODITY_CATEGORIES:
                rows = self._live_source.fetch_category_prices(item)
                if rows:
                    prices.extend(dict(row, category=item) for row in rows)
            return {"prices": prices, "category": category} if prices else None
        rows = self._live_source.fetch_category_prices(category)
        if not rows:
            return None
        return {"prices": [dict(row) for row in rows], "category": category}

    def _cached(self, category: str) -> dict[str, Any] | None:
        if category not in self._cache:
            return None
        if self._ttl <= 0:
            return None
        age = time.time() - self._cache_time.get(category, 0.0)
        if age >= self._ttl:
            return None
        return dict(self._cache[category])

    def _load_fixture(self, category: str) -> dict[str, Any]:
        if category == "all":
            prices = []
            for item in COMMODITY_CATEGORIES:
                prices.extend(dict(row, category=item) for row in self._fixture.get(item, []))
        else:
            prices = [dict(row) for row in self._fixture.get(category, [])]
        return {
            "prices": prices,
            "provenance": "sample",
            "source": "fixture",
            "category": category,
        }


def _source_name(source: Any | None) -> str:
    if source is None:
        return "commodity_live"
    name = type(source).__name__.replace("CommoditySource", "").lower()
    return name or "commodity_live"
