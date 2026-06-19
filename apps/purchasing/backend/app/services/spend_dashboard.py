"""Food cost dashboard analytics for Purchasing."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from statistics import mean
from typing import Any

from copilot_sdk.scoring.presets.purchasing import PurchasingPreset


class SpendDashboardService:
    """Food cost analytics from order data. Read-only.

    Kitchen language: covers, supplier, order, and waste.
    """

    def __init__(self, orders: list[dict]):
        self._orders = [order for order in orders if isinstance(order, dict)]

    def summary(self, days: int = 7) -> dict:
        """Return total spend, order count, average order amount, and cost per cover."""
        rows = self._windowed_orders(days)
        total = sum(_amount(row) for row in rows)
        order_count = len(rows)
        covers = sum(_covers(row) for row in rows if _covers(row) is not None)
        has_covers = any(_covers(row) is not None for row in rows)
        start, end = _period_bounds(rows)
        return {
            "total_spend": round(total, 2),
            "order_count": order_count,
            "avg_order_amount": round(total / order_count, 2) if order_count else 0.0,
            "cost_per_cover": round(total / covers, 2) if has_covers and covers > 0 else None,
            "period_start": start,
            "period_end": end,
        }

    def by_category(self, days: int = 30) -> list[dict]:
        """Return spend breakdown by food category."""
        rows = self._windowed_orders(days)
        category_names = list(PurchasingPreset().shape.category_names)
        totals = {category: 0.0 for category in category_names}
        counts = {category: 0 for category in category_names}
        for row in rows:
            category = str(row.get("category") or "")
            if category not in totals:
                totals[category] = 0.0
                counts[category] = 0
            totals[category] += _amount(row)
            counts[category] += 1
        total_spend = sum(totals.values())
        return [
            {
                "category": category,
                "total_amount": round(totals.get(category, 0.0), 2),
                "order_count": counts.get(category, 0),
                "pct_of_total": round((totals.get(category, 0.0) / total_spend) * 100, 2)
                if total_spend > 0
                else 0.0,
            }
            for category in category_names
        ]

    def by_supplier(self, days: int = 30, limit: int = 10) -> list[dict]:
        """Return top suppliers by spend."""
        rows = self._windowed_orders(days)
        grouped: dict[str, dict[str, Any]] = {}
        for row in rows:
            supplier_id = str(row.get("supplier_id") or "unknown")
            supplier = grouped.setdefault(
                supplier_id,
                {
                    "supplier_id": supplier_id,
                    "supplier_name": str(row.get("supplier_name") or supplier_id),
                    "total_amount": 0.0,
                    "order_count": 0,
                    "categories": set(),
                },
            )
            supplier["total_amount"] += _amount(row)
            supplier["order_count"] += 1
            if row.get("category"):
                supplier["categories"].add(str(row["category"]))
        result = [
            {
                "supplier_id": row["supplier_id"],
                "supplier_name": row["supplier_name"],
                "total_amount": round(row["total_amount"], 2),
                "order_count": row["order_count"],
                "categories": sorted(row["categories"]),
            }
            for row in grouped.values()
        ]
        result.sort(key=lambda row: row["total_amount"], reverse=True)
        return result[: max(0, int(limit))]

    def price_alerts(self, threshold_pct: float = 10.0) -> list[dict]:
        """Return line items priced above their rolling average."""
        threshold = float(threshold_pct)
        by_item: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for order in self._orders_sorted():
            for line in _line_items(order):
                item_name = str(line.get("name") or line.get("item_name") or line.get("item_id") or "")
                unit_price = _line_unit_price(order, line)
                if not item_name or unit_price is None:
                    continue
                by_item[item_name].append(
                    {
                        "date": _order_date(order),
                        "item_name": item_name,
                        "unit_price": unit_price,
                        "supplier_name": str(order.get("supplier_name") or ""),
                        "category": str(order.get("category") or line.get("category") or ""),
                    }
                )

        alerts = []
        for item_name, rows in by_item.items():
            dated = [row for row in rows if row["date"] is not None]
            dated.sort(key=lambda row: row["date"])
            if len(dated) < 2:
                continue
            current = dated[-1]
            history = [float(row["unit_price"]) for row in dated[:-1]]
            avg_price = mean(history)
            if avg_price <= 0:
                continue
            variance = ((float(current["unit_price"]) - avg_price) / avg_price) * 100
            if variance > threshold:
                alerts.append(
                    {
                        "item_name": item_name,
                        "current_price": round(float(current["unit_price"]), 4),
                        "avg_price": round(avg_price, 4),
                        "variance_pct": round(variance, 2),
                        "supplier_name": current["supplier_name"],
                        "category": current["category"],
                    }
                )
        alerts.sort(key=lambda row: row["variance_pct"], reverse=True)
        return alerts

    def cost_per_cover_trend(self, days: int = 30) -> list[dict]:
        """Return daily cost per cover where cover data exists."""
        grouped: dict[date, dict[str, float]] = defaultdict(lambda: {"total_spend": 0.0, "covers": 0.0})
        for row in self._windowed_orders(days):
            parsed = _order_date(row)
            if parsed is None:
                continue
            grouped[parsed]["total_spend"] += _amount(row)
            covers = _covers(row)
            if covers is not None:
                grouped[parsed]["covers"] += covers
        return [
            {
                "date": day.isoformat(),
                "total_spend": round(values["total_spend"], 2),
                "covers": int(values["covers"]) if values["covers"] > 0 else None,
                "cost_per_cover": round(values["total_spend"] / values["covers"], 2)
                if values["covers"] > 0
                else None,
            }
            for day, values in sorted(grouped.items())
        ]

    def _orders_sorted(self) -> list[dict]:
        return sorted(self._orders, key=lambda row: _order_date(row) or date.min)

    def _windowed_orders(self, days: int) -> list[dict]:
        if not self._orders:
            return []
        parsed_dates = [_order_date(row) for row in self._orders]
        parsed_dates = [value for value in parsed_dates if value is not None]
        if not parsed_dates:
            return list(self._orders)
        period_days = max(1, int(days))
        end = max(parsed_dates)
        start = end - timedelta(days=period_days - 1)
        return [
            row
            for row in self._orders
            if (parsed := _order_date(row)) is not None and start <= parsed <= end
        ]


def _amount(order: dict[str, Any]) -> float:
    for key in ("total_spend", "total_value", "total_amount", "amount"):
        if key in order:
            try:
                return max(0.0, float(order.get(key) or 0.0))
            except (TypeError, ValueError):
                return 0.0
    return 0.0


def _covers(order: dict[str, Any]) -> float | None:
    for key in ("covers", "cover_count", "expected_covers", "normal_covers"):
        if key not in order:
            continue
        try:
            value = float(order.get(key))
        except (TypeError, ValueError):
            return None
        return value if value > 0 else None
    return None


def _order_date(order: dict[str, Any]) -> date | None:
    value = order.get("order_date") or order.get("date") or order.get("delivery_date")
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _period_bounds(rows: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    dates = [_order_date(row) for row in rows]
    dates = [value for value in dates if value is not None]
    if not dates:
        return None, None
    return min(dates).isoformat(), max(dates).isoformat()


def _line_items(order: dict[str, Any]) -> list[dict[str, Any]]:
    items = order.get("items")
    if isinstance(items, list):
        return [item for item in items if isinstance(item, dict)]
    return []


def _line_unit_price(order: dict[str, Any], line: dict[str, Any]) -> float | None:
    for key in ("unit_price", "price", "current_price"):
        if key in line:
            try:
                value = float(line.get(key))
            except (TypeError, ValueError):
                return None
            return value if value > 0 else None
    quantity = line.get("quantity")
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        return None
    if qty <= 0:
        return None
    total_quantity = 0.0
    for item in _line_items(order):
        try:
            total_quantity += max(0.0, float(item.get("quantity") or 0.0))
        except (TypeError, ValueError):
            continue
    if total_quantity <= 0:
        return None
    return _amount(order) / total_quantity
