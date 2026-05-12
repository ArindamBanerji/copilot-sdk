"""Reward computation protocols and scaling helpers."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class RewardFunction(Protocol):
    """Domain reward contract used by optional RL components."""

    def compute(
        self,
        recommended_action: str,
        actual_action: str,
        outcome: dict[str, Any],
    ) -> float:
        ...


class RewardComputer:
    """Apply SDK-level clipping and asymmetric penalty scaling."""

    def __init__(self, reward_function: RewardFunction, penalty_ratio: float) -> None:
        self._reward_function = reward_function
        self._penalty_ratio = _positive_penalty_ratio(penalty_ratio)

    @property
    def penalty_ratio(self) -> float:
        return self._penalty_ratio

    def compute_reward(
        self,
        recommended_action: str,
        actual_action: str,
        outcome: dict[str, Any] | None = None,
    ) -> float:
        raw = float(self._reward_function.compute(
            recommended_action,
            actual_action,
            outcome or {},
        ))
        clipped = _clamp(raw, -1.0, 1.0)
        if clipped < 0:
            return clipped * self._penalty_ratio
        return clipped


def _positive_penalty_ratio(value: float) -> float:
    try:
        penalty = float(value)
    except (TypeError, ValueError):
        return 1.0
    if penalty <= 0:
        return 1.0
    return penalty


def _clamp(value: float, lower: float = -1.0, upper: float = 1.0) -> float:
    return max(lower, min(float(value), upper))
