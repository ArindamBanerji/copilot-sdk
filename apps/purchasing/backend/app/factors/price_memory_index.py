"""Purchasing price-memory-index factor computer.

Kitchen meaning: whether supplier prices stay stable over time.
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
    """Return price stability from change count over tracked months."""
    if not isinstance(context, dict):
        return 0.5
    changes = context.get("price_change_count")
    months = context.get("months_tracked")
    if changes is None or months is None:
        return 0.5
    try:
        tracked = max(float(months), 1.0)
        return _clamp(1.0 - (float(changes) / tracked))
    except (TypeError, ValueError):
        return 0.5
