"""Deterministic Toast POS test double for Purchasing."""

from __future__ import annotations


class DemoToastConnector:
    """Test double for ToastConnector. Returns fixture data.

    Same 5-member SourceConnector protocol. No network calls.
    Follows FakeConnector pattern from tests/test_di_profiler.py.
    """

    source_name = "toast_pos_mock"
    entity_type = "restaurant_sales"
    trust_tier = 2

    def __init__(self, fixture_data: dict[str, list[dict]] | None = None) -> None:
        self._data = fixture_data or self._default_fixtures()

    def fetch(self, entity_id: str) -> list[dict]:
        """Return fixture data for entity_id; missing date returns empty."""
        return list(self._data.get(entity_id, []))

    def validate(self, record: dict) -> bool:
        """Validate a Toast POS fixture record."""
        required = ("timestamp", "total_orders", "covers", "total_revenue")
        if not all(key in record for key in required):
            return False

        if not isinstance(record.get("total_orders"), int) or record["total_orders"] < 0:
            return False
        if not isinstance(record.get("covers"), int) or record["covers"] < 0:
            return False

        try:
            if float(record["total_revenue"]) < 0:
                return False
        except (TypeError, ValueError):
            return False
        return True

    @staticmethod
    def _default_fixtures() -> dict[str, list[dict]]:
        """Return seven days of deterministic restaurant sales data."""
        import random

        random.seed(42)
        base_ts = 1718000000.0
        fixtures: dict[str, list[dict]] = {}

        menu_items = [
            ("Grilled Salmon", "protein", 28.00),
            ("Chicken Parmesan", "protein", 22.00),
            ("Caesar Salad", "produce", 14.00),
            ("Seasonal Soup", "produce", 12.00),
            ("Mac and Cheese", "dairy", 16.00),
            ("Cheesecake", "dairy", 10.00),
            ("Pasta Primavera", "dry_goods", 18.00),
            ("Bread Basket", "dry_goods", 6.00),
            ("House Red Wine", "beverages", 12.00),
            ("Craft Beer", "beverages", 8.00),
            ("Espresso", "beverages", 5.00),
            ("Ribeye Steak", "protein", 42.00),
            ("Shrimp Tacos", "protein", 18.00),
            ("Garden Salad", "produce", 11.00),
            ("Tiramisu", "dairy", 12.00),
        ]

        for day_offset in range(7):
            date = f"2024-06-{10 + day_offset:02d}"
            covers = random.randint(80, 150)
            lunch_pct = random.uniform(0.35, 0.45)
            dinner_pct = random.uniform(0.45, 0.55)

            items = []
            total_revenue = 0.0
            total_orders = 0
            for name, category, price in menu_items:
                quantity = random.randint(3, max(4, covers // 5))
                revenue = round(quantity * price, 2)
                items.append(
                    {
                        "item_name": name,
                        "quantity_sold": quantity,
                        "revenue": revenue,
                        "category": category,
                    }
                )
                total_revenue += revenue
                total_orders += quantity

            lunch = int(covers * lunch_pct)
            dinner = int(covers * dinner_pct)
            fixtures[date] = [
                {
                    "timestamp": base_ts + day_offset * 86400,
                    "date": date,
                    "total_orders": total_orders,
                    "total_revenue": round(total_revenue, 2),
                    "covers": covers,
                    "items": items,
                    "dayparts": {
                        "lunch": lunch,
                        "dinner": dinner,
                        "late_night": covers - lunch - dinner,
                    },
                }
            ]

        return fixtures


MockToastConnector = DemoToastConnector
