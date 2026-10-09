from __future__ import annotations

from types import SimpleNamespace

import pytest

from copilot_sdk.graph import GraphStore, InMemoryGraphStore, ScoringPersistenceStore
from copilot_sdk.graph.scoring_persistence import GraphScoringPersistence
from copilot_sdk.graph.tenant_store import TenantScopedGraphStore
from copilot_sdk.scoring.investigation import InvestigationStep, InvestigationTrace, KUtilityStore
from apps.dataops.backend.app.dataops_governance import DataOpsGovernance


@pytest.mark.parametrize("bridge", [False, True])
def test_scoring_state_upsert_filter_and_copy_isolation(bridge: bool) -> None:
    graph = InMemoryGraphStore()
    store = GraphScoringPersistence(graph) if bridge else graph
    assert isinstance(graph, GraphStore)
    assert isinstance(store, ScoringPersistenceStore)
    metadata = {"n_updates": 1, "nested": [1]}
    first = store.save_k_utility("a", "episode", 2, .7, metadata)
    metadata["nested"] = [99]
    store.save_k_utility("b", "episode", 2, .1)
    store.save_k_utility("a", "other", 0, .2)
    assert store.get_k_utilities("a", "episode")[0]["metadata"]["nested"] == [1]
    assert store.save_k_utility("a", "episode", 2, .9, {"n_updates": 2}) == first
    rows = store.get_k_utilities("a", "episode")
    assert len(rows) == 1 and rows[0]["utility"] == .9
    rows[0]["metadata"]["n_updates"] = 99
    assert store.get_k_utilities("a", "episode")[0]["metadata"]["n_updates"] == 2
    assert len(store.get_k_utilities("a", limit=1)) == 1
    assert store.get_k_utilities("a", limit=0) == []
    with pytest.raises(ValueError):
        store.get_k_utilities("a", limit=-1)
    key = store.save_holdout_decision("a", "same", "group1", {"verdict": {"correct": True}})
    store.save_holdout_decision("b", "same", "group1")
    assert store.save_holdout_decision("a", "same", "group2", {"verdict": {"correct": False}}) == key
    assert store.get_holdout_decisions("a", "group1") == []
    rows = store.get_holdout_decisions("a", "group2")
    rows[0]["metadata"]["verdict"]["correct"] = True
    assert store.get_holdout_decisions("a")[0]["metadata"]["verdict"]["correct"] is False
    assert len(store.get_holdout_decisions("b")) == 1


def test_bridge_preserves_tenant_isolation_for_identical_keys() -> None:
    base = InMemoryGraphStore(domain="a")
    one = GraphScoringPersistence(TenantScopedGraphStore(base, "tenant-one"))
    two = GraphScoringPersistence(TenantScopedGraphStore(base, "tenant-two"))
    for store, value in ((one, .1), (two, .9)):
        store.save_k_utility("a", "category", 0, value)
        store.save_holdout_decision("a", "decision", "group", {"value": value})
    assert one.get_k_utilities("a")[0]["utility"] == .1
    assert two.get_k_utilities("a")[0]["utility"] == .9
    assert one.get_holdout_decisions("a")[0]["metadata"]["value"] == .1
    assert two.get_holdout_decisions("a")[0]["metadata"]["value"] == .9


def test_k_learning_retains_update_counts_across_wrappers() -> None:
    graph = InMemoryGraphStore(domain="a")
    store = KUtilityStore(graph, 2, profile="test")
    step = InvestigationStep(0, 1, "factor", .5, 1., "source", [.5]*2, [.5]*2, 0, 1, .1, .2, True)
    trace = InvestigationTrace("episode", "category", 2, [step, step], 0, .1, 1, .2)
    store.update_weights("category", trace, True)
    KUtilityStore(graph, 2, profile="test").update_weights("category", trace, False)
    row = graph.get_k_utilities("a", "category")[0]
    assert row["metadata"]["n_updates"] == 4
    assert row["metadata"]["last_episode_id"] == "episode"
    assert row["utility"] == pytest.approx(.57)
    assert store.get_weights("category")[0] == .5


def test_holdout_verification_reregistration_and_reconstruction() -> None:
    graph = InMemoryGraphStore(domain="dataops")
    governance = DataOpsGovernance(graph, SimpleNamespace(), SimpleNamespace(), profile="test")
    governance.register_holdout("a", "source", "class")
    governance.register_holdout("z", "source", "class")
    verified = governance.verify_holdout("a", {"correct": True})
    assert governance.holdout_status("source")[0]["decision_id"] == "a"
    # Re-registration must preserve verification and return the requested row,
    # even when a different decision sorts ahead of it.
    current = governance.register_holdout("z", "source", "class", [1.])
    assert current["decision_id"] == "z"
    current = governance.register_holdout("a", "new-source", "new-class")
    assert current["verified_at"] == verified["verified_at"]
    restored = DataOpsGovernance(graph, SimpleNamespace(), SimpleNamespace(), profile="test")
    assert restored.abstention("new-source", 1)["should_abstain"] is False
    assert restored.provenance("a")["complete"] is True
    assert len(restored.holdout_status("source")) == 1
    with pytest.raises(KeyError):
        restored.verify_holdout("missing", {})


def test_holdout_production_guard_rejects_memory() -> None:
    with pytest.raises(ValueError, match="AGE-backed"):
        DataOpsGovernance(InMemoryGraphStore(domain="dataops"), None, None, profile="production")


def test_bridge_propagates_backend_failures() -> None:
    class Unavailable(InMemoryGraphStore):
        def save_governance(self, domain: str, key: str, state: dict) -> None:
            raise ConnectionError("unavailable")

    with pytest.raises(ConnectionError, match="unavailable"):
        GraphScoringPersistence(Unavailable()).save_k_utility("a", "category", 0, .5)
