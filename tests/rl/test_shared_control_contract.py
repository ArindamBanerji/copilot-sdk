"""Contract regression tests: opt-in RL primitives never change scorer APIs."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import random

import pytest

from copilot_sdk.graph import GraphStore, InMemoryGraphStore
from copilot_sdk.graph.protocol import GraphStore as ProtocolGraphStore
from copilot_sdk.rl import (
    ExplorationBudget, LegacyRewardAdapter, MappingRewardFunction,
    OutcomeReceipt, RewardFunction, TemporalCreditAssigner, read_outcome_receipt,
)
from copilot_sdk.rl.reward import RewardFunction as LegacyRewardFunction
from copilot_sdk.rl.reward_protocol import compute_reward, normalize_reward


def receipt(**changes):
    data = dict(domain="soc", decision_id="decision-1", actor="analyst-1",
                evidence={"refs": ["ticket-1"]},
                verification={"verified": True, "verification_id": "verify-1"},
                learning_effect={"temporal_credit": {"earlier": 0.2}},
                reward=1.0, provenance={"formula_version": "soc-v1"})
    return OutcomeReceipt(**(data | changes))


def snapshot(**changes):
    return dict(category="test", status="GREEN", valid=True, paused=False,
                sufficient_evidence=True, consumed_budget=2, allowed_budget=10) | changes


def test_existing_imports_keep_identity():
    assert GraphStore is ProtocolGraphStore
    assert isinstance(InMemoryGraphStore(), GraphStore)
    assert RewardFunction is LegacyRewardFunction


def test_receipt_roundtrip_and_deep_immutability():
    source = {"refs": ["ticket-1"]}
    original = receipt(evidence=source)
    source["refs"].append("mutated")
    assert original.evidence["refs"] == ("ticket-1",)
    with pytest.raises(TypeError):
        original.learning_effect["temporal_credit"]["earlier"] = 0.9
    exported = original.to_dict()
    exported["evidence"]["refs"].append("changed")
    restored = OutcomeReceipt.from_dict(json.loads(json.dumps(original.to_dict())))
    assert restored == original
    assert restored.payload_hash == original.payload_hash


def test_receipt_retry_identity_and_conflict_detection():
    original = receipt()
    replay = OutcomeReceipt.from_dict(original.to_dict())
    conflicting = replace(original, reward=0.0)
    assert original.receipt_id == replay.receipt_id == conflicting.receipt_id
    assert original.payload_hash == replay.payload_hash != conflicting.payload_hash
    assert receipt(domain="s2p").receipt_id != original.receipt_id
    # A second verification cannot mint a second learning identity.
    assert receipt(verification={"verified": True, "verification_id": "verify-2"}).receipt_id == original.receipt_id


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -0.1, 1.1, True])
def test_receipt_rejects_bad_reward(value):
    with pytest.raises(ValueError):
        receipt(reward=value)


@pytest.mark.parametrize("verification", [{}, {"verified": "true", "verification_id": "v"}, {"verified": True}])
def test_receipt_never_infers_verification(verification):
    with pytest.raises(ValueError):
        receipt(verification=verification)


def test_legacy_read_is_explicit_bounded_and_preserves_raw():
    now = datetime(2026, 9, 13, tzinfo=timezone.utc)
    legacy = receipt().to_dict()
    legacy.pop("reward")
    legacy["reward_raw"] = -0.5
    for deadline in (None, now, now - timedelta(seconds=1)):
        with pytest.raises(ValueError):
            read_outcome_receipt(legacy, now=now, legacy_until=deadline)
    migrated = read_outcome_receipt(legacy, now=now, legacy_until=now + timedelta(days=1), legacy_reward_range=(-1, 1))
    assert migrated.reward == 0.25
    assert migrated.provenance["reward_raw"] == -0.5
    assert "reward_raw" not in migrated.to_dict()


def test_canonical_precedence_does_not_downgrade_bad_receipt():
    now = datetime.now(timezone.utc)
    canonical = receipt()
    assert read_outcome_receipt({"outcome_receipt": canonical.to_dict(), "reward_raw": 0}, now=now) == canonical
    with pytest.raises((TypeError, ValueError)):
        read_outcome_receipt({"outcome_receipt": {}, "reward_raw": 1}, now=now, legacy_until=now + timedelta(days=1))
    with pytest.raises(ValueError, match="conflicts"):
        read_outcome_receipt({"outcome_receipt": canonical.to_dict(), "domain": "s2p"}, now=now)


def test_mapping_reward_adapter_calls_domain_once():
    class Domain:
        calls = 0

        def compute(self, recommended, actual, outcome):
            self.calls += 1
            return 1.0 if recommended == actual else -1.0

    domain = Domain()
    adapter = LegacyRewardAdapter(domain, (-1, 1))
    assert isinstance(adapter, MappingRewardFunction)
    result = compute_reward(adapter, {"recommended_action": "close"}, {"actual_action": "escalate"}, formula_version="test-v1")
    assert domain.calls == 1
    assert result.raw == -1 and result.reward == result.binary_reward == 0


@pytest.mark.parametrize("raw,bounds", [(2, (0, 1)), (0, (1, 1)), (0, (1, -1)), (float("nan"), (0, 1)), (0, (0, float("inf")))])
def test_reward_range_errors_are_not_clipped(raw, bounds):
    with pytest.raises(ValueError):
        normalize_reward(raw, bounds)


def test_temporal_credit_discount_cap_and_empty_history():
    assigner = TemporalCreditAssigner(discount=0.5, chain_budget=0.5)
    history = [{"decision_id": "a", "delay": 1}, {"decision_id": "b", "delay": 2}]
    credits = assigner.assign("now", 0.8, history)
    assert sum(credits.values()) == pytest.approx(0.4)
    assert credits["a"] == pytest.approx(2 * credits["b"])
    assert assigner.assign("now", 0.8, []) == {}
    assert assigner.assign("now", 0, history) == {"a": 0, "b": 0}


@pytest.mark.parametrize("history", [
    [{"decision_id": "a", "delay": -1}], [{"decision_id": "now", "delay": 0}],
    [{"decision_id": "a", "delay": 0}, {"decision_id": "a", "delay": 1}],
    [{"decision_id": "a", "delay": float("nan")}],
])
def test_temporal_credit_rejects_invalid_or_duplicate_history(history):
    with pytest.raises(ValueError):
        TemporalCreditAssigner().assign("now", 1, history)


@pytest.mark.parametrize("changes", [
    {"status": "RED"}, {"status": "AMBER"}, {"valid": False}, {"paused": True},
    {"sufficient_evidence": False}, {"category": "other"}, {"consumed_budget": float("nan")},
    {"consumed_budget": -1}, {"allowed_budget": 0}, {"allowed_budget": "invalid"},
])
def test_exploration_fails_closed(changes):
    budget = ExplorationBudget()
    assert budget.epsilon(snapshot(**changes), "test") == 0
    assert not budget.should_explore(snapshot(**changes), "test", rng=random.Random(42))


def test_exploration_equation_and_no_implicit_missing_gates():
    budget = ExplorationBudget(0.1)
    assert budget.epsilon(snapshot(), "test") == pytest.approx(0.08)
    assert budget.epsilon(snapshot(consumed_budget=15), "test") == 0
    assert budget.epsilon(None, "test") == 0
    for key in snapshot():
        incomplete = snapshot()
        incomplete.pop(key)
        assert budget.epsilon(incomplete, "test") == 0
    with pytest.raises(ValueError):
        ExplorationBudget(0.126)
