"""Synthetic factor-vector generator for the JM Reference App.

This module emits factor vectors only.  It has no decision-quality
annotations and no dependency on the module that evaluates them.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class GeneratorConfig:
    """Configuration for deterministic synthetic factor vectors."""

    seed: int = 42
    n_decisions: int = 500
    n_categories: int | None = 6
    n_factors: int | None = 6
    category_names: list[str] | None = None
    factor_names: list[str] | None = None
    cold_start_variance: float = 0.18
    learned_variance: float = 0.05
    disruption_decision: int | None = 300
    disruption_categories: list[int] | None = None
    disruption_magnitude: float = 0.3


class SyntheticGenerator:
    """Produce ``(category, factor_dict)`` pairs without annotations."""

    def __init__(self, config: GeneratorConfig):
        self._config = config
        self._rng = np.random.default_rng(config.seed)
        self._decision_count = 0
        self._category_names = list(
            config.category_names
            or [f"cat_{i}" for i in range(config.n_categories or 0)]
        )
        self._factor_names = list(
            config.factor_names
            or [f"factor_{i}" for i in range(config.n_factors or 0)]
        )
        if not self._category_names:
            raise ValueError("at least one category is required")
        if not self._factor_names:
            raise ValueError("at least one factor is required")

    def generate(self) -> tuple[str, dict[str, float]]:
        """Generate one category and its factor vector."""

        self._decision_count += 1
        category_index = int(self._rng.integers(0, len(self._category_names)))
        category = self._category_names[category_index]

        post_disruption = (
            self._config.disruption_decision is not None
            and self._decision_count > self._config.disruption_decision
        )
        variance = (
            self._config.cold_start_variance
            if self._decision_count < 100
            else self._config.learned_variance
        )
        disrupted_categories = self._config.disruption_categories or []
        if post_disruption and category_index in disrupted_categories:
            variance += self._config.disruption_magnitude

        values = self._rng.normal(0.5, variance, size=len(self._factor_names))
        clipped = np.clip(values, 0.0, 1.0)
        factors = {
            name: float(value) for name, value in zip(self._factor_names, clipped)
        }
        return category, factors

    def generate_batch(self, n: int) -> list[tuple[str, dict[str, float]]]:
        """Generate ``n`` sequential factor-vector records."""

        if n < 0:
            raise ValueError("batch size must be non-negative")
        return [self.generate() for _ in range(n)]
