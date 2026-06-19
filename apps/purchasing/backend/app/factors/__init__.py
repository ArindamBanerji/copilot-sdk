"""Purchasing factor computers."""

from __future__ import annotations

from collections.abc import Callable

from .day_of_week import compute as day_of_week_compute
from .event_flag import compute as event_flag_compute
from .expected_demand import compute as expected_demand_compute
from .historical_waste import compute as historical_waste_compute
from .price_memory_index import compute as price_memory_index_compute
from .supplier_lead_time import compute as supplier_lead_time_compute
from .weather_forecast import compute as weather_forecast_compute

PURCHASING_FACTOR_COMPUTERS: dict[str, Callable[[dict], float]] = {
    "expected_demand": expected_demand_compute,
    "day_of_week": day_of_week_compute,
    "weather_forecast": weather_forecast_compute,
    "event_flag": event_flag_compute,
    "historical_waste": historical_waste_compute,
    "supplier_lead_time": supplier_lead_time_compute,
    "price_memory_index": price_memory_index_compute,
}

ALL_FACTOR_NAMES = list(PURCHASING_FACTOR_COMPUTERS.keys())


def _clamp(value: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.5
    return max(0.0, min(1.0, numeric))


def compute_factors(context: dict) -> dict[str, float]:
    """Compute all Purchasing factor scores from kitchen/order context."""
    payload = context if isinstance(context, dict) else {}
    return {
        name: _clamp(fn(payload))
        for name, fn in PURCHASING_FACTOR_COMPUTERS.items()
    }


__all__ = [
    "ALL_FACTOR_NAMES",
    "PURCHASING_FACTOR_COMPUTERS",
    "compute_factors",
]
