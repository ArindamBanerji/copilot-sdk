"""Cached purchasing context endpoints."""

from __future__ import annotations

import json
import math
import os
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any, Callable

from fastapi import APIRouter, HTTPException, status

from app.data_helpers import write_purchasing_fixture
from app.factors import compute_factors
from copilot_sdk.scoring.verification.weather import get_weather_factor


router = APIRouter(tags=["context"])
_evolution_store_factory: Callable[[], Any] | None = None
_APP_DIR = Path(__file__).resolve().parent
_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_FACTOR_NAMES = (
    # Mirrors PurchasingPreset factor order.
    "expected_demand",
    "day_of_week",
    "weather_forecast",
    "event_flag",
    "historical_waste",
    "supplier_lead_time",
    "price_memory_index",
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_data_json(filename: str, default: Any) -> Any:
    path = _DATA_DIR / filename
    if path.exists():
        return _load_json(path)
    fallback_path = _DEFAULT_DATA_DIR / filename
    if fallback_path.exists():
        return _load_json(fallback_path)
    return default


def set_evolution_store_factory(factory: Callable[[], Any] | None) -> None:
    global _evolution_store_factory
    _evolution_store_factory = factory


def _variant_from_evolution_event(event: dict[str, Any]) -> dict[str, Any]:
    metadata = event.get("metadata") if isinstance(event.get("metadata"), dict) else {}
    variant = dict(metadata)
    event_type = str(variant.get("event_type") or event.get("event_type") or "")
    rule_name = str(event.get("rule_name") or variant.get("rule_name") or "")
    variant_id = str(
        event.get("variant_id")
        or variant.get("variant_id")
        or variant.get("variantId")
        or rule_name
    )
    variant["event_type"] = event_type
    variant.setdefault("rule_name", rule_name)
    variant.setdefault("variant_id", variant_id)
    variant.setdefault("id", variant_id or rule_name)
    variant.setdefault("description", rule_name or variant_id)
    variant.setdefault("timestamp", event.get("timestamp"))
    return variant


def _evolution_variants() -> list[dict[str, Any]]:
    if _evolution_store_factory is None:
        return []
    try:
        store = _evolution_store_factory()
        events = store.get_evolution_events(domain="purchasing", limit=500)
    except Exception:
        return []
    return [_variant_from_evolution_event(event) for event in events if isinstance(event, dict)]


def _item_key(item: str) -> str:
    return item.strip().lower().replace(" ", "_")


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


def _order_vector(order: dict[str, Any]) -> list[float]:
    factors = _merged_order_factors(order)
    return [float(factors.get(name, 0.5)) for name in _FACTOR_NAMES]


def _merged_order_factors(order: dict[str, Any]) -> dict[str, float]:
    computed = compute_factors(_factor_context(order))
    return {**computed, **_explicit_factor_overrides(order)}


def _factor_context(order: dict[str, Any]) -> dict[str, Any]:
    outcome = order.get("outcome") if isinstance(order.get("outcome"), dict) else {}
    context = {
        "forecast_demand": order.get("forecast_demand") or order.get("expected_demand"),
        "par_level": order.get("par_level"),
        "day_of_week": _day_index(order.get("day_of_week")),
        "weather_score": order.get("weather_score") or order.get("weather_forecast"),
        "weather": order.get("weather"),
        "event_flag": order.get("event_flag"),
        "event_covers": order.get("event_covers"),
        "normal_covers": order.get("normal_covers"),
        "waste_pct": order.get("waste_pct") or order.get("historical_waste") or outcome.get("waste_pct"),
        "lead_time_days": order.get("lead_time_days") or order.get("supplier_lead_time"),
        "price_change_count": order.get("price_change_count"),
        "months_tracked": order.get("months_tracked"),
    }
    return {key: value for key, value in context.items() if value is not None}


def _explicit_factor_overrides(order: dict[str, Any]) -> dict[str, float]:
    overrides: dict[str, float] = {}
    for name in _FACTOR_NAMES:
        if name == "day_of_week" and order.get("day_of_week_factor") is not None:
            raw = order.get("day_of_week_factor")
        elif name in order:
            raw = order.get(name)
        else:
            continue
        value = _finite_factor(raw)
        if value is not None:
            overrides[name] = value
    return overrides


def _day_index(value: Any) -> Any:
    if isinstance(value, str):
        lookup = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }
        return lookup.get(value.strip().lower())
    return value


def _finite_factor(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    if 0.0 <= number <= 1.0:
        return number
    return None


def _waste_trend(values: list[float]) -> str:
    if len(values) < 2:
        return "unknown"
    delta = values[-1] - values[0]
    if abs(delta) < 0.01:
        return "flat"
    return "up" if delta > 0 else "down"


def _rule_matches_item(rule: dict[str, Any], item: dict[str, Any]) -> bool:
    if rule.get("event_type") != "promotion_approved":
        return False
    match = rule.get("match")
    if not isinstance(match, dict):
        return False

    categories = match.get("categories")
    if categories and item.get("category") not in categories:
        return False
    if match.get("event_required") and item.get("category") != "protein":
        return float(item.get("event_sensitivity", 0.0)) >= 0.5
    return True


def _get_weather() -> dict[str, Any]:
    use_live = os.environ.get("WEATHER_LIVE", "true").lower() != "false"
    if use_live:
        live = asdict(get_weather_factor(use_live=True))
        if live.get("source") == "live":
            return live

    cache_path = _DATA_DIR / "weather_cache.json"
    if cache_path.exists():
        return _load_json(cache_path)
    return asdict(get_weather_factor(use_live=False))


@router.get("/today-summary")
def today_summary() -> dict[str, Any]:
    return {
        "date": date.today().isoformat(),
        "day_of_week": date.today().strftime("%A"),
        "weather": _get_weather(),
        "events": [],
    }


@router.get("/items")
def items() -> list[dict[str, Any]]:
    path = _APP_DIR / "items.json"
    if not path.exists():
        return [
            {
                "item_id": "item-001",
                "name": "chicken_breast",
                "category": "protein",
                "unit": "lb",
                "par_level": 120,
                "supplier_lead_time": 0.45,
            }
        ]
    return _load_json(path)


@router.get("/waste-history/{item}")
def waste_history(item: str) -> dict[str, Any]:
    key = _item_key(item)
    history = _load_json(_DATA_DIR / "waste_history.json")
    values = history.get(key, [])
    return {"item": key, "waste_pct": values, "count": len(values)}


@router.get("/weather")
def weather() -> dict[str, Any]:
    return _get_weather()


@router.post("/order-metadata", status_code=status.HTTP_201_CREATED)
def save_order_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    decision_id = payload.get("decision_id")
    if not decision_id:
        raise HTTPException(status_code=400, detail="decision_id is required")

    metadata_path = _DATA_DIR / "order_metadata.json"
    metadata = _load_json(metadata_path) if metadata_path.exists() else {}
    record = dict(payload)
    record.setdefault("provenance", "sample")
    metadata[str(decision_id)] = record
    write_purchasing_fixture(metadata_path, metadata)
    return {"decision_id": str(decision_id), "metadata": record}


@router.get("/order-metadata")
def get_order_metadata() -> dict[str, Any]:
    return _load_json(_DATA_DIR / "order_metadata.json")


@router.get("/analytics")
def analytics() -> dict[str, Any]:
    return _load_data_json(
        "analytics_cache.json",
        {
            "source": "default",
            "contrast_card": {},
            "counterfactual": {},
            "category_accuracy": {},
            "day_of_week": {},
            "event_impact": {},
            "waste_cost_analysis": {},
            "ae_impact": {},
            "portfolio_summary": {},
        },
    )


@router.get("/similar")
def similar_orders(
    category: str,
    expected_demand: float,
    day_of_week: float,
    weather_forecast: float,
    event_flag: float,
    historical_waste: float,
    supplier_lead_time: float,
    price_memory_index: float = 0.5,
    n: int = 5,
) -> dict[str, Any]:
    seed = _load_data_json("purchasing_seed_v2.json", [])
    if not isinstance(seed, list):
        return {"similar": [], "count": 0}

    query_vector = [
        expected_demand,
        day_of_week,
        weather_forecast,
        event_flag,
        historical_waste,
        supplier_lead_time,
        price_memory_index,
    ]
    if len(query_vector) != len(_FACTOR_NAMES):
        return {"similar": [], "count": 0}
    results = []
    for order in seed:
        if category and order.get("category") != category:
            continue
        order_vector = _order_vector(order)
        similarity = _cosine_similarity(query_vector, order_vector)
        if similarity <= 0.85:
            continue
        results.append(
            {
                "order_id": order.get("order_id"),
                "item": order.get("item"),
                "category": order.get("category"),
                "day_of_week": order.get("day_of_week"),
                "is_event_day": order.get("is_event_day"),
                "quantity_lbs": order.get("quantity_lbs"),
                "waste_pct": order.get("waste_pct"),
                "stockout_occurred": order.get("stockout_occurred"),
                "is_correct": order.get("is_correct"),
                "similarity": round(similarity, 4),
            }
        )

    results.sort(key=lambda row: row["similarity"], reverse=True)
    return {"similar": results[:n], "count": len(results)}


@router.get("/item/{name}/profile")
def item_profile(name: str) -> dict[str, Any]:
    key = _item_key(name)
    catalog = items()
    item = next(
        (
            row
            for row in catalog
            if row.get("name") == key or _item_key(str(row.get("display_name", ""))) == key
        ),
        None,
    )
    if item is None:
        return {"error": "Item not found", "name": name}

    waste_payload = _load_data_json("waste_history.json", {})
    waste_values = waste_payload.get(item["name"], [])
    waste_avg = round(sum(waste_values) / len(waste_values), 4) if waste_values else None
    ae_rules = [rule for rule in _evolution_variants() if _rule_matches_item(rule, item)]
    return {
        "item": item,
        "waste_history": waste_values,
        "waste_avg": waste_avg,
        "waste_trend": _waste_trend(waste_values),
        "ae_rules": ae_rules,
        "ae_managed": bool(ae_rules),
    }
