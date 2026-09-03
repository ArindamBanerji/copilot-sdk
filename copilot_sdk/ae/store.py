"""GraphStore-backed AgentEvolver persistence."""

from __future__ import annotations

from typing import Any, cast

from copilot_sdk.ae.types import FitnessResult, PromotionDecision, Variant
from copilot_sdk.graph.protocol import GraphStore


class EvolutionStore:
    """Persist AE state through the public GraphStore contract."""

    def __init__(self, graph_store: GraphStore, domain: str) -> None:
        if not domain.strip():
            raise ValueError("domain must be a non-empty string")
        self.graph_store = graph_store
        self.domain = domain

    def save_variant(self, variant: Variant) -> None:
        self.graph_store.save_evolution(self.domain, variant.variant_id, {"rule": variant.rule, "metadata": variant.metadata})

    def get_variant(self, variant_id: str) -> dict[str, Any] | None:
        return cast(dict[str, Any] | None, self.graph_store.get_evolution(self.domain, variant_id))

    def list_variants(self) -> list[dict[str, Any]]:
        return cast(list[dict[str, Any]], self.graph_store.list_evolutions(self.domain))

    def delete_variant(self, variant_id: str) -> None:
        self.graph_store.delete_evolution(self.domain, variant_id)

    def save_fitness(self, result: FitnessResult) -> None:
        self.graph_store.save_ledger(self.domain, f"fitness:{result.variant_id}", {"variant_id": result.variant_id, "fitness": result.fitness, "sample_size": result.sample_size})

    def save_promotion(self, rule_id: str, decision: PromotionDecision) -> None:
        self.graph_store.save_promotion(self.domain, rule_id, {"promoted": decision.promoted, "reason": decision.reason, "p_value": decision.p_value, "sample_size": decision.sample_size, "effect": decision.effect, "fpr_bound": decision.fpr_bound, "checks": decision.checks})
