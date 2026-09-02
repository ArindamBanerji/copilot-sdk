"""Cross-copilot contract tests for Judgment Memory and RL."""

from __future__ import annotations

import inspect
from typing import Any

import pytest

from copilot_sdk.config import GraphConfig
from ci_platform.graph.age_graph_store import AGEGraphStore
from copilot_sdk.evolution.gate import DefaultPromotionGate
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.protocol import GraphStore, ProtocolV2GraphStore
from copilot_sdk.rl import (
    BinaryRewardFunction,
    CreditAssigner,
    DataOpsReward,
    ExplorationPolicy,
    GradedFinancialRewardFunction,
    PurchasingReward,
    RewardComputer,
    TradingReward,
)
from copilot_sdk.rl.presets import RL_PRESET_REGISTRY
from copilot_sdk.scoring.presets.dataops import DataOpsPreset
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset
from copilot_sdk.scoring.presets.soc import SOCPreset
from copilot_sdk.scoring.presets.trading import TradingPreset


DOMAINS = ("soc", "s2p", "trading", "purchasing", "dataops")
PENALTY_RATIOS = {"soc": 20.0, "s2p": 5.0, "trading": 2.0, "purchasing": 3.0, "dataops": 10.0}


def _store() -> InMemoryGraphStore:
    return InMemoryGraphStore(domain="shared")


def test_in_memory_store_implements_graphstore_protocol() -> None:
    assert isinstance(_store(), GraphStore)


def test_in_memory_store_implements_protocol_v2() -> None:
    assert isinstance(_store(), ProtocolV2GraphStore)


def test_graphstore_has_all_platform_state_methods() -> None:
    methods = {
        "save_evolution", "get_evolution", "list_evolutions", "delete_evolution",
        "save_posterior", "get_posterior", "list_posteriors", "delete_posterior",
        "save_promotion", "get_promotion", "list_promotions", "delete_promotion",
        "save_ledger", "get_ledger", "list_ledgers", "delete_ledger",
        "save_governance", "get_governance", "list_governance", "delete_governance",
    }
    assert methods.issubset({name for name, value in inspect.getmembers(GraphStore) if callable(value)})


def test_age_graph_store_has_all_platform_state_methods() -> None:
    state_methods = {
        "save_evolution", "get_evolution", "save_posterior", "get_posterior",
        "save_promotion", "get_promotion", "save_ledger", "get_ledger",
        "save_governance", "get_governance",
    }
    assert state_methods.issubset(set(vars(AGEGraphStore)))


@pytest.mark.parametrize("domain", DOMAINS)
def test_domain_config_uses_shared_age_graph(domain: str) -> None:
    config = GraphConfig.load(domain)
    assert config.backend == "age"
    assert config.graph == "soc_graph"
    assert config.authorized == f"{domain}:soc_graph"


def test_domain_isolation_in_memory() -> None:
    store = _store()
    first = store.write_decision("trading", "trend", "buy", 0.9, {})
    store.write_decision("purchasing", "produce", "order", 0.9, {})
    assert store.get_decision(first, "trading") is not None
    assert store.get_decisions("purchasing")
    assert store.get_decisions("trading", category="produce") == []


def test_shared_graph_traversal_is_available() -> None:
    store = _store()
    decision_id = store.write_decision("trading", "trend", "buy", 0.9, {})
    store.link_entity(decision_id, "security-1", "security", "trading")
    assert store.query_context("security-1", 2, domain="trading")


def test_tensor_shapes_for_sdk_presets() -> None:
    expected = {"soc": (6, 4, 6), "trading": (5, 4, 10), "purchasing": (5, 4, 7), "dataops": (6, 5, 6)}
    presets = {"soc": SOCPreset(), "trading": TradingPreset(), "purchasing": PurchasingPreset(), "dataops": DataOpsPreset()}
    for domain, shape in expected.items():
        assert presets[domain].shape.tensor_shape == shape


def test_theta_min_gate_is_common() -> None:
    gate = DefaultPromotionGate()
    for domain in DOMAINS:
        result = gate.evaluate({"total": 0, "accuracy": 0.0, "baseline_accuracy": 0.0, "sufficient": False})
        assert result["checks"]["conservation"] is False


def test_sqlite_is_not_protocol_v2() -> None:
    from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
    from copilot_sdk.scoring.scorer import CompoundingScorer
    store = SQLiteGraphStore(":memory:", domain="test")
    try:
        with pytest.raises(RuntimeError, match="AGE-backed"):
            CompoundingScorer.from_preset("trading", graph_store=store, profile="production")
    finally:
        store.close()


@pytest.mark.parametrize("reward", [BinaryRewardFunction(), GradedFinancialRewardFunction(), TradingReward(), PurchasingReward(), DataOpsReward()])
def test_all_five_reward_functions_implement_protocol(reward: Any) -> None:
    from copilot_sdk.rl.reward import DomainRewardFunction
    assert isinstance(reward, DomainRewardFunction)


@pytest.mark.parametrize("reward", [TradingReward(), PurchasingReward(), DataOpsReward()])
def test_graded_rewards_have_unit_range(reward: Any) -> None:
    assert reward.reward_range() == (0.0, 1.0)


def test_binary_soc_reward_is_valid_graded_reward() -> None:
    reward = RewardComputer(BinaryRewardFunction(), domain="soc")
    assert reward.compute("investigate", "investigate").reward == 1.0
    assert reward.compute("investigate", "suppress").reward == 0.0


@pytest.mark.parametrize("domain,reward", [("soc", BinaryRewardFunction()), ("s2p", GradedFinancialRewardFunction()), ("trading", TradingReward()), ("purchasing", PurchasingReward()), ("dataops", DataOpsReward())])
def test_reward_computer_accepts_all_domains(domain: str, reward: Any) -> None:
    result = RewardComputer(reward, domain=domain).compute("a", "a", {})
    assert 0.0 <= result.reward <= 1.0


def test_credit_assigner_handles_immediate_and_delayed_outcomes() -> None:
    assigner = CreditAssigner(temporal_discount=0.95)
    assert assigner.assign(1.0, ["a"], {"a": 1.0})["a"] == 1.0
    delayed = assigner.assign_temporal(1.0, [("a", 0), ("b", 2)])
    assert delayed[0].credit == pytest.approx(1.0)
    assert delayed[1].credit == pytest.approx(0.95**2)


@pytest.mark.parametrize("domain", DOMAINS)
def test_exploration_penalty_ratio_and_epsilon_bound(domain: str) -> None:
    policy = ExplorationPolicy(2, penalty_ratio=PENALTY_RATIOS[domain])
    assert policy.penalty_ratio == PENALTY_RATIOS[domain]
    assert policy.EPSILON_FIRM_STAR == 0.125
    assert policy.select_action([0.8, 0.2], conservation_fraction=0.4).epsilon <= 0.125 * 0.6


def test_exploration_stops_at_full_conservation_fraction() -> None:
    policy = ExplorationPolicy(2)
    assert policy.select_action([0.8, 0.2], conservation_fraction=1.0).epsilon == 0.0


@pytest.mark.parametrize("domain", DOMAINS)
def test_reward_persists_in_domain_ledger(domain: str) -> None:
    store = _store()
    result = RewardComputer(BinaryRewardFunction(), domain=domain).compute("a", "a", {}, decision_id="d1")
    entry_id = RewardComputer(BinaryRewardFunction(), domain=domain).persist(store, result)
    assert store.get_ledger(domain, entry_id)["reward"] == 1.0


@pytest.mark.parametrize("domain", DOMAINS)
def test_sequential_learning_safety_bound(domain: str) -> None:
    policy = ExplorationPolicy(2, penalty_ratio=PENALTY_RATIOS[domain])
    for _ in range(100):
        decision = policy.select_action([0.9, 0.1], conservation_fraction=0.8)
        assert decision.epsilon <= 0.125 * 0.2
    policy.set_conservation_status("RED")
    assert policy.select_action([0.9, 0.1]).epsilon == 0.0


def test_cross_copilot_reward_state_isolated() -> None:
    store = _store()
    soc = RewardComputer(BinaryRewardFunction(), domain="soc")
    trading = RewardComputer(TradingReward(), domain="trading")
    soc.persist(store, soc.compute("a", "a", {}, decision_id="soc-1"))
    assert store.list_ledgers("soc")
    assert store.list_ledgers("trading") == []
    assert trading.compute("a", "a", {"pnl": 50, "max_expected": 100}).reward == 0.5


def test_rl_registry_has_all_five_domains() -> None:
    assert set(RL_PRESET_REGISTRY) == {"soc", "s2p", "trading", "purchasing", "dataops"}
