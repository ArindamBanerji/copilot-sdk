"""Restaurant menu engineering for Purchasing."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from statistics import median
from typing import Any


@dataclass(frozen=True)
class MenuItemAnalysis:
    name: str
    price: float
    food_cost: float
    food_cost_pct: float
    contribution_margin: float
    popularity: float
    classification: str
    recommendation: str
    previous_food_cost_pct: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MenuEngineer:
    """Star, puzzle, plowhorse, dog matrix."""

    def analyze(self, menu_items: list[dict[str, Any]], cost_data: dict[str, Any] | None = None) -> list[MenuItemAnalysis]:
        cost_data = cost_data or {}
        if not menu_items:
            return []
        popular_cut = median([_number(item.get("orders"), 0) for item in menu_items])
        margin_cut = median([_price(item) - _cost(item, cost_data) for item in menu_items])
        analyses = []
        for item in menu_items:
            name = str(item.get("name") or "Unknown item")
            price = _price(item)
            food_cost = _cost(item, cost_data)
            margin = price - food_cost
            popularity = _number(item.get("orders"), 0)
            high_pop = popularity >= popular_cut
            high_margin = margin >= margin_cut
            classification = _classify(high_pop, high_margin)
            analyses.append(MenuItemAnalysis(
                name=name,
                price=round(price, 2),
                food_cost=round(food_cost, 2),
                food_cost_pct=round(food_cost / price, 4) if price > 0 else 0.0,
                contribution_margin=round(margin, 2),
                popularity=popularity,
                classification=classification,
                recommendation=_recommendation(classification),
                previous_food_cost_pct=_previous_pct(item),
            ))
        return analyses

    def recommendations(self, analyses: list[MenuItemAnalysis]) -> list[str]:
        return [f"{item.name}: {item.recommendation}" for item in analyses]

    def margin_alerts(self, analyses: list[MenuItemAnalysis], threshold: float = 5.0) -> list[dict[str, Any]]:
        alerts = []
        for item in analyses:
            if item.previous_food_cost_pct is None:
                continue
            change_pp = (item.food_cost_pct - item.previous_food_cost_pct) * 100
            if change_pp >= threshold:
                alerts.append({
                    "item": item.name,
                    "from_pct": round(item.previous_food_cost_pct, 4),
                    "to_pct": item.food_cost_pct,
                    "change_pp": round(change_pp, 1),
                    "message": f"{item.name} food cost rose. Consider a seasonal menu change or supplier switch.",
                })
        return alerts


def demo_menu_items() -> list[dict[str, Any]]:
    return [
        {"name": "Salmon entree", "price": 28, "food_cost": 10.08, "previous_food_cost_pct": 0.28, "orders": 86},
        {"name": "Chicken sandwich", "price": 18, "food_cost": 5.20, "previous_food_cost_pct": 0.30, "orders": 110},
        {"name": "Mushroom risotto", "price": 22, "food_cost": 6.00, "previous_food_cost_pct": 0.27, "orders": 32},
        {"name": "Seasonal salad", "price": 16, "food_cost": 7.20, "previous_food_cost_pct": 0.44, "orders": 95},
        {"name": "Lamb special", "price": 34, "food_cost": 16.50, "previous_food_cost_pct": 0.47, "orders": 24},
        {"name": "Kids pasta", "price": 12, "food_cost": 3.10, "previous_food_cost_pct": 0.26, "orders": 70},
    ]


def _price(item: dict[str, Any]) -> float:
    return _number(item.get("price") or item.get("menu_price"), 0)


def _cost(item: dict[str, Any], cost_data: dict[str, Any]) -> float:
    name = str(item.get("name") or "")
    return _number(cost_data.get(name, item.get("food_cost") or item.get("cost")), 0)


def _previous_pct(item: dict[str, Any]) -> float | None:
    value = item.get("previous_food_cost_pct")
    if value is None:
        return None
    return _number(value, 0)


def _number(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _classify(high_popularity: bool, high_margin: bool) -> str:
    if high_popularity and high_margin:
        return "star"
    if not high_popularity and high_margin:
        return "puzzle"
    if high_popularity and not high_margin:
        return "plowhorse"
    return "dog"


def _recommendation(classification: str) -> str:
    return {
        "star": "Keep promoting. Protect supplier relationships.",
        "puzzle": "Reposition with better menu placement and staff training.",
        "plowhorse": "Re-engineer ingredients and find cheaper alternatives.",
        "dog": "Consider seasonal removal or reformulation.",
    }[classification]
