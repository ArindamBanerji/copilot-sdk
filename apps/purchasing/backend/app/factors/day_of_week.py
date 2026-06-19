"""Purchasing day-of-week factor computer.

Kitchen meaning: service-day demand pressure from the calendar.
"""

from __future__ import annotations

DAY_SCORES = {
    0: 0.3,
    1: 0.3,
    2: 0.4,
    3: 0.5,
    4: 0.7,
    5: 1.0,
    6: 0.6,
}


def compute(context: dict) -> float:
    """Return the day demand modifier; missing data is neutral."""
    if not isinstance(context, dict) or "day_of_week" not in context:
        return 0.5
    try:
        day = int(context.get("day_of_week"))
    except (TypeError, ValueError):
        return 0.5
    return DAY_SCORES.get(day, 0.5)
