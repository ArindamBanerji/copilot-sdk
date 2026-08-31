"""Deterministic QuickBooks Online test double for Purchasing."""

from __future__ import annotations

from datetime import date, timedelta
from statistics import mean, median, pstdev
from typing import Any


class DemoQBOConnector:
    """Test double for QBOConnector. Returns fixture accounting data.

    Same 5-member SourceConnector protocol. No network calls.
    Fixture records use kitchen language: supplier, invoice, order,
    payment, amount.
    """

    source_name = "quickbooks_online_mock"
    entity_type = "accounting"
    trust_tier = 1

    def __init__(self, fixture_data: dict[str, list[dict]] | None = None) -> None:
        self._data = fixture_data or self._default_fixtures()

    def fetch(self, entity_id: str) -> list[dict]:
        """Return fixture records for entity_id."""
        if entity_id.startswith("price_history:"):
            _, supplier_id, item_name = entity_id.split(":", maxsplit=2)
            return self.compute_price_history(supplier_id, item_name)
        if entity_id.startswith("lead_times:"):
            _, supplier_id = entity_id.split(":", maxsplit=1)
            return [self.compute_lead_times(supplier_id)]
        return list(self._data.get(entity_id, []))

    def validate(self, record: dict) -> bool:
        """Validate normalized supplier or invoice fixture records."""
        if not isinstance(record, dict):
            return False
        record_type = str(record.get("record_type") or "")
        if record_type == "supplier":
            return bool(record.get("supplier_id") and record.get("supplier_name"))
        if record_type == "invoice":
            if not (record.get("supplier_id") and record.get("invoice_date") and record.get("amount") is not None):
                return False
            try:
                return float(record["amount"]) >= 0.0
            except (TypeError, ValueError):
                return False
        return bool(record.get("supplier_id") and record.get("supplier_name"))

    def fetch_vendors(self, max_results: int = 100) -> list[dict]:
        """Return normalized supplier profiles."""
        return list(self._data["vendors"][: int(max_results)])

    def fetch_bills(self, since_days: int = 365) -> list[dict]:
        """Return normalized invoice records."""
        return _filter_since(self._data["bills"], "invoice_date", since_days)

    def fetch_purchase_orders(self, since_days: int = 365) -> list[dict]:
        """Return normalized order records."""
        return _filter_since(self._data["purchase_orders"], "order_date", since_days)

    def fetch_payments(self, since_days: int = 365) -> list[dict]:
        """Return normalized payment records."""
        return _filter_since(self._data["payments"], "payment_date", since_days)

    def compute_price_history(self, vendor_id: str, item_name: str) -> list[dict]:
        """Return price history for supplier x item from invoices."""
        rows: list[dict] = []
        for invoice in self._data["bills"]:
            if str(invoice.get("supplier_id")) != str(vendor_id):
                continue
            for item in invoice.get("line_items", []):
                if str(item.get("item_name", "")).lower() != str(item_name).lower():
                    continue
                rows.append(
                    {
                        "date": invoice["invoice_date"],
                        "unit_price": item["unit_price"],
                        "quantity": item["quantity"],
                        "invoice_id": invoice["invoice_id"],
                    }
                )
        return sorted(rows, key=lambda row: row["date"])

    def compute_lead_times(self, vendor_id: str) -> dict:
        """Compute lead time stats from matched order/invoice records."""
        invoices = {
            str(row.get("order_id")): row
            for row in self._data["bills"]
            if str(row.get("supplier_id")) == str(vendor_id) and row.get("order_id")
        }
        lead_days: list[int] = []
        by_quarter: dict[str, list[int]] = {}
        for order in self._data["purchase_orders"]:
            if str(order.get("supplier_id")) != str(vendor_id):
                continue
            invoice = invoices.get(str(order.get("order_id")))
            if not invoice:
                continue
            days = (date.fromisoformat(invoice["invoice_date"]) - date.fromisoformat(order["order_date"])).days
            lead_days.append(days)
            by_quarter.setdefault(_quarter(invoice["invoice_date"]), []).append(days)
        return _lead_time_payload(lead_days, by_quarter)

    def test_connection(self) -> dict:
        """Mock connection status."""
        return {
            "connected": True,
            "company_name": "Demo Bistro Holdings",
            "realm_id": "mock-realm",
        }

    @staticmethod
    def _default_fixtures() -> dict[str, list[dict]]:
        """Return deterministic accounting fixtures."""
        vendors = _vendors()
        bills: list[dict] = []
        orders: list[dict] = []
        payments: list[dict] = []
        base_date = date(2025, 1, 3)

        for index in range(200):
            supplier = vendors[index % len(vendors)]
            invoice_date = base_date + timedelta(days=(index * 11) % 365)
            item_name, category, base_price = _item_for(supplier, index)
            unit_price = _price_for(supplier["archetype"], base_price, invoice_date.month, index)
            quantity = 5 + (index % 19)
            amount = round(unit_price * quantity, 2)
            order_id = f"ORD-{index + 1:04d}" if index < 150 else None
            invoice = {
                "record_type": "invoice",
                "invoice_id": f"INV-{index + 1:04d}",
                "supplier_id": supplier["supplier_id"],
                "supplier_name": supplier["supplier_name"],
                "archetype": supplier["archetype"],
                "invoice_date": invoice_date.isoformat(),
                "amount": amount,
                "currency": "USD",
                "order_id": order_id,
                "line_items": [
                    {
                        "item_name": item_name,
                        "category": category,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "amount": amount,
                    }
                ],
                "timestamp": invoice_date.isoformat(),
            }
            bills.append(invoice)

            if index < 150:
                lead_days = _lead_days_for(supplier["archetype"], index)
                order_date = invoice_date - timedelta(days=lead_days)
                orders.append(
                    {
                        "record_type": "order",
                        "order_id": order_id,
                        "supplier_id": supplier["supplier_id"],
                        "supplier_name": supplier["supplier_name"],
                        "order_date": order_date.isoformat(),
                        "expected_delivery_date": invoice_date.isoformat(),
                        "amount": amount,
                        "line_items": invoice["line_items"],
                        "timestamp": order_date.isoformat(),
                    }
                )

            if index < 50:
                payment_date = invoice_date + timedelta(days=7 + index % 10)
                payments.append(
                    {
                        "record_type": "payment",
                        "payment_id": f"PAY-{index + 1:04d}",
                        "supplier_id": supplier["supplier_id"],
                        "supplier_name": supplier["supplier_name"],
                        "invoice_id": invoice["invoice_id"],
                        "payment_date": payment_date.isoformat(),
                        "amount": amount,
                        "timestamp": payment_date.isoformat(),
                    }
                )

        return {
            "vendors": vendors,
            "bills": sorted(bills, key=lambda row: row["invoice_date"]),
            "purchase_orders": sorted(orders, key=lambda row: row["order_date"]),
            "payments": sorted(payments, key=lambda row: row["payment_date"]),
        }


def _vendors() -> list[dict]:
    archetypes = [
        ("gold_reliable", 5),
        ("seasonal_premium", 3),
        ("price_memory", 3),
        ("commodity_linked", 3),
        ("declining_quality", 3),
        ("new_unproven", 3),
        ("high_frequency_basic", 3),
        ("budget_volatile", 3),
        ("trust_trap", 2),
        ("format_changer", 2),
    ]
    names = [
        "Sysco Valley",
        "Harbor Prime",
        "FreshFields",
        "Dairy Direct",
        "Dry Pantry Co",
        "Coastal Premium",
        "Winter Seafood",
        "Peak Season Foods",
        "Memory Market",
        "Six Month Supply",
        "PriceTrack Produce",
        "Commodity Grain",
        "MarketLink Protein",
        "Index Beverage",
        "Quality Slide",
        "Late Crate",
        "Short Count Foods",
        "NuVend Supply",
        "Starter Produce",
        "Pilot Pantry",
        "Daily Dairy",
        "Basic Beverage",
        "Everyday Goods",
        "Budget Basket",
        "Value Fish",
        "Volatile Veg",
        "Trust First",
        "Spike Later",
        "Format Shift",
        "Invoice Remix",
    ]
    categories = ["protein", "produce", "dairy", "dry_goods", "beverages"]
    vendors: list[dict] = []
    offset = 0
    for archetype, count in archetypes:
        for local_index in range(count):
            idx = offset + local_index
            vendors.append(
                {
                    "record_type": "supplier",
                    "supplier_id": f"SUP-{idx + 1:03d}",
                    "supplier_name": names[idx],
                    "archetype": archetype,
                    "primary_category": categories[idx % len(categories)],
                    "active": True,
                    "balance": round(150.0 + idx * 37.5, 2),
                    "currency": "USD",
                    "timestamp": "2025-01-01",
                }
            )
        offset += count
    return vendors


def _item_for(supplier: dict, index: int) -> tuple[str, str, float]:
    category_items = {
        "protein": ("salmon filet", 18.0),
        "produce": ("romaine case", 24.0),
        "dairy": ("whole milk case", 16.0),
        "dry_goods": ("flour sack", 22.0),
        "beverages": ("cold brew keg", 38.0),
    }


    category = str(supplier["primary_category"])
    if supplier["archetype"] == "seasonal_premium":
        category = "protein"
        return "seafood case", category, 34.0
    item, price = category_items[category]
    return item, category, price


def _price_for(archetype: str, base_price: float, month: int, index: int) -> float:
    if archetype == "gold_reliable":
        multiplier = 1.0 + ((index % 5) - 2) * 0.005
    elif archetype == "seasonal_premium":
        multiplier = 1.15 if month in (11, 12) else 1.02
    elif archetype == "price_memory":
        multiplier = 1.10 if month >= 7 else 1.0
    elif archetype == "commodity_linked":
        multiplier = 1.0 + ((month % 6) - 2) * 0.03
    elif archetype == "declining_quality":
        multiplier = 1.0 + month * 0.006
    elif archetype == "new_unproven":
        multiplier = 0.98 + (index % 3) * 0.025
    elif archetype == "high_frequency_basic":
        multiplier = 0.96 + (index % 2) * 0.01
    elif archetype == "budget_volatile":
        multiplier = 0.90 + (index % 7) * 0.045
    elif archetype == "trust_trap":
        multiplier = 1.24 if month >= 9 else 0.97
    elif archetype == "format_changer":
        multiplier = 1.0 + (0.08 if index % 5 == 0 else 0.0)
    else:
        multiplier = 1.0
    return round(base_price * multiplier, 2)


def _lead_days_for(archetype: str, index: int) -> int:
    if archetype == "gold_reliable":
        return 3 + index % 2
    if archetype == "declining_quality":
        return 5 + index % 8
    if archetype == "new_unproven":
        return 6 + index % 6
    if archetype == "budget_volatile":
        return 2 + index % 10
    return 4 + index % 4


def _filter_since(rows: list[dict], field_name: str, since_days: int) -> list[dict]:
    if since_days >= 365:
        return list(rows)
    cutoff = date.today() - timedelta(days=int(since_days))
    filtered = []
    for row in rows:
        try:
            row_date = date.fromisoformat(str(row.get(field_name)))
        except ValueError:
            continue
        if row_date >= cutoff:
            filtered.append(row)
    return filtered


def _quarter(value: str) -> str:
    parsed = date.fromisoformat(value)
    return f"Q{((parsed.month - 1) // 3) + 1}"


def _lead_time_payload(lead_days: list[int], by_quarter: dict[str, list[int]]) -> dict:
    if not lead_days:
        return {
            "mean_days": None,
            "median_days": None,
            "std_days": None,
            "sample_count": 0,
            "by_quarter": {},
        }
    return {
        "mean_days": round(mean(lead_days), 2),
        "median_days": round(median(lead_days), 2),
        "std_days": round(pstdev(lead_days), 2) if len(lead_days) > 1 else 0.0,
        "sample_count": len(lead_days),
        "by_quarter": {key: round(mean(values), 2) for key, values in sorted(by_quarter.items())},
    }


MockQBOConnector = DemoQBOConnector
