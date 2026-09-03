"""Shared value types for the AgentEvolver SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Variant:
    """A candidate rule produced by a domain evolution strategy."""

    variant_id: str
    rule: Any
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.variant_id.strip():
            raise ValueError("variant_id must be a non-empty string")
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True)
class FitnessResult:
    """Fitness observed for a variant over an outcome sample."""

    variant_id: str
    fitness: float
    sample_size: int


@dataclass(frozen=True)
class PromotionDecision:
    """Auditable result of a paired bootstrap promotion check."""

    promoted: bool
    reason: str
    p_value: float
    sample_size: int
    effect: float
    fpr_bound: float
    checks: dict[str, bool] = field(default_factory=dict)


EvolutionVariant = Variant
PromotionResult = PromotionDecision
