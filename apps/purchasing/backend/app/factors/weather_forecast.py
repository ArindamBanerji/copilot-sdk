"""Purchasing weather-forecast factor computer.

Kitchen meaning: weather pressure on expected covers.
"""

from __future__ import annotations

from typing import Any

WEATHER_SCORES = {
    "sunny": 0.9,
    "clear": 0.9,
    "cloudy": 0.6,
    "overcast": 0.6,
    "rain": 0.3,
    "rainy": 0.3,
    "severe": 0.1,
    "storm": 0.1,
    "stormy": 0.1,
}

_CATEGORY_WEATHER_SCORES = {
    "storm": {
        "seafood": 0.1,
        "protein": 0.2,
        "produce": 0.2,
        "dairy": 0.4,
        "dry_goods": 0.9,
        "beverages": 0.8,
    },
    "heat": {
        "dairy": 0.3,
        "produce": 0.4,
        "seafood": 0.4,
        "protein": 0.5,
        "beverages": 0.6,
        "dry_goods": 0.9,
    },
    "rain": {
        "produce": 0.5,
        "seafood": 0.6,
        "protein": 0.7,
        "dairy": 0.7,
        "beverages": 0.8,
        "dry_goods": 0.9,
    },
    "normal": {
        "produce": 0.8,
        "seafood": 0.8,
        "protein": 0.8,
        "dairy": 0.8,
        "beverages": 0.8,
        "dry_goods": 0.9,
    },
}


def _clamp(value: Any, default: float = 0.5) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, numeric))


def compute_weather_impact(weather_data: dict, category: str) -> float:
    """Return category-specific weather score; missing data is neutral."""
    if not isinstance(weather_data, dict):
        return 0.5
    category_key = str(category or "").strip().lower() or "dry_goods"
    condition = _weather_condition(weather_data)
    category_scores = _CATEGORY_WEATHER_SCORES.get(condition, _CATEGORY_WEATHER_SCORES["normal"])
    return _clamp(category_scores.get(category_key, category_scores.get("dry_goods", 0.5)))


def compute(context: dict) -> float:
    """Return weather demand score; missing data is neutral."""
    if not isinstance(context, dict):
        return 0.5
    if "weather_score" in context:
        return _clamp(context.get("weather_score"))
    category = context.get("category")
    if category is not None:
        return compute_weather_impact(context, str(category))
    weather = context.get("weather")
    if weather is None:
        return 0.5
    return WEATHER_SCORES.get(str(weather).strip().lower(), 0.5)


def _weather_condition(weather_data: dict) -> str:
    raw = str(
        weather_data.get("condition")
        or weather_data.get("weather")
        or weather_data.get("forecast")
        or ""
    ).strip().lower()
    precipitation = _number(
        weather_data.get("precipitation_mm")
        or weather_data.get("precipitation")
        or weather_data.get("precipitation_prob")
        or weather_data.get("precipitationProb"),
        0.0,
    )
    wind = _number(
        weather_data.get("wind_speed_max")
        or weather_data.get("wind_mph")
        or weather_data.get("windMph"),
        0.0,
    )
    temperature = _number(
        weather_data.get("temperature_f")
        or weather_data.get("temperatureF"),
        70.0,
    )
    if "storm" in raw or precipitation >= 20 or wind >= 45:
        return "storm"
    if "heat" in raw or "hot" in raw or temperature >= 90:
        return "heat"
    if "rain" in raw or precipitation >= 5:
        return "rain"
    if raw in WEATHER_SCORES and WEATHER_SCORES[raw] <= 0.3:
        return "rain"
    return "normal"


def _number(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback
