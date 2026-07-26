from __future__ import annotations

import pytest

from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.rl import (
    ConservationBoundedThompson,
    CreditAssigner,
    GradedFinancialRewardFunction,
    PnLRewardFunction,
    WasteReductionRewardFunction,
)
from copilot_sdk.scoring.scorer import CompoundingScorer


def _scorer(domain: str, *, enable_rl: bool = True) -> CompoundingScorer:
    return CompoundingScorer.from_preset(
        domain,
        graph_store=InMemoryGraphStore(domain=domain),
        enable_rl=enable_rl,
        profile="test",
    )


def _factors(scorer: CompoundingScorer) -> dict[str, float]:
    return {name: 0.5 for name in scorer._preset.shape.factor_names}


def _category(scorer: CompoundingScorer) -> str:
    return scorer._preset.shape.category_names[0]


def _close(scorer: CompoundingScorer) -> None:
    scorer.graph_store.close()


def test_from_preset_trading_wires_rl_components():
    scorer = _scorer("trading")
    try:
        assert isinstance(scorer._reward_fn, PnLRewardFunction)
        assert isinstance(scorer._explorer, ConservationBoundedThompson)
        assert isinstance(scorer._credit, CreditAssigner)
    finally:
        _close(scorer)


def test_from_preset_enable_rl_false_preserves_no_auto_rl_behavior():
    scorer = _scorer("trading", enable_rl=False)
    try:
        assert scorer._reward_fn is None
        assert scorer._explorer is None
        assert scorer._credit is None
    finally:
        _close(scorer)


def test_from_preset_purchasing_wires_waste_reward():
    scorer = _scorer("purchasing")
    try:
        assert isinstance(scorer._reward_fn, WasteReductionRewardFunction)
    finally:
        _close(scorer)


def test_from_preset_dataops_wires_financial_reward():
    scorer = _scorer("dataops")
    try:
        assert isinstance(scorer._reward_fn, GradedFinancialRewardFunction)
    finally:
        _close(scorer)


def test_s2p_preset_wires_financial_reward():
    scorer = _scorer("s2p")
    try:
        assert isinstance(scorer._reward_fn, GradedFinancialRewardFunction)
        assert isinstance(scorer._explorer, ConservationBoundedThompson)
        assert isinstance(scorer._credit, CreditAssigner)
    finally:
        _close(scorer)


def test_score_output_matches_with_and_without_rl():
    with_rl = _scorer("trading")
    without_rl = _scorer("trading", enable_rl=False)
    try:
        factors = _factors(with_rl)
        category = _category(with_rl)

        score_with_rl = with_rl.score(factors, category)
        score_without_rl = without_rl.score(factors, category)

        assert score_with_rl.action == score_without_rl.action
        assert score_with_rl.action_index == score_without_rl.action_index
        assert score_with_rl.confidence == pytest.approx(score_without_rl.confidence)
        assert score_with_rl.probabilities == pytest.approx(score_without_rl.probabilities)
        assert score_with_rl.category == score_without_rl.category
        assert score_with_rl.factors == score_without_rl.factors
    finally:
        _close(with_rl)
        _close(without_rl)


def test_learn_with_rl_computes_reward_and_updates_explorer():
    scorer = _scorer("trading")
    try:
        result = scorer.score(_factors(scorer), _category(scorer))

        learn = scorer.learn(result.decision_id, result.action, context={"pnl_bps": 25})

        assert learn.reward_raw == 0.25
        assert learn.reward == 0.25
        assert scorer._explorer.alpha[result.action_index] == pytest.approx(1.25)
    finally:
        _close(scorer)


def test_learn_without_rl_still_has_no_reward():
    scorer = _scorer("trading", enable_rl=False)
    try:
        result = scorer.score(_factors(scorer), _category(scorer))

        learn = scorer.learn(result.decision_id, result.action, context={"pnl_bps": 25})

        assert learn.reward is None
        assert learn.reward_raw is None
    finally:
        _close(scorer)


def test_rl_setup_failure_does_not_block_from_preset(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("test setup failure")

    monkeypatch.setattr("copilot_sdk.rl.presets.get_rl_components", boom)

    scorer = _scorer("trading")
    try:
        assert scorer._reward_fn is None
        assert scorer._explorer is None
        assert scorer._credit is None
    finally:
        _close(scorer)


def test_from_preset_preserves_old_positional_evolve_argument_order():
    graph_store = InMemoryGraphStore(domain="trading")

    scorer = CompoundingScorer.from_preset(
        "trading",
        None,
        graph_store,
        None,
        None,
        None,
        True,
        True,
        profile="test",
    )
    try:
        assert scorer._evolve is True
        assert scorer._consolidation_enabled is True
    finally:
        _close(scorer)


def test_rl_setup_failure_preserves_explicit_components(monkeypatch):
    class ExplicitReward:
        def compute(self, *args, **kwargs):
            return 0.0

    class ExplicitExplorer:
        def update(self, action: int, reward: float) -> None:
            pass

    class ExplicitCredit:
        def assign(self, reward: float, factors: list[str]) -> dict[str, float]:
            return {}

    def boom(*args, **kwargs):
        raise RuntimeError("test setup failure")

    reward = ExplicitReward()
    explorer = ExplicitExplorer()
    credit = ExplicitCredit()
    monkeypatch.setattr("copilot_sdk.rl.presets.get_rl_components", boom)

    scorer = CompoundingScorer.from_preset(
        "trading",
        graph_store=InMemoryGraphStore(domain="trading"),
        reward_function=reward,
        credit_assigner=credit,
        exploration_policy=explorer,
        profile="test",
    )
    try:
        assert scorer._reward_fn is reward
        assert scorer._credit is credit
        assert scorer._explorer is explorer
    finally:
        _close(scorer)


def test_rl_setup_failure_preserves_one_explicit_component_only(monkeypatch):
    class ExplicitReward:
        def compute(self, *args, **kwargs):
            return 0.0

    def boom(*args, **kwargs):
        raise RuntimeError("test setup failure")

    reward = ExplicitReward()
    monkeypatch.setattr("copilot_sdk.rl.presets.get_rl_components", boom)

    scorer = CompoundingScorer.from_preset(
        "trading",
        graph_store=InMemoryGraphStore(domain="trading"),
        reward_function=reward,
        profile="test",
    )
    try:
        assert scorer._reward_fn is reward
        assert scorer._credit is None
        assert scorer._explorer is None
    finally:
        _close(scorer)
