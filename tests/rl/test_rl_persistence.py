from __future__ import annotations

import pytest

from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.rl import ConservationBoundedThompson, CreditAssigner, GradedFinancialRewardFunction
from copilot_sdk.rl.presets import get_rl_components
from copilot_sdk.scoring.presets.s2p import S2PPreset
from copilot_sdk.scoring.presets.trading import TradingPreset
from copilot_sdk.scoring.scorer import CompoundingScorer


class StoreWithoutRlState:
    pass


class FailingSaveStore:
    def load_rl_state(self, key: str) -> dict | None:
        return None

    def save_rl_state(self, key: str, data: dict) -> None:
        raise RuntimeError("save failed")


class WrongSizeStore:
    def load_rl_state(self, key: str) -> dict:
        return {
            "alpha": [2.0],
            "beta": [3.0],
            "conservation_status": "RED",
        }


def test_thompson_empty_store_uses_uniform_defaults():
    store = InMemoryGraphStore(domain="trading")

    policy = ConservationBoundedThompson(n_actions=3, graph_store=store)

    assert policy.get_priors() == {
        "alpha": [1.0, 1.0, 1.0],
        "beta": [1.0, 1.0, 1.0],
        "conservation_status": "GREEN",
    }


def test_thompson_update_accumulates_priors():
    policy = ConservationBoundedThompson(n_actions=2)

    policy.update(0, 0.5)
    policy.update(1, -0.25)

    assert policy.get_priors() == {
        "alpha": [1.5, 1.0],
        "beta": [1.0, 1.25],
        "conservation_status": "GREEN",
    }


def test_thompson_persistence_roundtrip():
    store = InMemoryGraphStore(domain="trading")
    policy = ConservationBoundedThompson(n_actions=2, graph_store=store)
    policy.set_conservation_status("AMBER")

    policy.update(0, 0.5)
    policy.update(1, -0.25)
    restored = ConservationBoundedThompson(n_actions=2, graph_store=store)

    assert restored.get_priors() == {
        "alpha": [1.5, 1.0],
        "beta": [1.0, 1.25],
        "conservation_status": "AMBER",
    }


def test_thompson_save_failure_does_not_block_update():
    policy = ConservationBoundedThompson(n_actions=2, graph_store=FailingSaveStore())

    policy.update(0, 0.5)

    assert policy.alpha == [1.5, 1.0]


def test_thompson_wrong_size_persisted_state_falls_back_to_uniform():
    policy = ConservationBoundedThompson(n_actions=2, graph_store=WrongSizeStore())

    assert policy.get_priors() == {
        "alpha": [1.0, 1.0],
        "beta": [1.0, 1.0],
        "conservation_status": "GREEN",
    }


def test_thompson_store_without_rl_methods_works_in_memory_only():
    policy = ConservationBoundedThompson(n_actions=2, graph_store=StoreWithoutRlState())

    policy.update(0, 0.5)

    assert policy.alpha == [1.5, 1.0]


def test_thompson_no_store_constructor_still_works():
    policy = ConservationBoundedThompson(n_actions=2)

    policy.update(1, -0.25)

    assert policy.beta == [1.0, 1.25]


def test_credit_assigner_math_unchanged_without_store():
    credit = CreditAssigner().assign(1.0, ["a", "b"], {"a": 3.0, "b": 1.0})

    assert credit["a"] == pytest.approx(0.75)
    assert credit["b"] == pytest.approx(0.25)


def test_credit_assigner_math_unchanged_with_store():
    store = InMemoryGraphStore(domain="trading")

    credit = CreditAssigner(graph_store=store).assign(1.0, ["a", "b"], {"a": 3.0, "b": 1.0})

    assert credit["a"] == pytest.approx(0.75)
    assert credit["b"] == pytest.approx(0.25)


def test_get_rl_components_passes_store_to_explorer_and_credit():
    store = InMemoryGraphStore(domain="trading")

    components = get_rl_components("trading", TradingPreset(), graph_store=store)

    assert components["exploration_policy"]._graph_store is store
    assert components["credit_assigner"]._graph_store is store


def test_get_rl_components_s2p_uses_financial_reward():
    components = get_rl_components("s2p", S2PPreset())

    assert isinstance(components["reward_function"], GradedFinancialRewardFunction)
    assert components["exploration_policy"].n_actions == S2PPreset().shape.n_actions


def test_learn_posterior_update_is_not_exploration_used():
    graph_store = InMemoryGraphStore(domain="trading")
    scorer = CompoundingScorer.from_preset("trading", graph_store=graph_store)
    try:
        factors = {name: 0.5 for name in scorer._preset.shape.factor_names}
        result = scorer.score(factors, scorer._preset.shape.category_names[0])

        learn = scorer.learn(result.decision_id, result.action, context={"pnl_bps": 25})

        assert learn.reward_raw == 0.25
        assert learn.exploration_used is False
    finally:
        scorer.graph_store.close()
