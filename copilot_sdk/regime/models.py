"""Public, domain-neutral regime value objects."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class RegimeState:
    """A classified operating state and the indicators that produced it."""

    regime: str
    confidence: float
    indicators: dict[str, float]
    timestamp: str

    @classmethod
    def create(
        cls,
        regime: str,
        confidence: float,
        indicators: dict[str, float],
        timestamp: str | None = None,
    ) -> "RegimeState":
        return cls(
            regime=str(regime),
            confidence=round(float(confidence), 4),
            indicators={key: round(float(value), 4) for key, value in indicators.items()},
            timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation for API and scoring contexts."""
        return asdict(self)
