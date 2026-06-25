"""Event planning support for Purchasing."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from copilot_sdk.scoring.presets.purchasing import PurchasingPreset


DEFAULT_TEMPLATES: dict[str, dict[str, float]] = {
    "mixed": {"protein": 0.45, "produce": 0.30, "dairy": 0.12, "dry_goods": 0.18, "beverages": 0.35},
    "american": {"protein": 0.50, "produce": 0.25, "dairy": 0.10, "dry_goods": 0.20, "beverages": 0.35},
    "italian": {"protein": 0.35, "produce": 0.30, "dairy": 0.22, "dry_goods": 0.25, "beverages": 0.30},
}

_CATEGORY_COSTS = {"protein": 8.0, "produce": 3.0, "dairy": 4.0, "dry_goods": 2.0, "beverages": 1.5}


@dataclass
class EventPlan:
    guest_count: int
    cuisine: str
    categories: list[dict[str, Any]]
    estimated_cost: float
    expected_waste_pct: float
    similar_events: int
    confidence: str
    dollar_impact: float
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EventPlanner:
    def __init__(self, history: list[dict[str, Any]] | None = None) -> None:
        self._history = list(_demo_history() if history is None else history)

    def plan(self, guest_count: int, cuisine: str = "mixed", past_events: list[dict[str, Any]] | None = None) -> EventPlan:
        guests = max(int(guest_count or 0), 0)
        cuisine_key = str(cuisine or "mixed").strip().lower()
        template = DEFAULT_TEMPLATES.get(cuisine_key, DEFAULT_TEMPLATES["mixed"])
        category_names = list(PurchasingPreset().shape.category_names)
        similar = self.similar_events(guests, past_events)
        adjustment = _usage_adjustment(similar)
        waste = _waste_rate(similar)
        categories: list[dict[str, Any]] = []
        total_cost = 0.0
        for category in category_names:
            pounds_per_guest = template.get(category, DEFAULT_TEMPLATES["mixed"].get(category, 0.1))
            quantity = round(guests * pounds_per_guest * adjustment, 1)
            cost = round(quantity * _CATEGORY_COSTS.get(category, 3.0), 2)
            total_cost += cost
            categories.append({
                "category": category,
                "quantity_lbs": quantity,
                "estimated_cost": cost,
                "text": f"For {guests} guests, plan about {quantity:g} lbs {category.replace('_', ' ')}.",
            })
        return EventPlan(
            guest_count=guests,
            cuisine=cuisine_key,
            categories=categories,
            estimated_cost=round(total_cost, 2),
            expected_waste_pct=round(waste, 3),
            similar_events=len(similar),
            confidence="high" if len(similar) >= 10 else "medium" if len(similar) >= 3 else "low",
            dollar_impact=1200.0,
            note="Last unplanned event cost $1,200 in waste and missed tables.",
        )

    def record_outcome(self, plan: dict[str, Any], actual_usage: dict[str, float], actual_waste: float) -> dict[str, Any]:
        event = {
            "guest_count": int(plan.get("guest_count") or plan.get("guestCount") or 0),
            "cuisine": str(plan.get("cuisine") or "mixed"),
            "actual_usage": dict(actual_usage or {}),
            "waste_pct": float(actual_waste or 0.0),
        }
        self._history.append(event)
        return {"recorded": True, "events": len(self._history), "event": event}

    def similar_events(self, guest_count: int, past_events: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        rows = list(past_events if past_events is not None else self._history)
        lower = guest_count * 0.7
        upper = guest_count * 1.3
        return [row for row in rows if lower <= _number(row.get("guest_count"), 0) <= upper]

    def history(self) -> list[dict[str, Any]]:
        return list(self._history)


def _usage_adjustment(events: list[dict[str, Any]]) -> float:
    if not events:
        return 1.0
    ratios = []
    for event in events:
        planned = _number(event.get("planned_lbs"), 1.0)
        used = _number(event.get("used_lbs"), planned)
        if planned > 0:
            ratios.append(used / planned)
    if not ratios:
        return 1.0
    return max(0.8, min(sum(ratios) / len(ratios), 1.25))


def _waste_rate(events: list[dict[str, Any]]) -> float:
    if not events:
        return 0.10
    values = [_number(row.get("waste_pct"), 0.10) for row in events]
    return sum(values) / len(values)


def _number(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _demo_history() -> list[dict[str, Any]]:
    return [
        {"guest_count": 72, "cuisine": "mixed", "planned_lbs": 64, "used_lbs": 61, "waste_pct": 0.08},
        {"guest_count": 84, "cuisine": "american", "planned_lbs": 76, "used_lbs": 74, "waste_pct": 0.07},
        {"guest_count": 90, "cuisine": "mixed", "planned_lbs": 82, "used_lbs": 79, "waste_pct": 0.09},
        {"guest_count": 66, "cuisine": "italian", "planned_lbs": 58, "used_lbs": 57, "waste_pct": 0.08},
        {"guest_count": 100, "cuisine": "american", "planned_lbs": 91, "used_lbs": 88, "waste_pct": 0.09},
        {"guest_count": 78, "cuisine": "mixed", "planned_lbs": 70, "used_lbs": 67, "waste_pct": 0.07},
    ]
