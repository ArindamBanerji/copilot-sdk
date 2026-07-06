"""Generate deterministic Purchasing supplier and order fixtures.

K3 demo-population fixture (Rule 67).
All output carries provenance="sample".
This data substantiates nothing; it is for demo realism only.
Never use it in a metric, score, par, or claim (F-26).
"""

from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any


SEED = 42
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SUPPLIERS_PATH = DATA_DIR / "purchasing_suppliers.json"
ORDERS_PATH = DATA_DIR / "purchasing_orders.json"
SAMPLE_PROVENANCE = "sample"
VALID_FIXTURE_PROVENANCE = frozenset({"sample", "demo"})

CATEGORIES = ("protein", "produce", "dairy", "dry_goods", "beverages")
ACTIONS = ("order_as_planned", "order_more", "order_less", "skip")
FACTOR_NAMES = (
    "expected_demand",
    "day_of_week",
    "weather_forecast",
    "event_flag",
    "historical_waste",
    "supplier_lead_time",
    "price_memory_index",
)
ARCHETYPE_COUNTS = {
    "reliable_premium": 6,
    "budget_volatile": 5,
    "seasonal_specialist": 4,
    "local_organic": 4,
    "national_distributor": 5,
    "commodity_bulk": 4,
    "specialty_dairy": 3,
    "quick_turn": 4,
    "relationship_legacy": 3,
    "new_vendor": 4,
    "declining_quality": 4,
    "inconsistent_star": 4,
}

NAMED_SUPPLIERS = [
    ("PUR-SUP-001", "Sierra Farms", "reliable_premium", ("protein", "produce")),
    ("PUR-SUP-002", "Pacific Seafood Co", "reliable_premium", ("protein",)),
    ("PUR-SUP-003", "Valley Fresh Produce", "local_organic", ("produce",)),
    ("PUR-SUP-004", "Metro Dairy Direct", "specialty_dairy", ("dairy",)),
    ("PUR-SUP-005", "BulkFoods National", "commodity_bulk", ("dry_goods", "beverages")),
    ("PUR-SUP-006", "QuickDrop Express", "quick_turn", ("protein", "produce")),
    ("PUR-SUP-007", "Heritage Provisions", "relationship_legacy", ("protein", "dairy")),
    ("PUR-SUP-008", "NuVend Supply", "new_vendor", CATEGORIES),
    ("PUR-SUP-009", "Greenleaf Organics", "declining_quality", ("produce",)),
    ("PUR-SUP-010", "Flash Foods", "inconsistent_star", ("protein", "produce")),
    ("PUR-SUP-011", "Sunrise Bakery Dist", "seasonal_specialist", ("dry_goods",)),
    ("PUR-SUP-012", "Coastal Beverages", "national_distributor", ("beverages",)),
]

NAME_STEMS = (
    "Summit", "Oakline", "Blue Ridge", "Riverbend", "Crown", "Prairie", "Northstar",
    "Harbor", "Evergreen", "Canyon", "Redwood", "Silverline", "Orchard", "Stonefield",
    "Golden Gate", "Mesa", "BrightPath", "Farmstead", "Lakeside", "Urban Table",
    "Pioneer", "GoodRoots", "Peak", "Atlas", "Horizon", "Fieldstone", "MarketLink",
    "Bayview", "Clearwater", "Vista", "Meridian", "Cedar", "Union", "FreshRoute",
    "Highland", "Bridgeway", "Riverside", "Copper Hill",
)
NAME_SUFFIXES = (
    "Foods", "Supply", "Distributors", "Provisions", "Market Co", "Direct",
    "Wholesale", "Organics", "Specialty", "Logistics",
)

ARCHETYPE_PROFILES = {
    "reliable_premium": (0.94, 1.12, 0.03, 0.02, 92, "stable", 8),
    "budget_volatile": (0.78, 0.86, 0.10, 0.11, 54, "volatile", 4),
    "seasonal_specialist": (0.86, 1.02, 0.07, 0.06, 48, "seasonal", 6),
    "local_organic": (0.88, 1.09, 0.08, 0.04, 64, "stable", 5),
    "national_distributor": (0.91, 1.00, 0.04, 0.03, 120, "stable", 10),
    "commodity_bulk": (0.84, 0.91, 0.05, 0.05, 88, "stable", 7),
    "specialty_dairy": (0.89, 1.05, 0.06, 0.04, 44, "stable", 6),
    "quick_turn": (0.87, 1.04, 0.05, 0.05, 70, "improving", 3),
    "relationship_legacy": (0.82, 1.18, 0.07, 0.08, 104, "flat", 12),
    "new_vendor": (0.90, 0.97, 0.04, 0.03, 8, "new", 1),
    "declining_quality": (0.76, 1.03, 0.14, 0.12, 66, "declining", 5),
    "inconsistent_star": (0.81, 0.95, 0.11, 0.13, 38, "volatile", 2),
}

ITEMS_BY_CATEGORY = {
    "protein": ("chicken_breast", "ground_beef", "salmon_fillet", "pork_chops", "tofu_blocks"),
    "produce": ("mixed_greens", "tomatoes", "avocados", "strawberries", "bananas"),
    "dairy": ("whole_milk", "greek_yogurt", "shredded_cheese", "butter_blocks"),
    "dry_goods": ("flour_sacks", "rice_bags", "pasta_cases", "oats_bulk"),
    "beverages": ("cold_brew", "orange_juice", "sparkling_water", "iced_tea"),
}


def clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)


def generate_suppliers(rng: random.Random) -> list[dict[str, Any]]:
    suppliers: list[dict[str, Any]] = []
    remaining = dict(ARCHETYPE_COUNTS)
    for supplier_id, name, archetype, categories in NAMED_SUPPLIERS:
        suppliers.append(_supplier_record(rng, supplier_id, name, archetype, categories))
        remaining[archetype] -= 1

    name_index = 0
    next_id = 13
    for archetype, count in remaining.items():
        for _ in range(count):
            categories = _categories_for_archetype(rng, archetype)
            stem = NAME_STEMS[name_index % len(NAME_STEMS)]
            suffix = NAME_SUFFIXES[(name_index * 3) % len(NAME_SUFFIXES)]
            name_index += 1
            suppliers.append(
                _supplier_record(
                    rng,
                    f"PUR-SUP-{next_id:03d}",
                    f"{stem} {suffix}",
                    archetype,
                    categories,
                )
            )
            next_id += 1
    return sorted(suppliers, key=lambda row: row["supplier_id"])


def _categories_for_archetype(rng: random.Random, archetype: str) -> tuple[str, ...]:
    if archetype == "specialty_dairy":
        return ("dairy",)
    if archetype == "local_organic":
        return ("produce",)
    if archetype == "commodity_bulk":
        return ("dry_goods", "beverages")
    if archetype == "seasonal_specialist":
        return (rng.choice(("produce", "dry_goods", "beverages")),)
    if archetype in {"quick_turn", "inconsistent_star"}:
        return ("protein", "produce")
    if archetype == "national_distributor":
        return CATEGORIES
    return tuple(rng.sample(CATEGORIES, rng.randint(1, 3)))


def _supplier_record(
    rng: random.Random,
    supplier_id: str,
    name: str,
    archetype: str,
    categories: tuple[str, ...],
) -> dict[str, Any]:
    otif, price, waste, exceptions, order_count, trend, years = ARCHETYPE_PROFILES[archetype]
    lead_base = 1.0 if archetype == "quick_turn" else 4.0 if archetype == "national_distributor" else 2.5
    if archetype == "new_vendor":
        order_count = rng.randint(3, 12)
    if supplier_id == "PUR-SUP-009":
        trend = "declining"
    return {
        "supplier_id": supplier_id,
        "provenance": SAMPLE_PROVENANCE,
        "name": name,
        "archetype": archetype,
        "categories": list(categories),
        "primary_category": categories[0],
        "otif_score": clamp(otif + rng.uniform(-0.025, 0.025)),
        "avg_order_value": round(rng.uniform(900, 7200) * price, 2),
        "price_index": clamp(price + rng.uniform(-0.035, 0.035)),
        "lead_time_days": round(max(0.5, lead_base + rng.uniform(-0.4, 1.2)), 1),
        "waste_rate": clamp(waste + rng.uniform(-0.01, 0.012)),
        "order_count_90d": int(order_count + rng.randint(-4, 6)),
        "exception_rate": clamp(exceptions + rng.uniform(-0.012, 0.018)),
        "payment_terms": rng.choice(("Net 15", "Net 30", "Net 45", "2/10 Net 30")),
        "quality_score": clamp(1.0 - waste * 1.8 + rng.uniform(-0.035, 0.025)),
        "recent_trend": trend,
        "years_active": years,
        "min_order_value": round(rng.choice((250, 500, 750, 1000, 1500)), 2),
        "delivery_window": rng.choice(("AM", "Midday", "PM", "Next-day AM")),
        "notes": _supplier_notes(archetype, name),
    }


def _supplier_notes(archetype: str, name: str) -> str:
    notes = {
        "reliable_premium": "Consistent service at premium pricing.",
        "budget_volatile": "Low pricing with variable delivery performance.",
        "seasonal_specialist": "Best performance during seasonal demand windows.",
        "local_organic": "Local sourcing with weather-sensitive perishables.",
        "national_distributor": "Broad catalog and stable logistics.",
        "commodity_bulk": "Strong bulk pricing for shelf-stable categories.",
        "specialty_dairy": "Focused dairy catalog with reliable cold chain.",
        "quick_turn": "Fast lead times for urgent replenishment.",
        "relationship_legacy": "Long relationship can mask deteriorating economics.",
        "new_vendor": "Promising new vendor with limited historical volume.",
        "declining_quality": "Recent quality trend requires monitoring.",
        "inconsistent_star": "High upside with inconsistent execution.",
    }
    return f"{name}: {notes[archetype]}"


def generate_orders(rng: random.Random, suppliers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    suppliers_by_id = {supplier["supplier_id"]: supplier for supplier in suppliers}
    start = date(2025, 11, 24)
    end = date(2026, 5, 21)
    forced_ids = (
        ["PUR-SUP-007"] * 35
        + ["PUR-SUP-008"] * 15
        + ["PUR-SUP-009"] * 25
        + ["MONDAY_PATTERN"] * 40
        + ["WEATHER_PRODUCE_PATTERN"] * 30
        + ["EVENT_PATTERN"] * 25
    )
    remaining = 500 - len(forced_ids)
    population = [supplier["supplier_id"] for supplier in suppliers]
    weights = [_supplier_weight(supplier) for supplier in suppliers]
    supplier_ids = forced_ids + rng.choices(population, weights=weights, k=remaining)
    rng.shuffle(supplier_ids)

    orders: list[dict[str, Any]] = []
    greenleaf_seen = 0
    for index, token in enumerate(supplier_ids, start=1):
        order_date = start + timedelta(days=rng.randrange((end - start).days + 1))
        pattern = ""
        if token == "MONDAY_PATTERN":
            pattern = "monday_over_ordering"
            order_date = _nearest_weekday(order_date, 0)
            if order_date > end:
                order_date -= timedelta(days=7)
            supplier = _choose_supplier_for_category(rng, suppliers, "produce")
        elif token == "WEATHER_PRODUCE_PATTERN":
            pattern = "weather_insensitive_produce"
            supplier = _choose_supplier_for_category(rng, suppliers, "produce")
        elif token == "EVENT_PATTERN":
            pattern = "event_overreaction"
            supplier = _choose_supplier_for_category(rng, suppliers, rng.choice(("protein", "dairy")))
        else:
            supplier = suppliers_by_id[token]

        if supplier["supplier_id"] == "PUR-SUP-009":
            greenleaf_seen += 1
        category = _choose_category(rng, supplier)
        if pattern == "weather_insensitive_produce":
            category = "produce"
        item_count = rng.randint(1, 3)
        items = _items_for_order(rng, category, item_count)
        factors = _factors_for_order(rng, supplier, order_date, category, pattern)
        outcome = _outcome_for_order(
            rng,
            supplier,
            category,
            factors,
            pattern,
            greenleaf_seen,
        )
        total_value = round(
            supplier["avg_order_value"] * rng.uniform(0.45, 1.4) * max(1, item_count / 2),
            2,
        )
        verification_score = _verification_score(rng, supplier, pattern, outcome)
        orders.append(
            {
                "order_id": f"PUR-ORD-{index:04d}",
                "provenance": SAMPLE_PROVENANCE,
                "supplier_id": supplier["supplier_id"],
                "supplier_name": supplier["name"],
                "category": category,
                "items": items,
                "total_value": total_value,
                "order_date": order_date.isoformat(),
                "delivery_date": (order_date + timedelta(days=max(1, round(supplier["lead_time_days"])))).isoformat(),
                "status": rng.choice(("delivered", "verified", "closed")),
                "day_of_week": order_date.strftime("%A"),
                "factors": factors,
                "outcome": outcome,
                "verified": True,
                "verification_score": verification_score,
            }
        )
    _apply_longitudinal_patterns(orders)
    return sorted(orders, key=lambda row: row["order_id"])


def _supplier_weight(supplier: dict[str, Any]) -> float:
    if supplier["supplier_id"] == "PUR-SUP-008":
        return 0.25
    if supplier["supplier_id"] == "PUR-SUP-007":
        return 1.4
    if supplier["supplier_id"] == "PUR-SUP-009":
        return 0.9
    return max(0.3, float(supplier["order_count_90d"]) / 50.0)


def _nearest_weekday(value: date, weekday: int) -> date:
    return value + timedelta(days=(weekday - value.weekday()) % 7)


def _choose_supplier_for_category(
    rng: random.Random,
    suppliers: list[dict[str, Any]],
    category: str,
) -> dict[str, Any]:
    candidates = [supplier for supplier in suppliers if category in supplier["categories"]]
    return rng.choice(candidates)


def _choose_category(rng: random.Random, supplier: dict[str, Any]) -> str:
    return str(rng.choice(supplier["categories"]))


def _items_for_order(rng: random.Random, category: str, count: int) -> list[dict[str, Any]]:
    names = rng.sample(ITEMS_BY_CATEGORY[category], k=min(count, len(ITEMS_BY_CATEGORY[category])))
    return [
        {
            "item_id": name,
            "name": name,
            "quantity": round(rng.uniform(20, 220), 1),
            "unit": "lb" if category != "beverages" else "case",
        }
        for name in names
    ]


def _factors_for_order(
    rng: random.Random,
    supplier: dict[str, Any],
    order_date: date,
    category: str,
    pattern: str,
) -> dict[str, float]:
    day_factor = 0.18 if order_date.weekday() == 0 else rng.uniform(0.42, 0.82)
    weather = rng.uniform(0.45, 0.9)
    event = rng.uniform(0.0, 0.45)
    demand = rng.uniform(0.42, 0.84)
    waste = clamp(float(supplier["waste_rate"]) + rng.uniform(-0.02, 0.04))
    price_memory = clamp(1.0 - abs(float(supplier["price_index"]) - 1.0) * 1.5 + rng.uniform(-0.08, 0.06))
    if supplier["supplier_id"] == "PUR-SUP-007":
        price_memory = rng.uniform(0.24, 0.46)
    if pattern == "weather_insensitive_produce":
        weather = rng.uniform(0.12, 0.38)
        demand = rng.uniform(0.58, 0.9)
    if pattern == "event_overreaction":
        event = rng.uniform(0.75, 0.98)
        demand = rng.uniform(0.62, 0.92)
    if pattern == "monday_over_ordering":
        demand = rng.uniform(0.68, 0.95)
    return {
        "expected_demand": clamp(demand),
        "day_of_week": clamp(day_factor),
        "weather_forecast": clamp(weather),
        "event_flag": clamp(event),
        "historical_waste": clamp(waste),
        "supplier_lead_time": clamp(float(supplier["lead_time_days"]) / 7.0),
        "price_memory_index": clamp(price_memory),
    }


def _outcome_for_order(
    rng: random.Random,
    supplier: dict[str, Any],
    category: str,
    factors: dict[str, float],
    pattern: str,
    greenleaf_seen: int,
) -> dict[str, Any]:
    action = "order_as_planned"
    waste = max(0.0, float(supplier["waste_rate"]) + rng.uniform(-0.015, 0.035))
    usage = rng.uniform(0.72, 0.98)
    quality_issue = rng.random() < float(supplier["exception_rate"])
    stockout = rng.random() < 0.05
    if pattern == "monday_over_ordering":
        action = "order_more"
        waste += rng.uniform(0.12, 0.22)
        usage = rng.uniform(0.55, 0.74)
    elif pattern == "weather_insensitive_produce":
        action = "order_as_planned"
        waste += rng.uniform(0.13, 0.24)
        usage = rng.uniform(0.48, 0.72)
    elif pattern == "event_overreaction":
        action = "order_more"
        waste += rng.uniform(0.10, 0.20)
        usage = rng.uniform(0.50, 0.76)
    elif supplier["supplier_id"] == "PUR-SUP-007":
        action = "order_as_planned"
        waste += rng.uniform(0.04, 0.10)
    elif supplier["supplier_id"] == "PUR-SUP-008":
        action = rng.choice(("order_as_planned", "order_less"))
        waste *= 0.7
        usage = rng.uniform(0.80, 0.97)
    elif supplier["supplier_id"] == "PUR-SUP-009":
        action = rng.choice(("order_less", "order_as_planned"))
        quality_issue = greenleaf_seen > 12 and rng.random() < 0.65
        waste += rng.uniform(0.05, 0.15) if quality_issue else rng.uniform(0.01, 0.04)
    elif category == "produce" and factors["weather_forecast"] < 0.4:
        waste += rng.uniform(0.04, 0.08)
    elif category == "dry_goods" and factors["expected_demand"] < 0.55 and rng.random() < 0.25:
        action = "skip"

    if action == "skip":
        usage = 0.0
        waste = 0.0
    return {
        "action_taken": action if action in ACTIONS else "order_as_planned",
        "actual_usage_pct": clamp(usage),
        "waste_pct": clamp(waste),
        "stockout": bool(stockout),
        "quality_issue": bool(quality_issue),
        "cost_variance_pct": round((1.0 - factors["price_memory_index"]) * rng.uniform(0.02, 0.18), 4),
    }


def _verification_score(
    rng: random.Random,
    supplier: dict[str, Any],
    pattern: str,
    outcome: dict[str, Any],
) -> float:
    if supplier["supplier_id"] == "PUR-SUP-008":
        return clamp(rng.uniform(0.78, 0.92))
    penalty = float(outcome["waste_pct"]) * 0.4 + (0.12 if outcome["quality_issue"] else 0.0)
    if pattern:
        penalty += 0.08
    return clamp(rng.uniform(0.76, 0.95) - penalty)


def _apply_longitudinal_patterns(orders: list[dict[str, Any]]) -> None:
    greenleaf_orders = sorted(
        [order for order in orders if order["supplier_id"] == "PUR-SUP-009"],
        key=lambda row: row["order_date"],
    )
    midpoint = len(greenleaf_orders) // 2
    for position, order in enumerate(greenleaf_orders):
        declining = position >= midpoint
        order["outcome"]["quality_issue"] = bool(declining and position % 3 != 0)
        if declining:
            order["outcome"]["waste_pct"] = clamp(max(order["outcome"]["waste_pct"], 0.18))
            order["verification_score"] = clamp(min(order["verification_score"], 0.68))


def write_fixtures() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(SEED)
    suppliers = generate_suppliers(rng)
    orders = generate_orders(rng, suppliers)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SUPPLIERS_PATH.write_text(json.dumps(suppliers, indent=2, sort_keys=True), encoding="utf-8")
    ORDERS_PATH.write_text(json.dumps(orders, indent=2, sort_keys=True), encoding="utf-8")
    return suppliers, orders


def main() -> None:
    suppliers, orders = write_fixtures()
    print(f"wrote {len(suppliers)} suppliers to {SUPPLIERS_PATH}")
    print(f"wrote {len(orders)} orders to {ORDERS_PATH}")


if __name__ == "__main__":
    main()
