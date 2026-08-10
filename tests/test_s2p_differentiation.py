from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from apps.s2p_differentiation.config import S2P_GENERATOR, S2P_ORACLE
from apps.s2p_differentiation.engine import run_three_arms
from examples.jm_reference.generator import SyntheticGenerator


@pytest.fixture(scope="module")
def result(tmp_path_factory: pytest.TempPathFactory) -> dict:
    return run_three_arms(
        replace(S2P_GENERATOR, n_decisions=500),
        S2P_ORACLE,
        n_decisions=500,
        output_dir=tmp_path_factory.mktemp("s2p-differentiation"),
    )


def test_three_arms_complete(result: dict) -> None:
    for key in ("arm_1_ci", "arm_2_reward_max", "arm_3_hand_specified"):
        arm = result[key]
        assert len(arm["decisions"]) == 500
        assert len(arm["quality_curve"]) == 500
        assert arm["conservation_states"]


def test_ci_quality_above_reward_max_post_disruption(result: dict) -> None:
    assert result["arm_1_ci"]["quality_curve"][-1] > result["arm_2_reward_max"]["quality_curve"][-1]


def test_reward_max_collapses_after_poisoned_promotion(result: dict) -> None:
    baseline = result["arm_2_reward_max"]
    assert baseline["promotions"]
    poison_step = baseline["promotions"][0]["promoted_at"]
    assert baseline["high_severity_quality_curve"][-1] < baseline["high_severity_quality_curve"][poison_step - 1]


def test_ci_rejects_poisoned_rule(result: dict) -> None:
    rejection = result["arm_1_ci"]["rejections"][0]
    assert rejection["reason"] in {"unstable_improvement", "conservation_not_green"}
    assert rejection["promoted"] is False


def test_baseline_is_faithful(result: dict) -> None:
    ci = result["arm_1_ci"]["quality_curve"][59]
    baseline = result["arm_2_reward_max"]["quality_curve"][59]
    assert baseline >= 0.80 * ci


def test_hand_specified_trails_ci(result: dict) -> None:
    assert result["arm_1_ci"]["quality_curve"][-1] > result["arm_3_hand_specified"]["quality_curve"][-1]


def test_oracle_separation_maintained() -> None:
    source = Path("examples/jm_reference/generator.py").read_text(encoding="utf-8")
    assert "is_correct" not in source
    assert "label_correct" not in source


def test_all_arms_same_seed() -> None:
    batches = [SyntheticGenerator(S2P_GENERATOR).generate_batch(25) for _ in range(3)]
    assert batches[0] == batches[1] == batches[2]
