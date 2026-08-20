"""Regime-conditioned conservation, learning, and centroid telemetry."""

from __future__ import annotations

from dataclasses import dataclass
import math
from threading import RLock
from typing import Any, Iterable, Mapping


def _regime_name(regime: Any) -> str:
    return str(regime or "").strip().lower()


@dataclass(frozen=True)
class RegimeParameters:
    """Runtime values selected for one scoring/learning regime."""

    regime: str
    theta_min: float
    penalty_ratio: float
    eta: float

    def to_dict(self) -> dict[str, float | str]:
        return {"regime": self.regime, "theta_min": self.theta_min,
                "penalty_ratio": self.penalty_ratio, "eta": self.eta}


class RegimeConservation:
    """Adjust conservation sensitivity without changing its base formula."""

    def __init__(self, *, absolute_minimum: float = 0.1) -> None:
        self.absolute_minimum = max(0.0, float(absolute_minimum))

    def adjust_theta_min(self, base_theta_min: float, regime: str) -> float:
        base = _finite_nonnegative(base_theta_min)
        if base is None:
            return self.absolute_minimum
        multiplier = {"volatile": 1.5, "calm": 0.8}.get(_regime_name(regime), 1.0)
        return max(self.absolute_minimum, base * multiplier)

    def adjust_penalty_ratio(self, base_ratio: float, regime: str) -> float:
        base = _finite_nonnegative(base_ratio)
        if base is None:
            return 0.0
        multiplier = {"volatile": 2.0, "calm": 0.5}.get(_regime_name(regime), 1.0)
        return base * multiplier


class RegimeLearningRate:
    """Select a conservative learning-rate multiplier for a regime."""

    def adjust_eta(self, base_eta: float, regime: str) -> float:
        base = _finite_nonnegative(base_eta)
        if base is None:
            return 0.0
        multiplier = {"volatile": 0.5, "calm": 1.5}.get(_regime_name(regime), 1.0)
        return base * multiplier


class PerRegimeCentroidTracker:
    """Track centroid movement independently for each observed regime."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._stats: dict[str, dict[str, float | int]] = {}

    def record(self, regime: str, before: Any, after: Any) -> dict[str, float | int | str]:
        movement = _distance(_flatten(before), _flatten(after))
        key = _regime_name(regime) or "unknown"
        with self._lock:
            current = self._stats.setdefault(
                key, {"updates": 0, "total_movement": 0.0, "last_movement": 0.0}
            )
            current["updates"] = int(current["updates"]) + 1
            current["total_movement"] = float(current["total_movement"]) + movement
            current["last_movement"] = movement
            return self._format(key, current)

    def movement_rate(self, regime: str) -> float:
        return float(self.get(regime)["mean_movement"])

    def convergence_speed(self, regime: str) -> float:
        return 1.0 / (1.0 + self.movement_rate(regime))

    def get(self, regime: str) -> dict[str, float | int | str]:
        key = _regime_name(regime) or "unknown"
        with self._lock:
            current = self._stats.get(key)
            if current is None:
                current = {"updates": 0, "total_movement": 0.0, "last_movement": 0.0}
            return self._format(key, current)

    def snapshot(self) -> dict[str, dict[str, float | int | str]]:
        with self._lock:
            return {key: self._format(key, value) for key, value in self._stats.items()}

    def _format(self, key: str, stats: Mapping[str, float | int]) -> dict[str, float | int | str]:
        updates = int(stats["updates"])
        total = float(stats["total_movement"])
        mean = total / updates if updates else 0.0
        return {"regime": key, "updates": updates, "total_movement": total,
                "last_movement": float(stats["last_movement"]),
                "mean_movement": mean, "convergence_speed": 1.0 / (1.0 + mean)}


def _finite_nonnegative(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, parsed) if math.isfinite(parsed) else None


def _flatten(value: Any) -> list[float]:
    if isinstance(value, (str, bytes)) or value is None:
        return [_finite_nonnegative(value) or 0.0]
    if isinstance(value, Iterable):
        flattened: list[float] = []
        for item in value:
            flattened.extend(_flatten(item))
        return flattened
    return [_finite_nonnegative(value) or 0.0]


def _distance(before: list[float], after: list[float]) -> float:
    length = max(len(before), len(after))
    left = before + [0.0] * (length - len(before))
    right = after + [0.0] * (length - len(after))
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(left, right)))
