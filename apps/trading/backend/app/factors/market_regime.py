"""Market regime factor computer."""

from __future__ import annotations

from typing import Any

from app.factors.base import clamp


def classify_regime(vix: float, trend_strength: float = 20.0) -> str:
    if vix > 30:
        return "volatile"
    if vix > 20:
        return "ranging"
    if trend_strength > 25:
        return "trending"
    return "ranging"


class MarketRegimeFactor:
    factor_name = "emotional_indicator"
    factor_index = 5

    def compute(self, event: object) -> float:
        if not isinstance(event, dict):
            return 0.5

        regime = event.get("current_regime")
        if regime is None:
            if "vix_at_entry" not in event:
                return 0.5
            try:
                vix = float(event.get("vix_at_entry"))
                trend_strength = float(event.get("trend_strength", 20.0))
            except (TypeError, ValueError):
                return 0.5
            regime = classify_regime(vix, trend_strength)

        accuracy = event.get("regime_accuracy", {})
        if not isinstance(accuracy, dict):
            return 0.5
        return clamp(accuracy.get(str(regime), 0.5))
