from __future__ import annotations

import math

import pytest

from copilot_sdk.substantiation.oracles import ChefOracle, DataOpsOracle, TraderOracle


ORACLES = [
    ("trader", TraderOracle, "strong_execution", 0.08),
    ("chef", ChefOracle, "order_as_planned", 0.07),
    ("dataops", DataOpsOracle, "accept", 0.10),
]


@pytest.mark.parametrize("name,oracle_cls,target_action,expected_lift", ORACLES)
def test_exp1_positive_lift(name, oracle_cls, target_action, expected_lift) -> None:
    oracle = oracle_cls()
    result = run_experiment(oracle, target_action, n_per_arm=1_000)
    assert abs(result["lift"] - expected_lift) < 0.04, (
        f"{name}: lift {result['lift']:.3f}, expected ~{expected_lift}"
    )


@pytest.mark.parametrize("name,oracle_cls,target_action,expected_lift", ORACLES)
def test_exp2_null_effect(name, oracle_cls, target_action, expected_lift) -> None:
    oracle = oracle_cls(treatment_lift=0.0, accuracy_lift=0.0)
    result = run_experiment(oracle, target_action, n_per_arm=1_000)
    assert abs(result["lift"]) < 0.03, (
        f"{name}: null lift {result['lift']:.3f}, should be ~0"
    )


@pytest.mark.parametrize("name,oracle_cls,target_action,expected_lift", ORACLES)
def test_exp3_floor_power(name, oracle_cls, target_action, expected_lift) -> None:
    p = 0.5
    z_a, z_b = 1.96, 0.84
    n_floor = math.ceil(2 * p * (1 - p) * ((z_a + z_b) / expected_lift) ** 2)
    assert 0 < n_floor < 10_000, f"{name}: floor N={n_floor}"


@pytest.mark.parametrize("name,oracle_cls,target_action,expected_lift", ORACLES)
def test_exp4_accuracy_gate_rejects(name, oracle_cls, target_action, expected_lift) -> None:
    oracle = oracle_cls(accuracy_lift=-0.08)
    result = run_experiment(oracle, target_action, n_per_arm=1_000)
    assert result["lift"] > 0.02, f"{name}: lift should be positive"
    assert result["accuracy_delta"] < -0.02, f"{name}: accuracy should be negative"
    gate_passes = result["lift"] > 0 and result["accuracy_delta"] >= 0
    assert not gate_passes, f"{name}: gate should reject positive lift + negative accuracy"


def run_experiment(oracle, target_action: str, n_per_arm: int = 1_000) -> dict[str, float]:
    treatment = [oracle.synthetic_outcome(shown=True) for _ in range(n_per_arm)]
    control = [oracle.synthetic_outcome(shown=False) for _ in range(n_per_arm)]

    t_rate = sum(1 for row in treatment if row["action"] == target_action) / n_per_arm
    c_rate = sum(1 for row in control if row["action"] == target_action) / n_per_arm
    t_acc = sum(1 for row in treatment if row.get("correct")) / n_per_arm
    c_acc = sum(1 for row in control if row.get("correct")) / n_per_arm

    return {
        "lift": t_rate - c_rate,
        "accuracy_delta": t_acc - c_acc,
        "treatment_rate": t_rate,
        "control_rate": c_rate,
    }
