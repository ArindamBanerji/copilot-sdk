"""Prep waste analysis in kitchen language."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from statistics import mean
from typing import Any


INDUSTRY_BENCHMARKS = {
    "protein": 0.12,
    "produce": 0.15,
    "dairy": 0.08,
    "dry_goods": 0.03,
    "beverages": 0.02,
}


@dataclass(frozen=True)
class ItemWasteProfile:
    item: str
    category: str
    order_count: int
    average_waste_pct: float
    benchmark_pct: float
    weekly_waste_cost: float
    trend: str
    flagged: bool
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class WasteTracker:
    DEFAULT_BENCHMARKS = INDUSTRY_BENCHMARKS

    def __init__(self, orders: list[dict[str, Any]], benchmarks: dict[str, float] | None = None):
        self._orders = orders
        self.benchmarks = benchmarks or self.DEFAULT_BENCHMARKS

    def analyze_all(self, orders: list[dict[str, Any]] | None = None) -> list[ItemWasteProfile]:
        rows = orders if orders is not None else self._orders
        grouped: dict[str, list[dict[str, Any]]] = {}
        for order in rows:
            for item in _items_for_order(order):
                grouped.setdefault(item["name"], []).append({**order, **item})
        profiles = [
            self._profile(item, item_orders)
            for item, item_orders in grouped.items()
            if len(item_orders) >= 5
        ]
        return sorted(profiles, key=lambda profile: profile.weekly_waste_cost, reverse=True)

    def top_waste_items(self, limit: int = 5) -> list[ItemWasteProfile]:
        return self.analyze_all()[:limit]

    def weekly_waste_cost(self) -> dict[str, Any]:
        profiles = self.analyze_all()
        total = sum(profile.weekly_waste_cost for profile in profiles)
        top_three = sum(profile.weekly_waste_cost for profile in profiles[:3])
        prevented_this_week = top_three * 0.25
        return {
            "weekly_waste_cost": round(total, 2),
            "top_three_addressable": round(top_three, 2),
            "prevented_this_week": round(prevented_this_week, 2),
        }

    def _profile(self, item: str, rows: list[dict[str, Any]]) -> ItemWasteProfile:
        category = str(rows[0].get("category") or "dry_goods")
        benchmark = self.benchmarks.get(category, 0.10)
        waste_values = [_waste_pct(row) for row in rows]
        avg_waste = mean(waste_values)
        weekly_cost = sum(_unit_cost(row) * _quantity(row) * _waste_pct(row) for row in rows[-7:])
        flagged = avg_waste > benchmark * 1.5
        return ItemWasteProfile(
            item=item,
            category=category,
            order_count=len(rows),
            average_waste_pct=round(avg_waste, 4),
            benchmark_pct=benchmark,
            weekly_waste_cost=round(weekly_cost, 2),
            trend=_trend(waste_values),
            flagged=flagged,
            recommendation=_recommendation(category, flagged),
        )


def _items_for_order(order: dict[str, Any]) -> list[dict[str, Any]]:
    items = order.get("items")
    if isinstance(items, list) and items:
        return [
            {
                "name": str(item.get("name") or item.get("item_id") or order.get("item") or "unknown"),
                "quantity": item.get("quantity") or order.get("quantity_lbs") or order.get("quantity") or 1,
                "category": order.get("category"),
                "unit_cost": item.get("unit_cost") or order.get("unit_cost") or order.get("unit_price") or 4,
            }
            for item in items
            if isinstance(item, dict)
        ]
    return [{
        "name": str(order.get("item") or order.get("item_name") or "unknown"),
        "quantity": order.get("quantity_lbs") or order.get("quantity") or 1,
        "category": order.get("category"),
        "unit_cost": order.get("unit_cost") or order.get("unit_price") or 4,
    }]


def _waste_pct(row: dict[str, Any]) -> float:
    outcome = row.get("outcome") if isinstance(row.get("outcome"), dict) else {}
    value = row.get("waste_pct", outcome.get("waste_pct", row.get("historical_waste", 0)))
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number / 100.0 if number > 1 else number


def _quantity(row: dict[str, Any]) -> float:
    try:
        return max(float(row.get("quantity", 1)), 0.0)
    except (TypeError, ValueError):
        return 1.0


def _unit_cost(row: dict[str, Any]) -> float:
    try:
        return max(float(row.get("unit_cost", 4)), 0.0)
    except (TypeError, ValueError):
        return 4.0


def _trend(values: list[float]) -> str:
    if len(values) < 4:
        return "stable"
    recent = mean(values[-3:])
    early = mean(values[:3])
    if recent < early * 0.9:
        return "improving"
    if recent > early * 1.1:
        return "worsening"
    return "stable"


def _recommendation(category: str, flagged: bool) -> str:
    if not flagged:
        return "Keep current prep plan."
    if category == "protein":
        return "Switch to pre-portioned. A small premium can save more in waste."
    if category == "produce":
        return "Reduce par for slow days. Tuesday produce par should be lower than Friday."
    if category == "dairy":
        return "Check walk-in temp. Dairy waste spikes when the cooler runs warm."
    return "Review pack size and shelf placement before the next order."
