"""Conviction factor computer."""

from __future__ import annotations

from typing import Any

from app.factors.base import clamp, mean_or_neutral


class ConvictionFactor:
    factor_name = "signal_alignment"
    factor_index = 0

    def compute(self, event: object) -> float:
        if not isinstance(event, dict):
            return 0.5

        components: list[float] = []
        tagged_signals = event.get("tagged_signals")
        if isinstance(tagged_signals, list) and tagged_signals:
            confirmed = sum(
                1
                for signal in tagged_signals
                if isinstance(signal, dict) and bool(signal.get("confirmed"))
            )
            components.append(confirmed / len(tagged_signals))

        if "has_trade_plan" in event:
            components.append(1.0 if bool(event.get("has_trade_plan")) else 0.3)

        if "position_conviction" in event:
            components.append(clamp(event.get("position_conviction")))

        if "size_vs_rolling_avg" in event:
            components.append(_sizing_score(event.get("size_vs_rolling_avg")))

        return mean_or_neutral(components)


def _sizing_score(value: Any) -> float:
    try:
        size = float(value)
    except (TypeError, ValueError):
        return 0.5
    if 0.8 <= size <= 1.5:
        return 0.8
    if size > 1.5:
        return 0.5
    return 0.6
