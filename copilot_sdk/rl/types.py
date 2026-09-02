"""Shared value types for domain-neutral reinforcement learning."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RewardResult:
    """A bounded reward and the evidence used to compute it."""

    reward: float
    binary_reward: float
    domain: str
    decision_id: str | None = None
    breakdown: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class CreditAssignment:
    """Reward credit assigned to prior decisions or factors."""

    target_id: str
    credit: float
    delay: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExplorationDecision:
    """Selected action plus the safety state that bounded exploration."""

    action: int
    explored: bool
    epsilon: float
    conservation_status: str
