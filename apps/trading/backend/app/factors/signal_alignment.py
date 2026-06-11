"""Trading signal-alignment factor computer."""

from __future__ import annotations

from typing import Any

from app.factors.base import clamp, mean_or_neutral
from app.factors.technical_signal import TechnicalSignalFactor


class SignalAlignmentFactor:
    factor_name = "signal_alignment"
    factor_index = 0

    def compute(self, event: object) -> float:
        ctx = event if isinstance(event, dict) else {}
        if not ctx:
            return 0.5

        components: list[float] = []
        tagged_signals = ctx.get("tagged_signals")
        if isinstance(tagged_signals, list) and tagged_signals:
            confirmed = sum(
                1
                for signal in tagged_signals
                if isinstance(signal, dict) and bool(signal.get("confirmed"))
            )
            components.append(confirmed / len(tagged_signals))

        indicator_score = TechnicalSignalFactor().compute(ctx)
        if _has_indicator_context(ctx):
            components.append(indicator_score)

        return mean_or_neutral(components)


def _has_indicator_context(ctx: dict[str, Any]) -> bool:
    return any(
        key in ctx
        for key in (
            "rsi_at_entry",
            "macd_signal",
            "price_vs_sma",
        )
    )
