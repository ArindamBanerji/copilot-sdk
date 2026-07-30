from __future__ import annotations

import pytest

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore


def _stores(tmp_path):
    return [
        InMemoryGraphStore(domain="soc"),
        SQLiteGraphStore(tmp_path / "global.db", domain="soc"),
    ]


def _write_status(store, status_id, domain, computed_at=None):
    store.write_conservation_status(
        status_id,
        domain,
        3,
        0.8,
        0.7,
        0.6,
        3,
        2,
        "GREEN",
        "v2",
    )
    if computed_at is not None:
        if isinstance(store, SQLiteGraphStore):
            store.connection.execute(
                "UPDATE conservation_snapshots SET computed_at = ? WHERE snapshot_id = ?",
                (computed_at, status_id),
            )
            store.connection.commit()
        else:
            store._conservation_snapshots[status_id]["computed_at"] = computed_at


@pytest.mark.parametrize("store_index", [0, 1], ids=["memory", "sqlite"])
def test_latest_conservation_per_domain(tmp_path, store_index):
    store = _stores(tmp_path)[store_index]
    _write_status(store, "soc-old", "soc", 1.0)
    _write_status(store, "soc-new", "soc", 2.0)
    _write_status(store, "trading-only", "trading", 1.5)

    latest = store.get_latest_conservation_statuses()
    assert len(latest) == 2
    assert {row["domain"] for row in latest} == {"soc", "trading"}
    assert next(row for row in latest if row["domain"] == "soc")["status_id"] == "soc-new"


def test_latest_conservation_empty_domain():
    assert InMemoryGraphStore(domain="soc").get_latest_conservation_statuses(["s2p"]) == []


class _FailingGlobalStore(InMemoryGraphStore):
    def get_latest_conservation_statuses(self, domains=None):
        raise RuntimeError("graph unavailable")


def test_latest_conservation_graph_error():
    with pytest.raises(RuntimeError, match="graph unavailable"):
        _FailingGlobalStore(domain="soc").get_latest_conservation_statuses()


@pytest.mark.parametrize("store_index", [0, 1], ids=["memory", "sqlite"])
def test_iks_trajectory_chronological(tmp_path, store_index):
    store = _stores(tmp_path)[store_index]
    for index, domain in enumerate(("soc", "trading", "soc", "trading", "soc")):
        store.save_centroids(
            domain,
            "default",
            [[float(index)]],
            metadata={"iks": float(index)},
            decision_id=f"d-{index}",
        )
    trajectory = store.get_iks_trajectory()
    assert [(row["domain"], row["iks"]) for row in trajectory] == [
        ("soc", 0.0),
        ("soc", 2.0),
        ("soc", 4.0),
        ("trading", 1.0),
        ("trading", 3.0),
    ]


@pytest.mark.parametrize("store_index", [0, 1], ids=["memory", "sqlite"])
def test_iks_trajectory_deduplicates_v2_legacy(tmp_path, store_index):
    store = _stores(tmp_path)[store_index]
    store.save_centroids(
        "soc", "default", [[1.0]], metadata={"iks": 0.4}, decision_id="d-1"
    )
    store.write_centroid_checkpoint(
        "v2-1",
        "soc",
        "default",
        "approve",
        [[2.0]],
        1,
        1,
        0.9,
        [1, 1],
        "hash",
        metadata={"decision_id": "d-1"},
    )
    trajectory = store.get_iks_trajectory()
    assert len(trajectory) == 1
    assert trajectory[0]["checkpoint_id"] == "v2-1"


@pytest.mark.parametrize("include_v2", [False, True])
def test_checkpoint_include_v2(tmp_path, include_v2):
    store = SQLiteGraphStore(tmp_path / f"checkpoint-{include_v2}.db", domain="soc")
    store.save_centroids(
        "soc", "default", [[1.0]], metadata={"iks": 0.4}, decision_id="d-1"
    )
    store.write_centroid_checkpoint(
        "v2-1", "soc", "default", "approve", [[2.0]], 1, 1, 0.9,
        [1, 1], "hash", metadata={"decision_id": "d-1"},
    )
    checkpoints = store.get_centroid_checkpoints("soc", include_v2=include_v2)
    assert len(checkpoints) == (2 if include_v2 else 1)
