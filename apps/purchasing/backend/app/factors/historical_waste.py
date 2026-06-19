"""Purchasing historical-waste factor computer.

Kitchen meaning: waste rate for the item or category.
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
    """Return waste pressure where 20 percent or more waste is worst."""
    if not isinstance(context, dict) or "waste_pct" not in context:
        return 0.5
    try:
        waste_pct = float(context.get("waste_pct"))
    except (TypeError, ValueError):
        return 0.5
    return _clamp(waste_pct / 0.20)
