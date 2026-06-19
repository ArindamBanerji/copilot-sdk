"""Purchasing event-flag factor computer.

Kitchen meaning: catering, banquet, or special event demand.
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
    """Return event demand pressure; missing data is neutral."""
    if not isinstance(context, dict):
        return 0.5
    if "event_flag" in context:
        value = context.get("event_flag")
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        return _clamp(value)
    event_covers = context.get("event_covers")
    normal_covers = context.get("normal_covers")
    if event_covers is None or normal_covers is None:
        return 0.5
    try:
        normal = float(normal_covers)
        if normal <= 0:
            return 0.5
        return _clamp(float(event_covers) / normal)
    except (TypeError, ValueError):
        return 0.5
