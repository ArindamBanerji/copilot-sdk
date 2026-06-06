"""Signal confidence factor computer."""

from __future__ import annotations

from typing import Any

from app.factors.base import clamp, mean_or_neutral


class SignalConfidenceFactor:
    factor_name = "signal_confidence"
    factor_index = 6

    def compute(self, event: object) -> float:
        ctx = event if isinstance(event, dict) else {}
        if not ctx:
            return 0.5

        components: list[float] = []

        if "factors_with_data" in ctx:
            components.append(_scaled_score(ctx.get("factors_with_data"), 10.0))

        if "category_accuracy" in ctx:
            components.append(clamp(ctx.get("category_accuracy")))

        if "similar_trade_count" in ctx:
            components.append(_scaled_score(ctx.get("similar_trade_count"), 100.0))

        if "novelty_distance" in ctx:
            components.append(_novelty_distance_score(ctx.get("novelty_distance")))

        return mean_or_neutral(components)


def _novelty_distance_score(value: Any) -> float:
    try:
        distance = float(value)
    except (TypeError, ValueError):
        return 0.5
    if distance <= 0.3:
        return 1.0
    if distance <= 0.6:
        return 0.7
    if distance <= 1.0:
        return 0.4
    return 0.1


def _scaled_score(value: Any, denominator: float) -> float:
    try:
        return clamp(float(value) / denominator)
    except (TypeError, ValueError):
        return 0.5
