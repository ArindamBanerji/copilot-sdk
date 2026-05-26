from __future__ import annotations

import pytest

from copilot_sdk.graph import InMemoryGraphStore


def _write(store: InMemoryGraphStore, domain: str, index: int, category: str = "alpha") -> str:
    return store.write_decision(
        domain,
        category,
        "approve",
        0.8,
        {"risk": float(index)},
        metadata={"decision_id": f"{domain}-{index}", "entity_id": f"entity-{index}", "created_at": float(index)},
    )


def test_memory_write_decision_returns_id_and_stores_fields():
    store = InMemoryGraphStore()

    decision_id = store.write_decision(
        "mock",
        "alpha",
        "approve",
        0.82,
        {"amount": 0.2},
        metadata={"entity_id": "invoice-1", "source": "unit", "created_at": 10.0},
    )

    decision = store.get_decision(decision_id)
    assert decision["decision_id"] == decision_id
    assert decision["domain"] == "mock"
    assert decision["entity_id"] == "invoice-1"
    assert decision["category"] == "alpha"
    assert decision["recommended_action"] == "approve"
    assert decision["confidence"] == 0.82
    assert decision["factors"] == {"amount": 0.2}
    assert decision["metadata"]["source"] == "unit"


def test_memory_write_outcome_links_to_decision():
    store = InMemoryGraphStore()
    decision_id = _write(store, "mock", 1)

    store.write_outcome(decision_id, "approve", True, metadata={"verified_at": 20.0})

    verified = store.get_verified_decisions("mock")
    assert len(verified) == 1
    assert verified[0]["decision_id"] == decision_id
    assert verified[0]["actual_action"] == "approve"
    assert verified[0]["is_correct"] is True
    assert verified[0]["verified_at"] == 20.0


def test_memory_write_outcome_missing_decision_raises():
    store = InMemoryGraphStore()

    with pytest.raises(KeyError):
        store.write_outcome("missing", "approve", True)


def test_memory_counts_empty_and_after_outcomes():
    store = InMemoryGraphStore()
    assert store.count_verified("mock") == 0
    assert store.count_correct("mock") == 0

    first = _write(store, "mock", 1)
    second = _write(store, "mock", 2)
    _write(store, "other", 3)
    store.write_outcome(first, "approve", True)
    store.write_outcome(second, "approve", False)

    assert store.count_decisions("mock") == 2
    assert store.count_verified("mock") == 2
    assert store.count_correct("mock") == 1
    assert store.count_verified("other") == 0


def test_memory_get_decision_missing_returns_none():
    assert InMemoryGraphStore().get_decision("missing") is None


def test_memory_get_decisions_all_category_and_limit():
    store = InMemoryGraphStore()
    _write(store, "mock", 1, category="alpha")
    _write(store, "mock", 2, category="beta")
    _write(store, "mock", 3, category="alpha")

    assert [d["entity_id"] for d in store.get_decisions("mock")] == ["entity-1", "entity-2", "entity-3"]
    assert [d["entity_id"] for d in store.get_decisions("mock", category="alpha")] == ["entity-1", "entity-3"]
    assert [d["entity_id"] for d in store.get_decisions("mock", limit=2)] == ["entity-1", "entity-2"]


def test_memory_domain_isolation():
    store = InMemoryGraphStore()
    first = _write(store, "mock", 1)
    second = _write(store, "other", 2)
    store.write_outcome(first, "approve", True)
    store.write_outcome(second, "approve", False)

    assert [d["decision_id"] for d in store.get_all_decisions("mock")] == [first]
    assert [d["decision_id"] for d in store.get_all_decisions("other")] == [second]
    assert store.count_correct("mock") == 1
    assert store.count_correct("other") == 0


def test_memory_save_centroids_stores():
    store = InMemoryGraphStore()

    store.save_centroids(
        "mock",
        "alpha",
        [[0.1, 0.2]],
        metadata={"iks": 3.5, "source": "unit"},
        decision_id="decision-1",
    )

    checkpoints = store.get_centroid_checkpoints("mock")
    assert len(checkpoints) == 1
    assert checkpoints[0]["domain"] == "mock"
    assert checkpoints[0]["decision_id"] == "decision-1"
    assert checkpoints[0]["category"] == "alpha"
    assert checkpoints[0]["centroids"] == [[0.1, 0.2]]
    assert checkpoints[0]["metadata"] == {"iks": 3.5, "source": "unit"}
    assert checkpoints[0]["created_at"]


def test_memory_load_latest_centroids_filters_domain():
    store = InMemoryGraphStore()
    store.save_centroids("alpha", "cat", [[0.0]])
    store.save_centroids("beta", "cat", [[1.0]])

    assert store.load_latest_centroids("alpha") == [[0.0]]
    assert store.load_latest_centroids("beta") == [[1.0]]


def test_memory_checkpoint_time_filter():
    store = InMemoryGraphStore()
    store.save_centroids("mock", "alpha", [[0.1]], decision_id="old", checkpoint_time="2026-05-01T00:00:00Z")
    store.save_centroids("mock", "alpha", [[0.2]], decision_id="new", checkpoint_time="2026-05-02T00:00:00Z")

    checkpoints = store.get_centroid_checkpoints(
        "mock",
        checkpoint_time_start="2026-05-01T12:00:00Z",
    )

    assert [checkpoint["decision_id"] for checkpoint in checkpoints] == ["new"]


def test_memory_decision_time_filter():
    store = InMemoryGraphStore()
    store.save_centroids(
        "mock",
        "alpha",
        [[0.1]],
        decision_id="outside",
        decision_time_start="2026-05-01T00:00:00Z",
        decision_time_end="2026-05-03T00:00:00Z",
    )
    store.save_centroids(
        "mock",
        "alpha",
        [[0.2]],
        decision_id="inside",
        decision_time_start="2026-05-02T00:00:00Z",
        decision_time_end="2026-05-02T12:00:00Z",
    )

    checkpoints = store.get_centroid_checkpoints(
        "mock",
        decision_time_start="2026-05-01T12:00:00Z",
        decision_time_end="2026-05-02T18:00:00Z",
    )

    assert [checkpoint["decision_id"] for checkpoint in checkpoints] == ["inside"]


def test_memory_centroid_checkpoints_limit():
    store = InMemoryGraphStore()
    for index in range(4):
        store.save_centroids("mock", "alpha", [[float(index)]], decision_id=f"decision-{index}")

    checkpoints = store.get_centroid_checkpoints("mock", limit=2)

    assert [checkpoint["decision_id"] for checkpoint in checkpoints] == [
        "decision-2",
        "decision-3",
    ]


def test_memory_store_archive():
    store = InMemoryGraphStore()
    ids = [_write(store, "mock", index) for index in range(4)]
    for decision_id in ids:
        store.write_outcome(decision_id, "approve", True)

    assert store.archive_old_decisions("mock", keep_recent=2) == 2

    assert [d["decision_id"] for d in store.get_all_decisions("mock")] == ids[2:]
    assert store.count_archived("mock") == 2
    assert store.count_verified("mock") == 2


def test_memory_get_evolution_events():
    store = InMemoryGraphStore()
    store.save_evolution_event("mock", "variant_created", "coverage_gap", "variant-1", {"seed": 7})
    store.save_evolution_event("other", "variant_created", "coverage_gap", "variant-2")

    events = store.get_evolution_events("mock")

    assert len(events) == 1
    assert events[0]["domain"] == "mock"
    assert events[0]["metadata"] == {"seed": 7}


def test_memory_rl_state_roundtrip_and_upsert():
    store = InMemoryGraphStore(domain="mock")

    store.save_rl_state("thompson", {"alpha": [1.0]})
    store.save_rl_state("thompson", {"alpha": [2.0], "beta": [3.0]})

    assert store.load_rl_state("thompson") == {"alpha": [2.0], "beta": [3.0]}
    assert store.load_rl_state("missing") is None


def test_memory_rl_state_domain_isolated():
    alpha = InMemoryGraphStore(domain="alpha")
    beta = InMemoryGraphStore(domain="beta")

    alpha.save_rl_state("thompson", {"alpha": [1.0]})
    beta.save_rl_state("thompson", {"alpha": [2.0]})

    assert alpha.load_rl_state("thompson") == {"alpha": [1.0]}
    assert beta.load_rl_state("thompson") == {"alpha": [2.0]}


def test_memory_rl_state_uses_copies():
    store = InMemoryGraphStore(domain="mock")
    data = {"alpha": [1.0]}

    store.save_rl_state("thompson", data)
    data["alpha"].append(2.0)
    loaded = store.load_rl_state("thompson")
    loaded["alpha"].append(3.0)

    assert store.load_rl_state("thompson") == {"alpha": [1.0]}


def test_memory_reset_clears_and_close_noop():
    store = InMemoryGraphStore()
    decision_id = _write(store, "mock", 1)
    store.write_outcome(decision_id, "approve", True)
    store.save_centroids("mock", "alpha", [[1.0]], decision_id=decision_id)
    store.save_evolution_event("mock", "event")
    store.save_rl_state("thompson", {"alpha": [1.0]})

    store.reset()
    store.close()

    assert store.get_all_decisions("mock") == []
    assert store.count_verified("mock") == 0
    assert store.get_centroid_checkpoints("mock") == []
    assert store.get_evolution_events("mock") == []
    assert store.load_rl_state("thompson") is None
