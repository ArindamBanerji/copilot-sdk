from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from copilot_sdk.graph import GraphStore, InMemoryGraphStore, ProtocolV2GraphStore, SQLiteGraphStore
from copilot_sdk.graph.protocol import L5LearningStore


@pytest.fixture(params=["memory", "sqlite"])
def store(request: pytest.FixtureRequest, tmp_path: Path) -> Any:
    if request.param == "memory":
        return InMemoryGraphStore()
    return SQLiteGraphStore(tmp_path / "l5-centroids.sqlite")


def _parse_iso(value: object) -> datetime:
    assert isinstance(value, str)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _rows_for_sqlite(store: Any, domain: str = "s2p") -> int:
    if not isinstance(store, SQLiteGraphStore):
        return len(store.get_centroids(domain))
    row = store.connection.execute(
        "SELECT COUNT(*) AS n FROM l5_centroids WHERE domain = ?",
        (domain,),
    ).fetchone()
    return int(row["n"])


def test_l5_centroid_architecture_boundary() -> None:
    assert not hasattr(GraphStore, "update_centroid")
    assert not hasattr(GraphStore, "get_centroids")
    assert not hasattr(ProtocolV2GraphStore, "update_centroid")
    assert not hasattr(ProtocolV2GraphStore, "get_centroids")
    assert hasattr(L5LearningStore, "update_centroid")
    assert hasattr(L5LearningStore, "get_centroids")
    assert hasattr(SQLiteGraphStore, "update_centroid")
    assert hasattr(SQLiteGraphStore, "get_centroids")
    assert hasattr(InMemoryGraphStore, "update_centroid")
    assert hasattr(InMemoryGraphStore, "get_centroids")


def test_basic_centroid_write_read_shape_and_types(store: Any) -> None:
    vector = [float(i) / 10.0 for i in range(7)]

    store.update_centroid(
        "s2p",
        "price_variance",
        "auto_approve",
        vector,
        0.125,
        caused_by_decision_id="DEC-1",
    )

    rows = store.get_centroids("s2p")
    assert len(rows) == 1
    row = rows[0]
    assert list(row) == [
        "category",
        "action",
        "vector_json",
        "delta_norm",
        "caused_by_decision_id",
        "updated_at",
    ]
    assert row["category"] == "price_variance"
    assert row["action"] == "auto_approve"
    assert row["vector_json"] == vector
    assert all(isinstance(value, float) for value in row["vector_json"])
    assert row["delta_norm"] == 0.125
    assert row["caused_by_decision_id"] == "DEC-1"
    assert _parse_iso(row["updated_at"])


def test_upsert_overwrites_same_identity_without_duplicates(store: Any) -> None:
    store.update_centroid("s2p", "cat", "act", [1, 2], 0.1, "DEC-old")
    first_updated_at = store.get_centroids("s2p")[0]["updated_at"]

    store.update_centroid("s2p", "cat", "act", [3.5, 4.5], 0.2, "DEC-new")

    rows = store.get_centroids("s2p")
    assert len(rows) == 1
    assert _rows_for_sqlite(store) == 1
    assert rows[0]["vector_json"] == [3.5, 4.5]
    assert rows[0]["delta_norm"] == 0.2
    assert rows[0]["caused_by_decision_id"] == "DEC-new"
    assert _parse_iso(rows[0]["updated_at"])
    assert isinstance(first_updated_at, str)


def test_multiple_centroids_are_sorted_and_domain_isolated(store: Any) -> None:
    store.update_centroid("s2p", "beta", "review", [2], 0.2)
    store.update_centroid("s2p", "alpha", "review", [1], 0.1)
    store.update_centroid("s2p", "alpha", "approve", [0], 0.0)
    store.update_centroid("trading", "alpha", "approve", [9], 0.9)

    assert [
        (row["category"], row["action"], row["vector_json"])
        for row in store.get_centroids("s2p")
    ] == [
        ("alpha", "approve", [0.0]),
        ("alpha", "review", [1.0]),
        ("beta", "review", [2.0]),
    ]
    assert [row["vector_json"] for row in store.get_centroids("trading")] == [[9.0]]
    assert store.get_centroids("missing") == []


def test_domain_scoped_reset_only_clears_matching_domain(store: Any) -> None:
    store.update_centroid("s2p", "cat", "act", [1], 0.1)
    store.update_centroid("trading", "cat", "act", [2], 0.2)

    store.domain_scoped_reset("s2p")

    assert store.get_centroids("s2p") == []
    assert [row["vector_json"] for row in store.get_centroids("trading")] == [[2.0]]


def test_in_memory_reset_clears_all_centroids() -> None:
    store = InMemoryGraphStore()
    store.update_centroid("s2p", "cat", "act", [1], 0.1)
    store.update_centroid("trading", "cat", "act", [2], 0.2)

    store.reset()

    assert store.get_centroids("s2p") == []
    assert store.get_centroids("trading") == []


def test_get_centroids_returns_copy_safe_records(store: Any) -> None:
    original = [1.0, 2.0]
    store.update_centroid("s2p", "cat", "act", original, 0.1)
    original.append(99.0)

    first = store.get_centroids("s2p")
    first[0]["category"] = "mutated"
    first[0]["vector_json"].append(42.0)

    second = store.get_centroids("s2p")
    assert second[0]["category"] == "cat"
    assert second[0]["vector_json"] == [1.0, 2.0]


def test_sqlite_l5_centroids_schema_and_checkpoint_separation(tmp_path: Path) -> None:
    store = SQLiteGraphStore(tmp_path / "schema.sqlite")
    tables = {
        row["name"]
        for row in store.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    assert "l5_centroids" in tables
    assert "centroid_checkpoints" in tables
    columns = {
        row["name"]
        for row in store.connection.execute("PRAGMA table_info(l5_centroids)").fetchall()
    }
    assert {
        "id",
        "domain",
        "category",
        "action",
        "vector_json",
        "delta_norm",
        "caused_by_decision_id",
        "updated_at",
    } <= columns

    store.update_centroid("s2p", "cat", "act", [1], 0.1)
    store.update_centroid("s2p", "cat", "act", [2], 0.2)
    assert _rows_for_sqlite(store) == 1
    checkpoint_count = store.connection.execute(
        "SELECT COUNT(*) AS n FROM centroid_checkpoints"
    ).fetchone()
    assert int(checkpoint_count["n"]) == 0


@pytest.mark.parametrize(
    ("vector", "expected"),
    [
        ([1, 2.5], [1.0, 2.5]),
        ((3, 4.25), [3.0, 4.25]),
        ([], []),
    ],
)
def test_vector_validation_accepts_numeric_iterables(store: Any, vector: Any, expected: list[float]) -> None:
    store.update_centroid("s2p", "cat", "act", vector, 0)

    assert store.get_centroids("s2p")[0]["vector_json"] == expected


@pytest.mark.parametrize(
    "bad_vector",
    [
        "123",
        b"123",
        {"a": 1},
        object(),
        [1, "bad"],
    ],
)
def test_vector_validation_rejects_bad_vectors(store: Any, bad_vector: Any) -> None:
    with pytest.raises((TypeError, ValueError)):
        store.update_centroid("s2p", "cat", "act", bad_vector, 0.1)


def test_bad_delta_norm_is_rejected(store: Any) -> None:
    with pytest.raises((TypeError, ValueError)):
        store.update_centroid("s2p", "cat", "act", [1.0], "bad-delta")
