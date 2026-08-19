"""Read-only market situation context for Trading scoring surfaces."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from copilot_sdk.regime import RegimeDetector, RegimePolicy


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
        state = RegimeDetector(RegimePolicy()).detect({
            "vix": vix_value,
            "adx": adx_value,
            "trend_strength": trend_value,
        })
        return cls(
            regime=state.regime,
            confidence=state.confidence,
            indicators=state.indicators,
        )


def _finite(value: Any, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if number == number and abs(number) != float("inf") else default
