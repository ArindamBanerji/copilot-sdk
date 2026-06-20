"""Deterministic commodity price fixtures for Purchasing."""

from __future__ import annotations


class MockCommoditySource:
    """Deterministic fixture data for commodity prices. No API calls."""

    provenance_tier = "sample"

    MOCK_PRICES = {
        "protein": [
            {"date": "2025-07", "item": "Ground Beef", "price": 5.72, "unit": "per lb"},
            {"date": "2025-08", "item": "Ground Beef", "price": 5.76, "unit": "per lb"},
            {"date": "2025-09", "item": "Ground Beef", "price": 5.81, "unit": "per lb"},
            {"date": "2025-10", "item": "Ground Beef", "price": 5.9, "unit": "per lb"},
            {"date": "2025-11", "item": "Ground Beef", "price": 6.02, "unit": "per lb"},
            {"date": "2025-12", "item": "Ground Beef", "price": 6.08, "unit": "per lb"},
            {"date": "2026-01", "item": "Ground Beef", "price": 5.89, "unit": "per lb"},
            {"date": "2026-02", "item": "Ground Beef", "price": 5.95, "unit": "per lb"},
            {"date": "2026-03", "item": "Ground Beef", "price": 6.01, "unit": "per lb"},
            {"date": "2026-04", "item": "Ground Beef", "price": 6.07, "unit": "per lb"},
            {"date": "2026-05", "item": "Ground Beef", "price": 6.12, "unit": "per lb"},
            {"date": "2026-06", "item": "Ground Beef", "price": 6.18, "unit": "per lb"},
        ],
        "produce": [
            {"date": "2025-07", "item": "Lettuce", "price": 1.62, "unit": "per head"},
            {"date": "2025-08", "item": "Lettuce", "price": 1.58, "unit": "per head"},
            {"date": "2025-09", "item": "Lettuce", "price": 1.61, "unit": "per head"},
            {"date": "2025-10", "item": "Lettuce", "price": 1.68, "unit": "per head"},
            {"date": "2025-11", "item": "Lettuce", "price": 1.74, "unit": "per head"},
            {"date": "2025-12", "item": "Lettuce", "price": 1.79, "unit": "per head"},
            {"date": "2026-01", "item": "Lettuce", "price": 1.72, "unit": "per head"},
            {"date": "2026-02", "item": "Lettuce", "price": 1.69, "unit": "per head"},
            {"date": "2026-03", "item": "Lettuce", "price": 1.65, "unit": "per head"},
            {"date": "2026-04", "item": "Lettuce", "price": 1.63, "unit": "per head"},
            {"date": "2026-05", "item": "Lettuce", "price": 1.67, "unit": "per head"},
            {"date": "2026-06", "item": "Lettuce", "price": 1.71, "unit": "per head"},
        ],
        "dairy": [
            {"date": "2025-07", "item": "Whole Milk", "price": 4.12, "unit": "per gal"},
            {"date": "2025-08", "item": "Whole Milk", "price": 4.1, "unit": "per gal"},
            {"date": "2025-09", "item": "Whole Milk", "price": 4.16, "unit": "per gal"},
            {"date": "2025-10", "item": "Whole Milk", "price": 4.2, "unit": "per gal"},
            {"date": "2025-11", "item": "Whole Milk", "price": 4.23, "unit": "per gal"},
            {"date": "2025-12", "item": "Whole Milk", "price": 4.26, "unit": "per gal"},
            {"date": "2026-01", "item": "Whole Milk", "price": 4.18, "unit": "per gal"},
            {"date": "2026-02", "item": "Whole Milk", "price": 4.14, "unit": "per gal"},
            {"date": "2026-03", "item": "Whole Milk", "price": 4.19, "unit": "per gal"},
            {"date": "2026-04", "item": "Whole Milk", "price": 4.21, "unit": "per gal"},
            {"date": "2026-05", "item": "Whole Milk", "price": 4.28, "unit": "per gal"},
            {"date": "2026-06", "item": "Whole Milk", "price": 4.31, "unit": "per gal"},
        ],
        "dry_goods": [
            {"date": "2025-07", "item": "Flour", "price": 0.55, "unit": "per lb"},
            {"date": "2025-08", "item": "Flour", "price": 0.56, "unit": "per lb"},
            {"date": "2025-09", "item": "Flour", "price": 0.55, "unit": "per lb"},
            {"date": "2025-10", "item": "Flour", "price": 0.57, "unit": "per lb"},
            {"date": "2025-11", "item": "Flour", "price": 0.58, "unit": "per lb"},
            {"date": "2025-12", "item": "Flour", "price": 0.59, "unit": "per lb"},
            {"date": "2026-01", "item": "Flour", "price": 0.57, "unit": "per lb"},
            {"date": "2026-02", "item": "Flour", "price": 0.58, "unit": "per lb"},
            {"date": "2026-03", "item": "Flour", "price": 0.6, "unit": "per lb"},
            {"date": "2026-04", "item": "Flour", "price": 0.61, "unit": "per lb"},
            {"date": "2026-05", "item": "Flour", "price": 0.6, "unit": "per lb"},
            {"date": "2026-06", "item": "Flour", "price": 0.62, "unit": "per lb"},
        ],
        "beverages": [
            {"date": "2025-07", "item": "Coffee", "price": 5.04, "unit": "per lb"},
            {"date": "2025-08", "item": "Coffee", "price": 5.12, "unit": "per lb"},
            {"date": "2025-09", "item": "Coffee", "price": 5.18, "unit": "per lb"},
            {"date": "2025-10", "item": "Coffee", "price": 5.23, "unit": "per lb"},
            {"date": "2025-11", "item": "Coffee", "price": 5.31, "unit": "per lb"},
            {"date": "2025-12", "item": "Coffee", "price": 5.38, "unit": "per lb"},
            {"date": "2026-01", "item": "Coffee", "price": 5.28, "unit": "per lb"},
            {"date": "2026-02", "item": "Coffee", "price": 5.33, "unit": "per lb"},
            {"date": "2026-03", "item": "Coffee", "price": 5.4, "unit": "per lb"},
            {"date": "2026-04", "item": "Coffee", "price": 5.47, "unit": "per lb"},
            {"date": "2026-05", "item": "Coffee", "price": 5.53, "unit": "per lb"},
            {"date": "2026-06", "item": "Coffee", "price": 5.59, "unit": "per lb"},
        ],
    }

    def __init__(self, fixture_data: dict[str, list[dict]] | None = None):
        self._data = fixture_data or self.MOCK_PRICES

    def fetch_category_prices(self, category: str) -> list[dict] | None:
        rows = self._data.get(category)
        return [dict(row) for row in rows] if rows else None

    def fetch_price_index(self, category: str) -> float | None:
        prices = self._data.get(category)
        if not prices:
            return None
        current = float(prices[-1]["price"])
        avg = sum(float(row["price"]) for row in prices) / len(prices)
        return round(current / avg, 3) if avg else None
