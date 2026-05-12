"""Credit assignment helpers for optional RL feedback."""

from __future__ import annotations

from typing import Mapping


class CreditAssigner:
    """Distribute temporally discounted reward across contributing factors."""

    def __init__(self, temporal_discount: float = 0.95) -> None:
        self.temporal_discount = float(temporal_discount)

    def assign(
        self,
        reward: float,
        factors: list[str] | tuple[str, ...],
        factor_contributions: Mapping[str, float] | None = None,
        decision_age: int = 0,
    ) -> dict[str, float]:
        factor_names = [str(factor) for factor in factors]
        if not factor_names:
            return {}

        age = max(int(decision_age), 0)
        base = float(reward) * (self.temporal_discount ** age)
        contributions = factor_contributions or {}
        absolute_total = sum(abs(float(contributions.get(factor, 0.0))) for factor in factor_names)

        if absolute_total > 0.0:
            return {
                factor: base * (abs(float(contributions.get(factor, 0.0))) / absolute_total)
                for factor in factor_names
            }

        uniform = base / len(factor_names)
        return {factor: uniform for factor in factor_names}
