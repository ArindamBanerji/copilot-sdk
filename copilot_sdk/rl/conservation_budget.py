"""Fail-closed exploration proposals; no action selection or scorer mutation."""

from __future__ import annotations

import math
import random
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExplorationBudget:
    """epsilon = epsilon_firm_star * (1 - consumed / allowed).

Snapshots must explicitly identify category, GREEN status, valid=True,
paused=False, sufficient_evidence=True and finite consumed/allowed budgets.
Validity/freshness and category evidence are the caller's governance gate.
AMBER remains shadow-only. This is an admission proposal, not permission to
replace the authoritative judgment action or an atomic budget reservation.
"""

    epsilon_firm_star: float = 0.125

    def __post_init__(self) -> None:
        if not math.isfinite(self.epsilon_firm_star) or not 0 <= self.epsilon_firm_star <= 0.125:
            raise ValueError("epsilon_firm_star must be in [0, 0.125]")

    def epsilon(self, snapshot: Mapping[str, Any] | None, category: str) -> float:
        if not isinstance(snapshot, Mapping) or not isinstance(category, str) or not category.strip():
            return 0.0
        if (snapshot.get("category") != category or snapshot.get("status") != "GREEN"
                or snapshot.get("valid") is not True or snapshot.get("paused") is not False
                or snapshot.get("sufficient_evidence") is not True):
            return 0.0
        try:
            consumed = float(snapshot["consumed_budget"])
            allowed = float(snapshot["allowed_budget"])
        except (KeyError, TypeError, ValueError, OverflowError):
            return 0.0
        if not math.isfinite(consumed) or not math.isfinite(allowed) or consumed < 0 or allowed <= 0:
            return 0.0
        return self.epsilon_firm_star * (1.0 - min(1.0, consumed / allowed))

    def should_explore(self, snapshot: Mapping[str, Any] | None, category: str, *, rng: random.Random) -> bool:
        epsilon = self.epsilon(snapshot, category)
        return epsilon > 0 and rng.random() < epsilon
