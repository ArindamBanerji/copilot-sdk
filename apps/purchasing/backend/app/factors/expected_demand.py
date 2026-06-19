"""Purchasing expected-demand factor computer.

Kitchen meaning: how much supplier stock is needed relative to par.
"""

from __future__ import annotations

from typing import Any


def _clamp(value: Any, default: float = 0.5) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, numeric))


def compute(context: dict) -> float:
    """Return demand forecast divided by par level; missing data is neutral."""
    if not isinstance(context, dict):
        return 0.5
    forecast = context.get("forecast_demand")
    par_level = context.get("par_level")
    if forecast is None or par_level is None:
        return 0.5
    try:
        par = float(par_level)
        if par <= 0:
            return 0.5
        return _clamp(float(forecast) / par)
    except (TypeError, ValueError):
        return 0.5
