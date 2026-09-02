"""Trading reward adapter for risk-adjusted performance outcomes."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from copilot_sdk.rl.reward_functions import PnLRewardFunction


class TradingReward(PnLRewardFunction):
    """Compute risk-adjusted P&L relative to the expected maximum."""

    def compute(
        self,
        recommended_action: str,
        actual_action: str,
        outcome: Mapping[str, Any],
    ) -> float:
        del recommended_action, actual_action
        risk_adjusted = _number(outcome.get("risk_adjusted_pnl"))
        if "risk_adjusted_pnl" not in outcome:
            if "pnl" in outcome or "realized_pnl" in outcome:
                risk_adjusted = _number(
                    outcome.get("pnl", outcome.get("realized_pnl"))
                )
            else:
                risk_adjusted = _number(outcome.get("pnl_bps")) / 100.0
        maximum = _number(outcome.get("max_expected"))
        if maximum <= 0.0:
            return _clamp(risk_adjusted) if "pnl_bps" in outcome else 0.0
        return _clamp(risk_adjusted / maximum)

    def reward_range(self) -> tuple[float, float]:
        return (0.0, 1.0)


def _number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _clamp(value: float) -> float:
    return max(0.0, min(float(value), 1.0))
