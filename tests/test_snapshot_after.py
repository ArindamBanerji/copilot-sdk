from __future__ import annotations

from pathlib import Path

import pytest

from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore


def _seed(store, domain: str = "test") -> tuple[str, str]:
    decision_id = store.write_decision(
        domain, "quality", "investigate", 0.9, {"severity": 0.8}, {"decision_id": "decision-1"}
    )
    checkpoint_id = "checkpoint-1"
    store.write_centroid_checkpoint(
        checkpoint_id=checkpoint_id,
        domain=domain,
        category="quality",
        action="investigate",
        centroids=[[[0.1]]],
        decisions_count=1,
        verified_count=1,
        iks=1.0,
        shape=[1, 1, 1],
        factor_names_hash="hash",
        decision_id=decision_id,
    )
    return decision_id, checkpoint_id


@pytest.fixture(params=["memory", "sqlite"])
def store(request, tmp_path):
    value = InMemoryGraphStore(domain="test") if request.param == "memory" else SQLiteGraphStore(Path(tmp_path) / "jm.db", domain="test")
    yield value
    value.close()


def test_write_checkpoint_creates_snapshot_after_edge(store):
    decision_id, checkpoint_id = _seed(store)
    assert store.get_checkpoint_lineage("test", checkpoint_id)["decision_id"] == decision_id


def test_get_checkpoint_lineage_returns_decision(store):
    decision_id, checkpoint_id = _seed(store)
    result = store.get_checkpoint_lineage("test", checkpoint_id)
    assert result is not None
    assert result["decision_id"] == decision_id
    assert result["recommended_action"] == "investigate"


def test_get_decision_checkpoints_returns_list(store):
    decision_id, _ = _seed(store)
    store.write_centroid_checkpoint(
        checkpoint_id="checkpoint-2", domain="test", category="quality", action="investigate",
        centroids=[[[0.2]]], decisions_count=2, verified_count=2, iks=1.0, shape=[1, 1, 1],
        factor_names_hash="hash", decision_id=decision_id,
    )
    assert len(store.get_decision_checkpoints("test", decision_id)) == 2


def test_lineage_not_found_returns_none(store):
    assert store.get_checkpoint_lineage("test", "nonexistent") is None


def test_decision_checkpoints_empty_returns_empty(store):
    assert store.get_decision_checkpoints("test", "nonexistent") == []


def test_lineage_domain_scoped(store):
    _, checkpoint_id = _seed(store, "a")
    assert store.get_checkpoint_lineage("b", checkpoint_id) is None


def test_lineage_cross_adapter_parity(tmp_path):
    stores = [InMemoryGraphStore(domain="test"), SQLiteGraphStore(Path(tmp_path) / "parity.db", domain="test")]
    try:
        results = []
        for value in stores:
            decision_id, checkpoint_id = _seed(value)
            results.append(value.get_checkpoint_lineage("test", checkpoint_id)["decision_id"] == decision_id)
        assert results == [True, True]
    finally:
        for value in stores:
            value.close()


def test_backfill_idempotent(age_graph_store):
    store = age_graph_store("trading")
    decision_id = store.write_decision("trading", "quality", "investigate", 0.9, {"x": 1.0})
    store.write_centroid_checkpoint(
        checkpoint_id="backfill-checkpoint", domain="trading", category="quality", action="investigate",
        centroids=[[[0.1]]], decisions_count=1, verified_count=1, iks=1.0, shape=[1, 1, 1],
        factor_names_hash="hash", decision_id=decision_id,
    )
    first = store.backfill_snapshot_after("trading")
    second = store.backfill_snapshot_after("trading")
    assert first["created"] == 0
    assert second["created"] == 0
    assert store.get_checkpoint_lineage("trading", "backfill-checkpoint") is not None
