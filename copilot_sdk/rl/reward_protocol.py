"""Mapping-based RL contract; the legacy ``rl.RewardFunction`` stays intact.

Domain functions are pure: they interpret evidence, never select actions or
write learning state. Normalization is explicit, finite and range-checked.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol, cast, runtime_checkable

from .outcome_receipt import OutcomeReceipt
from .reward import DomainRewardFunction as LegacyRewardFunction


@runtime_checkable
class RewardFunction(Protocol):
    def compute_reward(self, decision: Mapping[str, Any], outcome: Mapping[str, Any]) -> float:
        """Return a raw reward using only the supplied decision and evidence."""
        ...

    def reward_range(self) -> tuple[float, float]:
        """Return the finite inclusive raw range, with lower < upper."""
        ...


def normalize_reward(raw: float, reward_range: tuple[float, float]) -> float:
    lower, upper = map(float, reward_range)
    raw = float(raw)
    if not all(math.isfinite(value) for value in (lower, upper, raw)):
        raise ValueError("reward and range must be finite")
    if lower >= upper or not lower <= raw <= upper:
        raise ValueError("reward must be inside an ordered, nonempty range")
    # Scaling first avoids overflow for otherwise valid extreme finite ranges.
    scale = max(abs(lower), abs(upper), 1.0)
    return (raw / scale - lower / scale) / (upper / scale - lower / scale)


@dataclass(frozen=True)
class LegacyRewardAdapter:
    """Adapt SOC/S2P-style compute(recommended, actual, outcome), explicitly."""

    function: LegacyRewardFunction
    raw_range: tuple[float, float] = (0.0, 1.0)

    def __post_init__(self) -> None:
        normalize_reward(self.raw_range[0], self.raw_range)

    def compute_reward(self, decision: Mapping[str, Any], outcome: Mapping[str, Any]) -> float:
        recommended = decision["recommended_action"]
        actual = outcome["actual_action"]
        if not isinstance(recommended, str) or not recommended.strip():
            raise ValueError("recommended_action is required")
        if not isinstance(actual, str) or not actual.strip():
            raise ValueError("actual_action is required")
        return cast(float, self.function.compute(recommended, actual, outcome))

    def reward_range(self) -> tuple[float, float]:
        return self.raw_range


@dataclass(frozen=True)
class ComputedReward:
    raw: float
    reward: float
    binary_reward: float
    reward_range: tuple[float, float]
    formula_version: str


def compute_reward(
    function: RewardFunction,
    decision: Mapping[str, Any],
    outcome: Mapping[str, Any],
    *,
    formula_version: str,
) -> ComputedReward:
    """Call a domain function once; validate without silently clipping errors."""
    if not isinstance(formula_version, str) or not formula_version.strip():
        raise ValueError("formula_version is required")
    lower, upper = function.reward_range()
    bounds = (float(lower), float(upper))
    raw = float(function.compute_reward(decision, outcome))
    reward = normalize_reward(raw, bounds)
    return ComputedReward(raw, reward, float(reward == 1.0), bounds, formula_version)


__all__ = ["RewardFunction", "OutcomeReceipt", "LegacyRewardAdapter", "ComputedReward", "compute_reward"]
