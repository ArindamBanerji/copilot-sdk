from __future__ import annotations

from copilot_sdk.scoring.presets.purchasing import PurchasingPreset
from copilot_sdk.substantiation import ChefOracle, ChefPipelineTest
from copilot_sdk.substantiation.populate_readiness import populate_default_readiness


def _sample(oracle: ChefOracle, *, shown: bool, n: int = 1000) -> list[dict]:
    return [oracle.synthetic_outcome(shown=shown) for _ in range(n)]


def _order_rate(outcomes: list[dict]) -> float:
    return sum(row["action"] != "skip" for row in outcomes) / len(outcomes)


def test_chef_deterministic():
    first = ChefOracle(seed=7)
    second = ChefOracle(seed=7)
    assert [first.synthetic_outcome(shown=True) for _ in range(20)] == [
        second.synthetic_outcome(shown=True) for _ in range(20)
    ]


def test_chef_treatment_higher():
    treatment = _sample(ChefOracle(seed=11), shown=True)
    control = _sample(ChefOracle(seed=11), shown=False)
    assert _order_rate(treatment) > _order_rate(control)


def test_chef_correct_modeled():
    outcomes = _sample(ChefOracle(seed=13), shown=True, n=200)
    assert any(row["correct"] for row in outcomes)
    assert any(not row["correct"] for row in outcomes)


def test_chef_domain_actions():
    preset_actions = set(PurchasingPreset().shape.action_names)
    outcomes = _sample(ChefOracle(seed=17), shown=True, n=200) + _sample(
        ChefOracle(seed=17),
        shown=False,
        n=200,
    )
    assert {row["action"] for row in outcomes} <= preset_actions


def test_chef_exp1_known_lift():
    result = ChefPipelineTest().exp1_known_lift()
    assert result.passed
    assert abs(result.measured_lift - result.expected_lift) <= 0.04


def test_chef_exp2_zero_lift():
    result = ChefPipelineTest().exp2_zero_lift()
    assert result.passed
    assert abs(result.measured_lift) <= 0.03


def test_chef_exp3_floor_power():
    result = ChefPipelineTest().exp3_floor_power()
    assert result.passed
    assert result.detail["n_per_arm_floor"] > 0


def test_chef_exp4_gate_rejects():
    result = ChefPipelineTest().exp4_gate_rejects()
    assert result.passed
    assert result.detail["gate_correctly_rejected"] is True


def test_readiness_purchasing_instrumented():
    entry = next(
        row
        for row in populate_default_readiness()
        if row.feature == "P73-par-intelligence"
    )
    assert entry.instrumented is True
    assert entry.gate() == (False, ["proven"])
