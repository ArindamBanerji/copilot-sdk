from __future__ import annotations

from pathlib import Path

import pytest

from copilot_sdk.evolution import EvolutionRule
from copilot_sdk.evolution.toy_rules import ActionBiasRule, FactorWeightRule, ThresholdRule


def test_threshold_rule_implements_evolution_rule():
    assert isinstance(ThresholdRule(["first", "second"]), EvolutionRule)


def test_threshold_rule_returns_domain_action():
    actions = ["first", "second"]
    rule = ThresholdRule(actions, cutoff=0.5)

    assert rule.predict({"confidence": "0.9"}) in actions
    assert rule.predict({"confidence": "0.1"}) in actions
    assert rule.predict({"confidence": "not-a-number"}) in actions


def test_threshold_rule_variant_preserves_actions():
    actions = ["first", "second", "third"]
    variant = ThresholdRule(actions).generate_variant(seed=12)

    assert list(variant.actions) == actions
    assert variant.predict({"confidence": 0.7}) in actions


def test_factor_weight_rule_works_with_dataops_action_count():
    actions = ["a0", "a1", "a2", "a3", "a4"]
    rule = FactorWeightRule(actions, factor_count=6)

    assert rule.predict({"factors": [0.9, 0.8, 0.7]}) in actions
    assert rule.predict({"factors": {"x": "0.9", "y": object(), "metadata": {"z": 1}}}) in actions


def test_action_bias_rule_deterministic_variant():
    actions = ["first", "last"]
    one = ActionBiasRule(actions).generate_variant(seed=5)
    two = ActionBiasRule(actions).generate_variant(seed=5)

    assert one == two
    assert one.predict({"factors": [1.0, 1.0]}) in actions


def test_all_rules_handle_empty_context():
    actions = ["first", "second"]

    assert ThresholdRule(actions).predict({}) in actions
    assert FactorWeightRule(actions).predict({}) in actions
    assert ActionBiasRule(actions).predict({}) in actions


@pytest.mark.parametrize("actions", [None, [], ["only"]])
def test_rules_require_at_least_two_actions(actions):
    with pytest.raises(ValueError):
        ThresholdRule(actions)
    with pytest.raises(ValueError):
        FactorWeightRule(actions)
    with pytest.raises(ValueError):
        ActionBiasRule(actions)


def test_no_hardcoded_domain_vocabulary_in_toy_rules():
    text = Path("copilot_sdk/evolution/toy_rules.py").read_text(encoding="utf-8").lower()
    forbidden = [
        "credential_access",
        "lateral_movement",
        "brute_force",
        "buy",
        "hold",
        "sell",
        "auto_approve",
        "investigate",
    ]

    for word in forbidden:
        assert word not in text
