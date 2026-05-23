from __future__ import annotations

from pathlib import Path

from copilot_sdk.scoring.presets.dataops import DataOpsPreset
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset
from copilot_sdk.scoring.presets.trading import TradingPreset
from copilot_sdk.scoring.scorer import CompoundingScorer


def _scorer(tmp_path: Path, domain: str = "trading", evolve: bool = False) -> CompoundingScorer:
    return CompoundingScorer.from_preset(
        domain,
        db_path=str(tmp_path / f"{domain}.db"),
        evolve=evolve,
    )


def _factors(preset, value: float = 0.8) -> dict[str, float]:
    return {name: value for name in preset.shape.factor_names}


def _score_and_learn(scorer: CompoundingScorer, preset, count: int = 1) -> None:
    categories = tuple(preset.shape.category_names)
    for index in range(count):
        result = scorer.score(_factors(preset), categories[index % len(categories)])
        scorer.learn(result.decision_id, result.action)


def test_evolve_false_creates_no_active_evolver(tmp_path):
    scorer = _scorer(tmp_path, evolve=False)

    assert getattr(scorer, "_evolve") is False
    assert getattr(scorer, "_evolver") is None


def test_evolve_true_creates_evolver(tmp_path):
    scorer = _scorer(tmp_path, evolve=True)

    assert getattr(scorer, "_evolve") is True
    assert getattr(scorer, "_evolver") is not None


def test_evolve_true_registers_three_rules(tmp_path):
    scorer = _scorer(tmp_path, evolve=True)

    active = scorer._evolver.get_active_rules()

    assert sorted(active) == [
        "action_bias_rule",
        "confidence_boundary_rule",
        "factor_weight_rule",
    ]


def test_rules_return_actual_trading_preset_actions(tmp_path):
    scorer = _scorer(tmp_path, domain="trading", evolve=True)
    actions = set(TradingPreset().shape.action_names)

    for rule in scorer._evolver.get_active_rules().values():
        assert rule.predict({"confidence": 0.8, "factors": [0.8, 0.7, 0.6]}) in actions


def test_score_learn_no_crash_with_evolve_true(tmp_path):
    scorer = _scorer(tmp_path, evolve=True)
    preset = TradingPreset()
    scorer._conservation_pause = lambda: None

    _score_and_learn(scorer, preset, count=1)

    assert scorer.graph_store.count_verified(scorer._domain) == 1


def test_evolution_triggers_after_twenty_learns(tmp_path):
    scorer = _scorer(tmp_path, evolve=True)
    preset = TradingPreset()
    scorer._conservation_pause = lambda: None

    _score_and_learn(scorer, preset, count=19)
    assert scorer._evolver.get_evolution_history() == []

    _score_and_learn(scorer, preset, count=1)

    history = scorer._evolver.get_evolution_history(limit=100)
    assert len(history) >= 3
    assert {event["rule_name"] for event in history} == set(scorer._evolver.get_active_rules())
    assert "variant_generated" in {event["event_type"] for event in history}


def test_dataops_actions_wired_correctly(tmp_path):
    scorer = _scorer(tmp_path, domain="dataops", evolve=True)
    actions = set(DataOpsPreset().shape.action_names)

    for rule in scorer._evolver.get_active_rules().values():
        assert set(rule.actions) == actions
        assert rule.predict({"confidence": 1.0, "factors": [1.0] * 6}) in actions


def test_purchasing_actions_wired_correctly(tmp_path):
    scorer = _scorer(tmp_path, domain="purchasing", evolve=True)
    actions = set(PurchasingPreset().shape.action_names)

    for rule in scorer._evolver.get_active_rules().values():
        assert set(rule.actions) == actions
