"""Pure, capped causal credit proposals; no scorer or persistence side effects."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TemporalCreditAssigner:
    """Apply reward * discount**delay, proportionally capped by chain_budget.

History is an explicit causal list, not inferred from coincident timestamps.
Duplicate IDs and invalid delays are rejected to prevent double-credit. The
output is an intent to include in OutcomeReceipt.learning_effect, not learning.
"""

    discount: float = 0.99
    chain_budget: float = 0.5

    def __post_init__(self) -> None:
        if not math.isfinite(self.discount) or not 0 < self.discount <= 1:
            raise ValueError("discount must be in (0, 1]")
        if not math.isfinite(self.chain_budget) or not 0 <= self.chain_budget <= 1:
            raise ValueError("chain_budget must be in [0, 1]")

    def assign(self, decision_id: str, reward: float, history: Sequence[Mapping[str, Any]]) -> dict[str, float]:
        if not isinstance(decision_id, str) or not decision_id.strip():
            raise ValueError("decision_id is required")
        if not math.isfinite(reward) or not 0 <= reward <= 1:
            raise ValueError("reward must be in [0, 1]")
        credits: dict[str, float] = {}
        for item in history:
            target = item.get("decision_id")
            if not isinstance(target, str) or not target.strip():
                raise ValueError("causal decision_id is required")
            if target == decision_id or target in credits:
                raise ValueError("causal history must exclude the outcome decision and duplicates")
            delay = float(item["delay"])
            if not math.isfinite(delay) or delay < 0:
                raise ValueError("causal delay must be finite and nonnegative")
            credits[target] = reward * self.discount ** delay
        total = math.fsum(credits.values())
        cap = reward * self.chain_budget
        if total > cap:
            return {target: value * (cap / total) for target, value in credits.items()}
        return credits
