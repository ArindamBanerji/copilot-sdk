"""Trading decision-context factor computer."""

from __future__ import annotations

from app.factors.base import clamp


class EmotionalIndicatorFactor:
    factor_name = "emotional_indicator"
    factor_index = 5

    def compute(self, event: object) -> float:
        ctx = event if isinstance(event, dict) else {}
        if not ctx:
            return 0.5

        score = 1.0
        minutes_since_last = _number(ctx.get("minutes_since_last_trade"), 999.0)
        last_was_loss = bool(ctx.get("last_trade_was_loss", False))
        consecutive_wins = _number(ctx.get("consecutive_wins"), 0.0)
        sizing_vs_avg = _number(ctx.get("size_vs_rolling_avg"), 1.0)

        if last_was_loss and minutes_since_last < 30:
            score -= 0.4
        if consecutive_wins >= 3 and sizing_vs_avg > 1.3:
            score -= 0.3
        if bool(ctx.get("entry_at_day_extreme", False)):
            score -= 0.2

        return clamp(score)


def _number(value: object, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
