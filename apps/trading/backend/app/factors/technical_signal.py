"""Technical signal factor computer."""

from __future__ import annotations

from typing import Any

from app.factors.base import clamp, mean_or_neutral


class TechnicalSignalFactor:
    factor_name = "position_sizing"
    factor_index = 2

    def compute(self, event: object) -> float:
        if not isinstance(event, dict):
            return 0.5

        components: list[float] = []
        direction = str(event.get("entry_direction", "long")).lower()

        tagged_signals = event.get("tagged_signals")
        if isinstance(tagged_signals, list) and tagged_signals:
            confirmed = sum(
                1
                for signal in tagged_signals
                if isinstance(signal, dict) and bool(signal.get("confirmed"))
            )
            components.append(confirmed / len(tagged_signals))

        if "rsi_at_entry" in event:
            components.append(_rsi_score(event.get("rsi_at_entry"), direction))

        if "macd_signal" in event:
            components.append(_macd_score(event.get("macd_signal"), direction))

        if "price_vs_sma" in event:
            components.append(_sma_score(event.get("price_vs_sma"), direction))

        return mean_or_neutral(components)


def _rsi_score(value: Any, direction: str) -> float:
    try:
        rsi = float(value)
    except (TypeError, ValueError):
        return 0.5
    if direction == "short":
        if rsi > 70:
            return 0.9
        if rsi > 50:
            return 0.7
        if rsi > 30:
            return 0.5
        return 0.2
    if rsi < 30:
        return 0.9
    if rsi < 50:
        return 0.7
    if rsi < 70:
        return 0.5
    return 0.2


def _macd_score(value: Any, direction: str) -> float:
    signal = str(value or "neutral").lower()
    if signal == "neutral":
        return 0.5
    if (direction == "short" and signal == "bearish") or (
        direction != "short" and signal == "bullish"
    ):
        return 1.0
    return 0.1


def _sma_score(value: Any, direction: str) -> float:
    try:
        price_vs_sma = float(value)
    except (TypeError, ValueError):
        return 0.5
    if direction == "short":
        inverted = 1.0 / max(price_vs_sma, 0.8)
        return clamp(min(inverted, 1.25) / 1.25)
    clipped = min(max(price_vs_sma, 0.8), 1.2)
    return clamp(clipped / 1.2)
