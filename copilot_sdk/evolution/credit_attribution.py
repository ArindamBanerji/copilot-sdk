"""Step-level credit attribution for multi-step evolution chains."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


HALF_LIFE = 30
CHAIN_DISCOUNT = 0.5


@dataclass(frozen=True)
class StepRecord:
    step_id: str
    step_type: str
    timestamp: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata or {}))


@dataclass(frozen=True)
class StepCredit:
    step_id: str
    credit: float
    decay_factor: float


class StepCreditAssigner:
    def __init__(self, half_life: int = HALF_LIFE, chain_discount: float = CHAIN_DISCOUNT) -> None:
        self.half_life = max(float(half_life), 1e-9)
        self.chain_discount = max(float(chain_discount), 0.0)

    def assign(self, chain: list[StepRecord], outcome_reward: float) -> list[StepCredit]:
        if not chain:
            return []

        newest_timestamp = max(float(step.timestamp) for step in chain)
        ordered_by_recency = sorted(
            enumerate(chain),
            key=lambda item: (float(item[1].timestamp), item[0]),
            reverse=True,
        )
        recency_rank = {index: rank for rank, (index, _) in enumerate(ordered_by_recency)}

        weights: list[float] = []
        decay_factors: list[float] = []
        for index, step in enumerate(chain):
            age = max(newest_timestamp - float(step.timestamp), 0.0)
            time_decay = 0.5 ** (age / self.half_life)
            chain_weight = self.chain_discount ** recency_rank[index]
            decay = time_decay * chain_weight
            decay_factors.append(decay)
            weights.append(decay)

        total = sum(weights)
        if total <= 0.0:
            weights = [1.0 for _ in chain]
            total = float(len(chain))

        reward = float(outcome_reward)
        return [
            StepCredit(
                step_id=step.step_id,
                credit=reward * (weights[index] / total),
                decay_factor=decay_factors[index],
            )
            for index, step in enumerate(chain)
        ]


def step(step_id: str, step_type: str = "step", *, age_seconds: float = 0.0) -> StepRecord:
    """Small helper for callers that need a relative timestamp record."""
    return StepRecord(step_id=step_id, step_type=step_type, timestamp=time.time() - float(age_seconds))
