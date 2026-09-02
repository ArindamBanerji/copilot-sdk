"""Domain-injected, bounded reward computation and GraphStore persistence."""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable
from uuid import uuid4

from copilot_sdk.rl.types import RewardResult


@runtime_checkable
class DomainRewardFunction(Protocol):
    """Protocol implemented by a copilot's domain reward function."""

    def compute(
        self,
        recommended_action: str,
        actual_action: str,
        outcome: Mapping[str, Any],
    ) -> float:
        ...


RewardFunction = DomainRewardFunction


class RewardComputer:
    """Normalize domain rewards while preserving binary rewards as a special case."""

    def __init__(
        self,
        reward_function: DomainRewardFunction,
        penalty_ratio: float = 1.0,
        domain: str = "unknown",
    ) -> None:
        if penalty_ratio <= 0:
            raise ValueError("penalty_ratio must be positive")
        self._reward_function = reward_function
        self._penalty_ratio = float(penalty_ratio)
        self._domain = str(domain)

    @property
    def penalty_ratio(self) -> float:
        return self._penalty_ratio

    def compute(
        self,
        recommended_action: str,
        actual_action: str,
        outcome: Mapping[str, Any] | None = None,
        *,
        decision_id: str | None = None,
    ) -> RewardResult:
        raw = float(
            self._reward_function.compute(
                recommended_action, actual_action, outcome or {}
            )
        )
        reward = _clamp(raw, 0.0, 1.0)
        binary = 1.0 if reward >= 1.0 else 0.0
        return RewardResult(
            reward=reward,
            binary_reward=binary,
            domain=self._domain,
            decision_id=decision_id,
            breakdown={"raw": raw, "binary": binary},
        )

    def compute_reward(
        self,
        recommended_action: str,
        actual_action: str,
        outcome: dict[str, Any] | None = None,
    ) -> float:
        """Compatibility scalar API for callers that only need the reward."""
        raw = float(
            self._reward_function.compute(
                recommended_action, actual_action, outcome or {}
            )
        )
        clipped = _clamp(raw, -1.0, 1.0)
        return clipped * self._penalty_ratio if clipped < 0.0 else clipped

    def persist(
        self,
        graph_store: Any,
        result: RewardResult,
        *,
        decision_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> str:
        """Persist a reward through the GraphStore ledger contract."""
        saver = getattr(graph_store, "save_ledger", None)
        if not callable(saver):
            raise RuntimeError("GraphStore does not expose save_ledger")
        entry_id = f"rl-reward:{result.domain}:{decision_id or result.decision_id or uuid4().hex}"
        state = {
            "entry_id": entry_id,
            "decision_id": decision_id or result.decision_id,
            "reward": result.reward,
            "binary_reward": result.binary_reward,
            "domain": result.domain,
            "breakdown": dict(result.breakdown),
            "metadata": dict(metadata or {}),
        }
        saver(result.domain, entry_id, state)
        return entry_id


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(float(value), upper))
