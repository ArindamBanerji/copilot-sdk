"""Cached purchasing context endpoints."""

from __future__ import annotations

import json
import math
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status

from copilot_sdk.scoring.verification.weather import get_weather_factor


router = APIRouter(tags=["context"])
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


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _item_key(item: str) -> str:
    return item.strip().lower().replace(" ", "_")


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


def _order_vector(order: dict[str, Any]) -> list[float]:
    return [
        float(order.get("expected_demand", 0.0)),
        float(order.get("day_of_week_factor", 0.0)),
        float(order.get("weather_forecast", 0.0)),
        float(order.get("event_flag", 0.0)),
        float(order.get("historical_waste", 0.0)),
        float(order.get("supplier_lead_time", 0.0)),
        float(order.get("price_memory_index", 0.5)),
    ]


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
    metadata[str(decision_id)] = record
    _write_json(metadata_path, metadata)
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
    evolution_payload = _load_data_json("evolution_fixtures.json", {"variants": []})
    variants = evolution_payload.get("variants", [])
    ae_rules = [rule for rule in variants if _rule_matches_item(rule, item)]
    return {
        "item": item,
        "waste_history": waste_values,
        "waste_avg": waste_avg,
        "waste_trend": _waste_trend(waste_values),
        "ae_rules": ae_rules,
        "ae_managed": bool(ae_rules),
    }
