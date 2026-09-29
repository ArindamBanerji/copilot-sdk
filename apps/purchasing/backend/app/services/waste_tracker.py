"""Prep waste analysis in kitchen language."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from statistics import mean
from typing import Any, cast


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
    data_available: bool = True

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
            if item_orders and (
                len(item_orders) >= 5
                or any(
                    isinstance(row.get("factors"), dict)
                    or isinstance(row.get("factor_vector"), (list, tuple))
                    or isinstance(row.get("probabilities"), (list, tuple))
                    for row in item_orders
                )
            )
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
        if not waste_values:
            return ItemWasteProfile(
                item=item, category=category, order_count=0,
                average_waste_pct=0.0, benchmark_pct=benchmark,
                weekly_waste_cost=0.0, trend="stable", flagged=False,
                recommendation=_recommendation(category, False),
            )
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
            data_available=all(_row_data_available(row) for row in rows),
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
    factors = cast(dict[str, Any], order.get("factors")) if isinstance(order.get("factors"), dict) else {}
    outcome = cast(dict[str, Any], order.get("outcome")) if isinstance(order.get("outcome"), dict) else {}
    factor_vector = order.get("factor_vector")
    # AGE decisions use a compact vector rather than the kitchen order fields.
    # Preserve the decision as one analyzable item while retaining its category
    # and confidence for the waste calculation.
    vector_quantity = factor_vector[0] if isinstance(factor_vector, (list, tuple)) and factor_vector else None
    return [{
        "name": str(order.get("item") or order.get("item_name") or order.get("decision_id") or "unknown"),
        "quantity": order.get("quantity_lbs") or order.get("quantity") or factors.get("quantity") or vector_quantity or 1,
        "category": order.get("category") or "dry_goods",
        "unit_cost": order.get("unit_cost") or order.get("unit_price") or factors.get("unit_cost") or outcome.get("unit_cost") or 4,
    }]


def _waste_pct(row: dict[str, Any]) -> float:
    outcome = cast(dict[str, Any], row.get("outcome")) if isinstance(row.get("outcome"), dict) else {}
    factors = cast(dict[str, Any], row.get("factors")) if isinstance(row.get("factors"), dict) else {}
    value = row.get("waste_pct", outcome.get("waste_pct", row.get("historical_waste", factors.get("waste_pct"))))
    if value is None:
        correct = outcome.get("is_correct", row.get("is_correct"))
        score = row.get("score", row.get("confidence", factors.get("confidence")))
        if correct is False:
            try:
                value = 1.0 - float(score or 0.0)
            except (TypeError, ValueError):
                value = 1.0
        else:
            value = 0.0
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number / 100.0 if number > 1 else number


def _row_data_available(row: dict[str, Any]) -> bool:
    raw_outcome = row.get("outcome")
    outcome: dict[str, Any] = raw_outcome if isinstance(raw_outcome, dict) else {}
    raw_factors = row.get("factors")
    factors: dict[str, Any] = raw_factors if isinstance(raw_factors, dict) else {}
    waste_value = row.get("waste_pct", outcome.get("waste_pct", row.get("historical_waste", factors.get("waste_pct"))))
    quantity = row.get("quantity")
    unit_cost = row.get("unit_cost")
    for value in (waste_value, quantity, unit_cost):
        if value is None:
            return False
        try:
            float(value)
        except (TypeError, ValueError):
            return False
    return True


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
