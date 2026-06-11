"""Trading risk/reward factor computer."""

from __future__ import annotations

from app.factors.base import clamp


class RiskRewardActualFactor:
    factor_name = "risk_reward_actual"
    factor_index = 4

    def compute(self, event: object) -> float:
        ctx = event if isinstance(event, dict) else {}
        if not ctx:
            return 0.5

        planned_rr = _number(ctx.get("planned_risk_reward"))
        actual_rr = _number(ctx.get("actual_risk_reward", ctx.get("r_multiple")))

        if actual_rr is None:
            return 0.5
        if planned_rr is None:
            return clamp((actual_rr + 1.0) / 3.0)
        if planned_rr <= 0:
            return 0.5

        ratio = actual_rr / planned_rr
        return clamp((ratio + 0.5) / 2.0)


def _number(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
