"""Variant generation orchestration."""

from __future__ import annotations

from typing import Any, Mapping

from copilot_sdk.ae.strategy import DomainEvolutionStrategy
from copilot_sdk.ae.types import Variant


class VariantGenerator:
    """Delegate candidate generation to an explicitly supplied domain strategy."""

    def __init__(self, strategy: DomainEvolutionStrategy) -> None:
        self.strategy = strategy

    def generate(
        self, rule: Any, context: Mapping[str, Any] | None = None
    ) -> list[Variant]:
        variants = self.strategy.generate_variants(rule, context or {})
        if not isinstance(variants, list) or not all(
            isinstance(variant, Variant) for variant in variants
        ):
            raise TypeError("domain strategy must return list[Variant]")
        return variants

    def generate_variants(
        self, rule: Any, context: Mapping[str, Any] | None = None
    ) -> list[Variant]:
        return self.generate(rule, context)
