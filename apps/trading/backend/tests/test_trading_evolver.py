from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.trading_evolver import (
    MAX_MULTIPLIER,
    MIN_MULTIPLIER,
    TRADING_FACTOR_NAMES,
    TradingAgentEvolver,
    TradingVariantGenerator,
    _VariantRule,
    _default_conservation_state,
)


class BaselineScorer:
    def __init__(self):
        self.graph_store = object()
        self.mutated = False
        self.state = {"weights": [1.0, 2.0, 3.0]}

    def predict(self, decision):
        return decision.get("recommended_action")


class StoreFactory:
    def __init__(self):
        self.created = []

    def __call__(self):
        store = ShadowStore()
        self.created.append(store)
        return store


class ShadowStore:
    def __init__(self):
        self.reads = []

    def record_shadow_read(self, decision):
        self.reads.append(decision)


def decisions(improvement_pp=10.0, count=50):
    variant_correct_count = int(count * 0.80)
    baseline_correct_count = int(count * (0.80 - improvement_pp / 100.0))
    rows = []
    for index in range(count):
        rows.append({
            "actual_action": "strong_execution",
            "recommended_action": "strong_execution" if index < baseline_correct_count else "partial_execution",
            "baseline_correct": index < baseline_correct_count,
            "variant_correct": index < variant_correct_count,
        })
    return rows


def make_evolver(conservation_state="GREEN"):
    return TradingAgentEvolver(
        baseline_scorer=BaselineScorer(),
        store_factory=StoreFactory(),
        factor_names=TRADING_FACTOR_NAMES,
        conservation_provider=lambda: {"status": conservation_state},
    )


def add_batches(evolver, variant, improvements):
    for improvement in improvements:
        evolver.shadow_test(variant, decisions(improvement), batch_size=50)


def test_generator_produces_variant():
    variant = TradingVariantGenerator(TRADING_FACTOR_NAMES).generate()
    assert variant["variant_id"]
    assert variant["adjustments"]


def test_adjustments_bounded():
    variant = TradingVariantGenerator(TRADING_FACTOR_NAMES).generate()
    assert all(MIN_MULTIPLIER <= value <= MAX_MULTIPLIER for value in variant["adjustments"].values())


def test_adjustments_use_trading_factors():
    variant = TradingVariantGenerator(TRADING_FACTOR_NAMES).generate()
    assert set(variant["adjustments"]).issubset(set(TRADING_FACTOR_NAMES))


def test_shadow_uses_isolated_store():
    evolver = make_evolver()
    variant = evolver.generate_variant()
    result = evolver.shadow_test(variant, decisions(), batch_size=50)
    assert result["shadow_store_isolated"] is True
    assert evolver.last_shadow_store is not evolver.baseline_scorer.graph_store
    assert evolver.last_shadow_store.reads


def test_shadow_result_fields():
    evolver = make_evolver()
    variant = evolver.generate_variant()
    result = evolver.shadow_test(variant, decisions(), batch_size=50)
    assert result["variant_accuracy"] >= 0
    assert result["baseline_accuracy"] >= 0
    assert "improvement_pp" in result
    assert "conservation_safe" in result


def test_promotion_requires_3_batches():
    evolver = make_evolver()
    variant = evolver.generate_variant()
    add_batches(evolver, variant, [10.0, 10.0])
    assert evolver.check_promotion(variant["variant_id"])["reason"] == "insufficient_batches"


def test_promotion_requires_5pp():
    evolver = make_evolver()
    variant = evolver.generate_variant()
    add_batches(evolver, variant, [3.0, 3.0, 3.0])
    assert evolver.check_promotion(variant["variant_id"])["reason"] == "insufficient_improvement"


def test_promotion_requires_green():
    evolver = make_evolver("AMBER")
    variant = evolver.generate_variant()
    add_batches(evolver, variant, [10.0, 10.0, 10.0])
    assert evolver.check_promotion(variant["variant_id"])["reason"] == "conservation_not_green"


def test_promotion_requires_stability():
    evolver = make_evolver()
    variant = evolver.generate_variant()
    add_batches(evolver, variant, [5.0, 30.0, 5.0])
    assert evolver.check_promotion(variant["variant_id"])["reason"] == "unstable_improvement"


def test_batch_count_gate_independent():
    evolver = make_evolver()
    variant = evolver.generate_variant()
    add_batches(evolver, variant, [10.0, 10.0])
    check = evolver.check_promotion(variant["variant_id"])
    assert check["batches"] == 2
    assert check["reason"] == "insufficient_batches"


def test_successful_promotion():
    evolver = make_evolver()
    variant = evolver.generate_variant()
    add_batches(evolver, variant, [10.0, 10.0, 10.0])
    result = evolver.promote(variant["variant_id"])
    assert result["promoted"] is True
    assert result["adjustments"]


def test_no_scorer_mutation():
    evolver = make_evolver()
    before = dict(evolver.baseline_scorer.state)
    variant = evolver.generate_variant()
    evolver.shadow_test(variant, decisions(), batch_size=50)
    assert evolver.baseline_scorer.state == before
    assert evolver.baseline_scorer.mutated is False


def test_evolution_log():
    evolver = make_evolver()
    variant = evolver.generate_variant()
    evolver.shadow_test(variant, decisions(), batch_size=50)
    log = evolver.evolution_log()
    assert len(log) == 1
    assert log[0]["status"] == "evaluating"


def test_conservation_gate_at_promotion():
    state = {"status": "GREEN"}
    evolver = TradingAgentEvolver(
        baseline_scorer=BaselineScorer(),
        store_factory=StoreFactory(),
        factor_names=TRADING_FACTOR_NAMES,
        conservation_provider=lambda: state,
    )
    variant = evolver.generate_variant()
    add_batches(evolver, variant, [10.0, 10.0, 10.0])
    state["status"] = "RED"
    result = evolver.promote(variant["variant_id"])
    assert result["promoted"] is False
    assert result["reason"] == "conservation_not_green"


def test_conservation_not_hardcoded_green():
    state = _default_conservation_state()

    assert state["status"] != "GREEN"
    assert state["note"] == "conservation service not configured"


def test_router_evolution_log():
    client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
    response = client.get("/api/trading/evolution/log")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_variant_adjustments_affect_score():
    decision = {
        "base_score": 0.5,
        "factors": {"signal_alignment": 0.8},
        "score_mode": True,
    }
    low = _VariantRule({
        "variant_id": "low",
        "factor_weight_adjustments": {"signal_alignment": 0.5},
    }).predict(decision)
    high = _VariantRule({
        "variant_id": "high",
        "factor_weight_adjustments": {"signal_alignment": 1.5},
    }).predict(decision)
    assert high > low


def test_apply_unknown_proposal_returns_404():
    client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))
    response = client.post("/api/trading/evolution/apply", json={"proposal_id": "missing"})
    assert response.status_code == 404
