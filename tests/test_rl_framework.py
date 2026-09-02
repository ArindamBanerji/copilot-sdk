"""Contract tests for the domain-neutral RL framework."""

from __future__ import annotations

import random
from collections.abc import Mapping
from typing import Any

import pytest

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.rl import CreditAssigner, ExplorationPolicy, RewardComputer
from copilot_sdk.rl.reward import DomainRewardFunction


class GradedFunction:
    def compute(self, recommended_action: str, actual_action: str, outcome: Mapping[str, Any]) -> float:
        del recommended_action, actual_action
        return float(outcome.get("quality", 0.0))


class BinaryFunction:
    def compute(self, recommended_action: str, actual_action: str, outcome: Mapping[str, Any]) -> float:
        del outcome
        return 1.0 if recommended_action == actual_action else 0.0


def test_reward_computer_accepts_graded_function() -> None:
    result = RewardComputer(GradedFunction(), domain="dataops").compute("a", "b", {"quality": 0.65})
    assert result.reward == pytest.approx(0.65)
    assert result.binary_reward == 0.0


def test_reward_computer_clips_above_one() -> None:
    result = RewardComputer(GradedFunction()).compute("a", "b", {"quality": 3.0})
    assert result.reward == 1.0


def test_reward_computer_clips_below_zero() -> None:
    result = RewardComputer(GradedFunction()).compute("a", "b", {"quality": -1.0})
    assert result.reward == 0.0


def test_binary_is_graded_endpoint_for_success() -> None:
    binary = RewardComputer(BinaryFunction()).compute("a", "a")
    graded = RewardComputer(GradedFunction()).compute("a", "a", {"quality": 1.0})
    assert binary.reward == graded.reward == 1.0


def test_binary_is_graded_endpoint_for_failure() -> None:
    binary = RewardComputer(BinaryFunction()).compute("a", "b")
    graded = RewardComputer(GradedFunction()).compute("a", "b", {"quality": 0.0})
    assert binary.reward == graded.reward == 0.0


def test_reward_result_carries_decision_and_domain() -> None:
    result = RewardComputer(BinaryFunction(), domain="s2p").compute("a", "a", decision_id="D-1")
    assert result.decision_id == "D-1"
    assert result.domain == "s2p"


def test_reward_persists_through_graph_store() -> None:
    store = InMemoryGraphStore(domain="s2p")
    computer = RewardComputer(BinaryFunction(), domain="s2p")
    result = computer.compute("approve", "approve", decision_id="D-2")
    entry_id = computer.persist(store, result)
    assert store.get_ledger("s2p", entry_id) == {
        "entry_id": entry_id,
        "decision_id": "D-2",
        "reward": 1.0,
        "binary_reward": 1.0,
        "domain": "s2p",
        "breakdown": {"raw": 1.0, "binary": 1.0},
        "metadata": {},
    }


def test_reward_persistence_requires_graph_store_contract() -> None:
    result = RewardComputer(BinaryFunction()).compute("a", "a")
    with pytest.raises(RuntimeError, match="save_ledger"):
        RewardComputer(BinaryFunction()).persist(object(), result)


def test_credit_assigner_distributes_uniformly() -> None:
    assigned = CreditAssigner(temporal_discount=1.0).assign(1.0, ["a", "b"])
    assert assigned == {"a": 0.5, "b": 0.5}


def test_credit_assigner_weights_factor_contributions() -> None:
    assigned = CreditAssigner(temporal_discount=1.0).assign(
        1.0, ["a", "b"], {"a": 3.0, "b": 1.0}
    )
    assert assigned == {"a": 0.75, "b": 0.25}


def test_credit_assigner_discounts_decision_age() -> None:
    assigned = CreditAssigner(temporal_discount=0.5).assign(1.0, ["a"], decision_age=2)
    assert assigned["a"] == pytest.approx(0.25)


def test_credit_assigner_empty_factors_is_empty() -> None:
    assert CreditAssigner().assign(1.0, []) == {}


def test_credit_assigner_temporal_records_delayed_credit() -> None:
    records = CreditAssigner(0.5).assign_temporal(1.0, [("D0", 0), ("D2", 2)])
    assert [record.target_id for record in records] == ["D0", "D2"]
    assert [record.credit for record in records] == [1.0, 0.25]


def test_credit_assigner_rejects_invalid_discount() -> None:
    with pytest.raises(ValueError):
        CreditAssigner(0.0)


def test_exploration_ceiling_is_canonical() -> None:
    assert ExplorationPolicy.EPSILON_FIRM_STAR == pytest.approx(0.125)


def test_exploration_rejects_epsilon_above_ceiling() -> None:
    with pytest.raises(ValueError):
        ExplorationPolicy(2, epsilon=0.126)


def test_exploration_green_can_explore(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(random, "random", lambda: 0.0)
    monkeypatch.setattr(random, "randrange", lambda _n: 1)
    decision = ExplorationPolicy(2, epsilon=0.125).select_action([0.9, 0.1])
    assert decision.action == 1
    assert decision.explored is True
    assert decision.epsilon == 0.125


@pytest.mark.parametrize("status", ["AMBER", "RED"])
def test_exploration_is_disabled_outside_green(status: str) -> None:
    policy = ExplorationPolicy(2, epsilon=0.125)
    policy.set_conservation_status(status)
    decision = policy.select_action([0.1, 0.9])
    assert decision.action == 1
    assert decision.explored is False
    assert decision.epsilon == 0.0


def test_exploration_reports_conservation_state() -> None:
    policy = ExplorationPolicy(2)
    policy.set_conservation_status("RED")
    assert policy.conservation_status == "RED"
    assert policy.select_action([0.8, 0.2]).conservation_status == "RED"


def test_exploration_rejects_wrong_action_value_shape() -> None:
    with pytest.raises(ValueError):
        ExplorationPolicy(2).select_action([1.0])


def test_domain_reward_function_is_runtime_protocol() -> None:
    assert isinstance(BinaryFunction(), DomainRewardFunction)
