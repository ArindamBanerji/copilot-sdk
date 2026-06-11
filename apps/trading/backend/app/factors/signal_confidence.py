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

        dk_score = _dk_weight_score(ctx)
        if dk_score is not None:
            return dk_score

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


def _dk_weight_score(ctx: dict[str, Any]) -> float | None:
    weights_by_category = ctx.get("dk_weights_by_category")
    tagged = ctx.get("tagged_signal_indices")
    if not isinstance(weights_by_category, dict) or not isinstance(tagged, list):
        return None

    category = ctx.get("category_index", 0)
    weights = weights_by_category.get(category)
    if weights is None:
        weights = weights_by_category.get(str(category))
    if not isinstance(weights, list) or not weights:
        return 0.5

    relevant: list[float] = []
    for index in tagged:
        try:
            signal_index = int(index)
        except (TypeError, ValueError):
            continue
        if 0 <= signal_index < len(weights):
            relevant.append(clamp(weights[signal_index]))
    return mean_or_neutral(relevant)
