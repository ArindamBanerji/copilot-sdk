"""Contract tests for the portable AgentEvolver framework."""

from __future__ import annotations

import pytest
from typing import Any, Mapping, Sequence, cast

from copilot_sdk.ae import (
    EvolutionStore,
    FitnessEvaluator,
    PromotionGate,
    Variant,
    VariantGenerator,
)
from copilot_sdk.ae.strategy import DomainEvolutionStrategy
from copilot_sdk.graph.memory_store import InMemoryGraphStore


class Strategy:
    def generate_variants(self, rule: Any, context: Mapping[str, Any]) -> list[Variant]:
        return [Variant(f"{rule}-1", f"{rule}:tight", {"source": context["source"]})]

    def evaluate_fitness(self, variant: Variant, outcomes: Sequence[Mapping[str, Any]]) -> float:
        return sum(float(item["value"]) for item in outcomes) / len(outcomes)

    def domain_constraints(self) -> dict[str, Any]:
        return {"conservation": True, "penalty_ratio": 5}


def _pairs(n: int = 30) -> tuple[list[float], list[float]]:
    return [0.9] * n, [0.5] * n


def test_variant_requires_id() -> None:
    with pytest.raises(ValueError):
        Variant("", "rule")


def test_variant_preserves_rule_and_metadata() -> None:
    variant = Variant("v1", "rule", {"owner": "trading"})
    assert variant.rule == "rule"
    assert variant.metadata == {"owner": "trading"}


def test_strategy_is_runtime_protocol_compliant() -> None:
    assert isinstance(Strategy(), DomainEvolutionStrategy)


def test_generator_delegates_to_domain_strategy() -> None:
    assert VariantGenerator(Strategy()).generate("r", {"source": "seed"})[0].variant_id == "r-1"


def test_generator_alias_matches_generate() -> None:
    assert VariantGenerator(Strategy()).generate_variants("r", {"source": "seed"})[0].rule == "r:tight"


def test_generator_rejects_invalid_strategy_output() -> None:
    class InvalidStrategy(Strategy):
        def generate_variants(self, rule: Any, context: Any) -> Any:
            return ["not-a-variant"]

    with pytest.raises(TypeError):
        VariantGenerator(cast(DomainEvolutionStrategy, InvalidStrategy())).generate("r", {})


def test_fitness_evaluator_returns_result() -> None:
    result = FitnessEvaluator(Strategy()).evaluate(Variant("v", "r"), [{"value": 0.4}, {"value": 0.8}])
    assert result.fitness == pytest.approx(0.6)
    assert result.sample_size == 2


def test_fitness_evaluator_alias_returns_scalar() -> None:
    assert FitnessEvaluator(Strategy()).evaluate_fitness(Variant("v", "r"), [{"value": 1.0}]) == 1.0


def test_fitness_rejects_nonfinite_result() -> None:
    class BadStrategy(Strategy):
        def evaluate_fitness(self, variant: Variant, outcomes: Sequence[Mapping[str, Any]]) -> float:
            return float("nan")

    with pytest.raises(ValueError):
        FitnessEvaluator(BadStrategy()).evaluate(Variant("v", "r"), [])


def test_gate_defaults_to_e22_thresholds() -> None:
    gate = PromotionGate()
    assert gate.min_n == 30
    assert gate.fpr_threshold == 0.05


def test_gate_accepts_exact_minimum_sample() -> None:
    candidate, baseline = _pairs()
    assert PromotionGate(random_seed=1).evaluate(candidate, baseline).promoted


def test_gate_rejects_insufficient_sample() -> None:
    result = PromotionGate().evaluate(*_pairs(29))
    assert not result.promoted and result.reason == "insufficient_sample_size"


def test_gate_requires_paired_lengths() -> None:
    with pytest.raises(ValueError):
        PromotionGate().evaluate([1.0] * 30, [0.0] * 29)


def test_gate_promotes_clear_superiority() -> None:
    assert PromotionGate(random_seed=2).should_promote(*_pairs())


def test_gate_rejects_equal_performance() -> None:
    assert not PromotionGate(random_seed=2).evaluate([0.5] * 30, [0.5] * 30).promoted


def test_gate_rejects_worse_candidate() -> None:
    assert not PromotionGate(random_seed=2).evaluate([0.2] * 30, [0.5] * 30).promoted


def test_gate_blocks_non_green_conservation() -> None:
    result = PromotionGate().evaluate(*_pairs(), conservation_state="RED")
    assert not result.promoted and result.reason == "conservation_not_green"


def test_gate_is_reproducible_with_seed() -> None:
    candidate, baseline = _pairs()
    first = PromotionGate(random_seed=9).evaluate(candidate, baseline)
    second = PromotionGate(random_seed=9).evaluate(candidate, baseline)
    assert first == second


def test_gate_reports_effect_and_p_value() -> None:
    result = PromotionGate(random_seed=3).evaluate(*_pairs())
    assert result.effect == pytest.approx(0.4)
    assert 0.0 <= result.p_value <= 1.0


def test_evolution_store_persists_variant() -> None:
    store = EvolutionStore(InMemoryGraphStore(), "trading")
    store.save_variant(Variant("v1", "rule"))
    saved = store.get_variant("v1")
    assert saved is not None and saved["rule"] == "rule"
    assert len(store.list_variants()) == 1


def test_evolution_store_persists_fitness_in_ledger() -> None:
    store = EvolutionStore(InMemoryGraphStore(), "purchasing")
    result = FitnessEvaluator(Strategy()).evaluate(Variant("v1", "r"), [{"value": 0.8}])
    store.save_fitness(result)
    saved = store.graph_store.get_ledger("purchasing", "fitness:v1")
    assert saved is not None and saved["fitness"] == 0.8


def test_evolution_store_persists_promotion() -> None:
    store = EvolutionStore(InMemoryGraphStore(), "dataops")
    decision = PromotionGate().evaluate(*_pairs())
    store.save_promotion("rule-1", decision)
    saved = store.graph_store.get_promotion("dataops", "rule-1")
    assert saved is not None and saved["promoted"] is True


def test_evolution_store_is_domain_scoped() -> None:
    graph = InMemoryGraphStore()
    EvolutionStore(graph, "soc").save_variant(Variant("v", "soc-rule"))
    assert EvolutionStore(graph, "trading").get_variant("v") is None


def test_evolution_store_delete_is_explicit() -> None:
    store = EvolutionStore(InMemoryGraphStore(), "soc")
    store.save_variant(Variant("v", "r"))
    store.delete_variant("v")
    assert store.get_variant("v") is None


def test_end_to_end_generation_fitness_and_promotion() -> None:
    variant = VariantGenerator(Strategy()).generate("base", {"source": "seed"})[0]
    fitness = FitnessEvaluator(Strategy()).evaluate(variant, [{"value": 0.9}] * 30)
    decision = PromotionGate(random_seed=7).evaluate(*_pairs())
    assert fitness.sample_size == 30 and decision.promoted


def test_gate_rejects_invalid_parameters() -> None:
    with pytest.raises(ValueError):
        PromotionGate(min_n=0)
    with pytest.raises(ValueError):
        PromotionGate(fpr_threshold=1.0)
