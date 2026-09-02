"""Purchasing reward adapter for cost-impact outcomes."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from copilot_sdk.rl.reward_functions import WasteReductionRewardFunction


class PurchasingReward(WasteReductionRewardFunction):
    """Compute realized cost impact relative to the maximum opportunity."""

    def compute(
        self,
        recommended_action: str,
        actual_action: str,
        outcome: Mapping[str, Any],
    ) -> float:
        del recommended_action, actual_action
        maximum = _number(outcome.get("max_cost"))
        if maximum <= 0.0:
            return 0.0
        if "cost_impact" in outcome:
            impact = _number(outcome.get("cost_impact"))
        else:
            actual = _number(outcome.get("actual_cost"))
            optimal = _number(outcome.get("optimal_cost"))
            impact = maximum - abs(actual - optimal)
        return _clamp(impact / maximum)

    def reward_range(self) -> tuple[float, float]:
        return (0.0, 1.0)


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value: float) -> float:
    return max(0.0, min(float(value), 1.0))
