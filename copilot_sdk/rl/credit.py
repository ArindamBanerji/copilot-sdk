"""Temporal credit assignment for delayed outcomes."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from copilot_sdk.rl.types import CreditAssignment


class CreditAssigner:
    """Assign discounted credit across a causal sequence of contributors."""

    def __init__(self, temporal_discount: float = 0.95, graph_store: object | None = None) -> None:
        if not 0.0 < temporal_discount <= 1.0:
            raise ValueError("temporal_discount must be in (0, 1]")
        self.temporal_discount = float(temporal_discount)
        self.graph_store = graph_store
        self._graph_store = graph_store

    def assign(
        self,
        reward: float,
        factors: Sequence[str],
        factor_contributions: Mapping[str, float] | None = None,
        decision_age: int = 0,
    ) -> dict[str, float]:
        names = [str(factor) for factor in factors]
        if not names:
            return {}
        base = float(reward) * self.temporal_discount ** max(int(decision_age), 0)
        weights = {name: abs(float((factor_contributions or {}).get(name, 0.0))) for name in names}
        total = sum(weights.values())
        if total <= 0.0:
            share = base / len(names)
            return {name: share for name in names}
        return {name: base * weight / total for name, weight in weights.items()}

    def assign_temporal(
        self,
        reward: float,
        contributors: Sequence[tuple[str, int]],
    ) -> list[CreditAssignment]:
        """Assign discounted reward to contributors with explicit delays."""
        return [
            CreditAssignment(
                target_id=str(target_id),
                credit=float(reward) * self.temporal_discount ** max(int(delay), 0),
                delay=max(int(delay), 0),
            )
            for target_id, delay in contributors
        ]
