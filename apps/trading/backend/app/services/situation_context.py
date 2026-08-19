"""Read-only market situation context for Trading scoring surfaces."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SituationContext:
    """The market context attached to a scoring observation.

    The classifier intentionally reports state and confidence only.  It does
    not produce a trade, allocation, or timing instruction.
    """

    regime: str
    confidence: float
    indicators: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def detect(
        cls,
        vix: float,
        adx: float,
        trend_strength: float | None = None,
    ) -> "SituationContext":
        vix_value = _finite(vix, 20.0)
        adx_value = _finite(adx, 20.0)
        trend_value = _finite(trend_strength, adx_value)

        if vix_value > 30.0:
            regime = "volatile"
            distance = vix_value - 30.0
        elif vix_value < 20.0 and trend_value > 25.0:
            regime = "trending"
            distance = min(20.0 - vix_value, trend_value - 25.0)
        elif vix_value < 15.0 and trend_value <= 20.0:
            regime = "calm"
            distance = min(15.0 - vix_value, 20.0 - trend_value)
        else:
            regime = "ranging"
            distance = min(abs(vix_value - 20.0), abs(trend_value - 25.0))

        confidence = round(min(1.0, max(0.05, distance / 10.0)), 4)
        return cls(
            regime=regime,
            confidence=confidence,
            indicators={
                "vix": round(vix_value, 4),
                "adx": round(adx_value, 4),
                "trend_strength": round(trend_value, 4),
            },
        )


def _finite(value: Any, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if number == number and abs(number) != float("inf") else default
