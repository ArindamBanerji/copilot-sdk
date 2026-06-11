"""Trading timing-quality factor computer."""

from __future__ import annotations

from app.factors.base import clamp


class TimingQualityFactor:
    factor_name = "timing_quality"
    factor_index = 3

    def compute(self, event: object) -> float:
        ctx = event if isinstance(event, dict) else {}
        if not ctx:
            return 0.5

        score = 1.0
        entry_delay = _number(ctx.get("entry_delay_minutes"), 0.0)
        if entry_delay > 30:
            score -= 0.3
        elif entry_delay > 10:
            score -= 0.1

        hold_pct = _number(ctx.get("hold_time_vs_plan_pct"), 1.0)
        if hold_pct < 0.5:
            score -= 0.3
        elif hold_pct < 0.8:
            score -= 0.1

        tod_accuracy = _optional_number(ctx.get("time_of_day_accuracy"))
        if tod_accuracy is not None and tod_accuracy < 0.40:
            score -= 0.2

        return clamp(score)


def _number(value: object, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _optional_number(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
