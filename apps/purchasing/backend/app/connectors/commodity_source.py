"""Commodity price source implementations for Purchasing."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Protocol
from urllib.parse import urlencode
from urllib.request import urlopen


class CommoditySource(Protocol):
    """Real commodity price source. FRED API or equivalent."""

    provenance_tier: str

    def fetch_category_prices(self, category: str) -> list[dict] | None:
        """Fetch recent commodity prices for a food category."""
        ...

    def fetch_price_index(self, category: str) -> float | None:
        """Current price index for category versus 12-month average."""
        ...


class FREDCommoditySource:
    """FRED API source for food commodity prices.

    FRED series IDs per Purchasing category:
      protein: APU0000FF1101 (ground beef avg price)
      produce: APU0000712311 (lettuce avg price)
      dairy: APU0000DA1110 (whole milk avg price)
      dry_goods: APU0000FA1101 (flour avg price)
      beverages: APU0000FJ4101 (coffee avg price)
    """

    provenance_tier = "scraped_external"

    def __init__(self, api_key: str = ""):
        self._api_key = api_key
        self._base_url = "https://api.stlouisfed.org/fred"
        self._series_map = {
            "protein": "APU0000FF1101",
            "produce": "APU0000712311",
            "dairy": "APU0000DA1110",
            "dry_goods": "APU0000FA1101",
            "beverages": "APU0000FJ4101",
        }
        self._item_map = {
            "protein": "Ground Beef",
            "produce": "Lettuce",
            "dairy": "Whole Milk",
            "dry_goods": "Flour",
            "beverages": "Coffee",
        }

    def fetch_category_prices(self, category: str) -> list[dict] | None:
        """GET /fred/series/observations and return last 12 monthly observations."""
        frozen = self._frozen_prices(category)
        if frozen is not None:
            return frozen
        if not self._api_key:
            return None
        series_id = self._series_map.get(category)
        if not series_id:
            return None
        params = urlencode(
            {
                "series_id": series_id,
                "api_key": self._api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 12,
            }
        )
        try:
            with urlopen(f"{self._base_url}/series/observations?{params}", timeout=3) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return None

        rows: list[dict] = []
        for observation in reversed(payload.get("observations", [])):
            value = observation.get("value")
            if value in (None, "."):
                continue
            try:
                price = round(float(value), 2)
            except (TypeError, ValueError):
                continue
            rows.append(
                {
                    "date": str(observation.get("date", ""))[:7],
                    "item": self._item_map.get(category, category),
                    "price": price,
                    "unit": self._unit_for(category),
                }
            )
        return rows or None

    def fetch_price_index(self, category: str) -> float | None:
        """Current price divided by the available 12-month average."""
        rows = self.fetch_category_prices(category)
        if not rows:
            return None
        prices = [float(row["price"]) for row in rows if row.get("price") is not None]
        if not prices:
            return None
        avg = sum(prices) / len(prices)
        return round(prices[-1] / avg, 3) if avg else None

    def _unit_for(self, category: str) -> str:
        return "per lb" if category in {"protein", "produce", "dry_goods"} else "per unit"

    def _frozen_prices(self, category: str) -> list[dict] | None:
        freeze_path = os.environ.get("FRED_FREEZE", "").strip()
        if not freeze_path:
            return None
        try:
            payload = json.loads(Path(freeze_path).read_text(encoding="utf-8"))
        except Exception:
            return None
        rows = payload.get(category)
        if not isinstance(rows, list):
            return None
        return [dict(row) for row in rows if isinstance(row, dict)]
