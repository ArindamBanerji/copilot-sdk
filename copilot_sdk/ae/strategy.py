"""Domain injection contract for AgentEvolver."""

from __future__ import annotations

from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

from copilot_sdk.ae.types import Variant


@runtime_checkable
class DomainEvolutionStrategy(Protocol):
    """Domain-owned rule generation and fitness semantics."""

    def generate_variants(
        self, rule: Any, context: Mapping[str, Any]
    ) -> list[Variant]:
        ...

    def evaluate_fitness(
        self, variant: Variant, outcomes: Sequence[Mapping[str, Any]]
    ) -> float:
        ...

    def domain_constraints(self) -> dict[str, Any]:
        ...
