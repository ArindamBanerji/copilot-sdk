"""Variant fitness evaluation."""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from copilot_sdk.ae.strategy import DomainEvolutionStrategy
from copilot_sdk.ae.types import FitnessResult, Variant


class FitnessEvaluator:
    """Evaluate variants using the injected domain strategy."""

    def __init__(self, strategy: DomainEvolutionStrategy) -> None:
        self.strategy = strategy

    def evaluate(
        self, variant: Variant, outcomes: Sequence[Mapping[str, Any]]
    ) -> FitnessResult:
        fitness = float(self.strategy.evaluate_fitness(variant, outcomes))
        if not math.isfinite(fitness):
            raise ValueError("fitness must be finite")
        return FitnessResult(variant.variant_id, fitness, len(outcomes))

    def evaluate_fitness(
        self, variant: Variant, outcomes: Sequence[Mapping[str, Any]]
    ) -> float:
        return self.evaluate(variant, outcomes).fitness
