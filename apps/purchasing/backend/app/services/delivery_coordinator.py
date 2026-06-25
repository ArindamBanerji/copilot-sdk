"""Delivery schedule support for Purchasing."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any


DEMO_SUPPLIER_SCHEDULES = {
    "sysco": {"name": "Sysco", "delivers_days": ["Mon", "Wed", "Fri"], "window": "7am-9am"},
    "fresh_produce": {"name": "FreshProduce", "delivers_days": ["Mon", "Tue", "Thu"], "window": "9am-11am"},
    "dairy_direct": {"name": "DairyDirect", "delivers_days": ["Mon", "Wed", "Fri"], "window": "11am-1pm"},
}

DEMO_PENDING_ORDERS = [
    {"supplier": "sysco", "items": ["protein", "dry_goods"], "amount": 1240},
    {"supplier": "sysco", "items": ["dry_goods"], "amount": 420},
    {"supplier": "fresh_produce", "items": ["produce"], "amount": 610},
    {"supplier": "dairy_direct", "items": ["dairy"], "amount": 380},
]


class DeliveryCoordinator:
    RECEIVING_MINUTES = 30

    def schedule_day(
        self,
        day: date | str,
        pending_orders: list[dict[str, Any]] | None = None,
        suppliers: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        target = _to_date(day)
        orders = list(pending_orders or DEMO_PENDING_ORDERS)
        supplier_rows = suppliers or DEMO_SUPPLIER_SCHEDULES
        weekday = target.strftime("%a")
        deliveries = []
        unknown = []
        for order in orders:
            supplier_id = str(order.get("supplier") or "")
            supplier = supplier_rows.get(supplier_id)
            if supplier is None:
                unknown.append(order)
                continue
            if weekday not in supplier.get("delivers_days", []):
                continue
            existing = next((row for row in deliveries if row.get("supplier_id") == supplier_id), None)
            if existing is not None:
                existing["items"] = sorted(set(existing.get("items", [])) | set(order.get("items") or []))
                existing["amount"] = float(existing.get("amount") or 0) + float(order.get("amount") or 0)
                existing["merged_orders"] = int(existing.get("merged_orders") or 1) + 1
                continue
            deliveries.append({
                "supplier": supplier.get("name", supplier_id),
                "supplier_id": supplier_id,
                "window": str(supplier.get("window", "Call supplier")),
                "items": list(order.get("items") or []),
                "amount": float(order.get("amount") or 0),
                "merged_orders": 1,
            })
        return {
            "date": target.isoformat(),
            "deliveries": deliveries,
            "unknown_suppliers": unknown,
            "receiving_minutes": len(deliveries) * self.RECEIVING_MINUTES,
            "provenance": "demo",
        }

    def schedule_week(
        self,
        start_date: date | str,
        pending_orders: list[dict[str, Any]] | None = None,
        suppliers: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        start = _to_date(start_date)
        days = [self.schedule_day(start + timedelta(days=offset), pending_orders, suppliers) for offset in range(7)]
        deliveries = sum(len(day["deliveries"]) for day in days)
        suggestions = self.suggest_consolidation_week(days)
        return {
            "start": start.isoformat(),
            "days": days,
            "delivery_count": deliveries,
            "opportunities": len(suggestions),
            "receiving_hours_saved": round(len(suggestions) * self.RECEIVING_MINUTES / 60, 1),
            "provenance": "demo",
        }

    def suggest_consolidation(self, schedule: dict[str, Any]) -> list[dict[str, Any]]:
        suggestions = []
        for delivery in schedule.get("deliveries", []):
            if int(delivery.get("merged_orders") or 1) < 2:
                continue
            supplier = delivery.get("supplier", delivery.get("supplier_id", "supplier"))
            items = sorted(delivery.get("items", []))
            suggestions.append({
                "supplier": supplier,
                "items": items,
                "minutes_saved": self.RECEIVING_MINUTES,
                "text": f"Combine {supplier} {' + '.join(items)} into one delivery. Save 30 min receiving.",
            })
        return suggestions

    def suggest_consolidation_week(self, week_schedule: list[dict[str, Any]]) -> list[dict[str, Any]]:
        suggestions = []
        for day_schedule in week_schedule:
            suggestions.extend(self.suggest_consolidation(day_schedule))
        return suggestions


def _to_date(value: date | str) -> date:
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        return date.today()

