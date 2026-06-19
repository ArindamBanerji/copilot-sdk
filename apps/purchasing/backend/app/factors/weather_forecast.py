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


def _clamp(value: Any, default: float = 0.5) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, numeric))


def compute(context: dict) -> float:
    """Return weather demand score; missing data is neutral."""
    if not isinstance(context, dict):
        return 0.5
    if "weather_score" in context:
        return _clamp(context.get("weather_score"))
    weather = context.get("weather")
    if weather is None:
        return 0.5
    return WEATHER_SCORES.get(str(weather).strip().lower(), 0.5)
