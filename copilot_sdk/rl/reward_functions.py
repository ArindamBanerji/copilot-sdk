"""Built-in reward functions for common copilot feedback patterns."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class BinaryRewardFunction:
    """Return +1 for matching actions and -1 otherwise."""

    def compute(
        self,
        recommended_action: str,
        actual_action: str,
        outcome: Mapping[str, Any],
    ) -> float:
        del outcome
        return 1.0 if actual_action == recommended_action else -1.0


class GradedFinancialRewardFunction:
    """Reward recovered value, or penalize slow overrides."""

    def compute(
        self,
        recommended_action: str,
        actual_action: str,
        outcome: Mapping[str, Any],
    ) -> float:
        if actual_action == recommended_action:
            recovered = _number(outcome.get("recovered"))
            at_risk = max(_number(outcome.get("at_risk")), 1.0)
            return _clamp(recovered / at_risk, -1.0, 1.0)

        cycle_time_hours = _number(outcome.get("cycle_time_hours"))
        return -min(1.0, max(cycle_time_hours, 0.0) / 24.0)


class PnLRewardFunction:
    """Scale basis-point P&L into the reward interval."""

    def compute(
        self,
        recommended_action: str,
        actual_action: str,
        outcome: Mapping[str, Any],
    ) -> float:
        del recommended_action, actual_action
        return _clamp(_number(outcome.get("pnl_bps")) / 100.0, -1.0, 1.0)


class WasteReductionRewardFunction:
    """Reward waste reductions, where negative delta means lower waste."""

    def compute(
        self,
        recommended_action: str,
        actual_action: str,
        outcome: Mapping[str, Any],
    ) -> float:
        del recommended_action, actual_action
        waste_delta = _number(outcome.get("waste_pct_change"))
        return _clamp(-waste_delta / 10.0, -1.0, 1.0)


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value: float, lower: float = -1.0, upper: float = 1.0) -> float:
    return max(lower, min(float(value), upper))
