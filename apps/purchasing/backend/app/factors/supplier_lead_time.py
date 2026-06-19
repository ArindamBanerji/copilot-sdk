"""Purchasing supplier-lead-time factor computer.

Kitchen meaning: how reliably supplier orders arrive soon enough.
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
    """Return delivery speed where same-day is best and 7+ days is worst."""
    if not isinstance(context, dict) or "lead_time_days" not in context:
        return 0.5
    try:
        return _clamp(1.0 - (float(context.get("lead_time_days")) / 7.0))
    except (TypeError, ValueError):
        return 0.5
