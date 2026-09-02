"""DataOps reward adapter for resolution and blast-radius improvements."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from copilot_sdk.rl.reward_functions import GradedFinancialRewardFunction


class DataOpsReward(GradedFinancialRewardFunction):
    """Compute resolution-time improvement times blast-radius reduction."""

    def compute(
        self,
        recommended_action: str,
        actual_action: str,
        outcome: Mapping[str, Any],
    ) -> float:
        del recommended_action, actual_action
        time_improvement = _improvement(
            outcome,
            "resolution_time_improvement",
            "resolution_time_baseline",
            "resolution_time",
        )
        blast_reduction = _improvement(
            outcome,
            "blast_radius_reduction",
            "blast_radius_baseline",
            "blast_radius",
        )
        return _clamp(time_improvement) * _clamp(blast_reduction)

    def reward_range(self) -> tuple[float, float]:
        return (0.0, 1.0)


def _improvement(
    outcome: Mapping[str, Any], direct_key: str, baseline_key: str, current_key: str
) -> float:
    if direct_key in outcome:
        return _number(outcome.get(direct_key))
    baseline = _number(outcome.get(baseline_key))
    if baseline <= 0.0:
        return 0.0
    current = _number(outcome.get(current_key))
    return (baseline - current) / baseline


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value: float) -> float:
    return max(0.0, min(float(value), 1.0))
