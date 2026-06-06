from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from copilot_sdk.graph import GraphStore, InMemoryGraphStore, ProtocolV2GraphStore, SQLiteGraphStore
from copilot_sdk.graph.protocol import L5LearningStore


FORBIDDEN_WELFORD = {
    "confirmed_mean",
    "overridden_mean",
    "m2_confirmed",
    "m2_overridden",
    "count_confirmed",
    "count_overridden",
}


@pytest.fixture(params=["memory", "sqlite"])
def store(request: pytest.FixtureRequest, tmp_path: Path) -> Any:
    if request.param == "memory":
        return InMemoryGraphStore()
    return SQLiteGraphStore(tmp_path / "l5-dk.sqlite")


def _parse_iso(value: object) -> datetime:
    assert isinstance(value, str)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _sqlite_rows(store: Any, domain: str) -> list[dict[str, Any]]:
    if not isinstance(store, SQLiteGraphStore):
        return list(store._l5_dk_weights.get(domain, []))
    return [
        dict(row)
        for row in store.connection.execute(
            """
            SELECT id, domain, weight_json, n_decisions_used, computed_at,
                   supersedes_id, is_current, created_at
            FROM l5_dk_weights
            WHERE domain = ?
            ORDER BY id
            """,
            (domain,),
        ).fetchall()
    ]


def test_l5_dk_architecture_boundary() -> None:
    assert not hasattr(GraphStore, "update_dk_weights")
    assert not hasattr(GraphStore, "get_dk_weights")
    assert not hasattr(ProtocolV2GraphStore, "update_dk_weights")
    assert not hasattr(ProtocolV2GraphStore, "get_dk_weights")
    assert hasattr(L5LearningStore, "update_dk_weights")
    assert hasattr(L5LearningStore, "get_dk_weights")
    assert hasattr(SQLiteGraphStore, "update_dk_weights")
    assert hasattr(SQLiteGraphStore, "get_dk_weights")
    assert hasattr(InMemoryGraphStore, "update_dk_weights")
    assert hasattr(InMemoryGraphStore, "get_dk_weights")


def test_first_write_read_shape_and_types(store: Any) -> None:
    tensor = [[float(c * 7 + d) for d in range(7)] for c in range(5)]

    store.update_dk_weights("s2p", tensor, n_decisions_used=12, computed_at=123.5)

    row = store.get_dk_weights("s2p")
    assert row is not None
    assert list(row) == [
        "weight_json",
        "n_decisions_used",
        "computed_at",
        "supersedes_id",
        "created_at",
        "domain",
    ]
    assert row["weight_json"] == tensor
    assert all(isinstance(value, float) for values in row["weight_json"] for value in values)
    assert row["n_decisions_used"] == 12
    assert row["computed_at"] == 123.5
    assert row["supersedes_id"] is None
    assert _parse_iso(row["created_at"])
    assert row["domain"] == "s2p"
    assert FORBIDDEN_WELFORD.isdisjoint(row)


def test_dataops_six_by_six_tensor_roundtrip(store: Any) -> None:
    tensor = [[float(c + d / 10) for d in range(6)] for c in range(6)]

    store.update_dk_weights("dataops", tensor, n_decisions_used=0, computed_at=456)

    row = store.get_dk_weights("dataops")
    assert row is not None
    assert row["weight_json"] == tensor
    assert row["n_decisions_used"] == 0
    assert row["computed_at"] == 456.0


def test_version_history_current_row_and_supersedes_chain(store: Any) -> None:
    store.update_dk_weights("s2p", [[1.0, 2.0]], 1, 10.0)
    first_rows = _sqlite_rows(store, "s2p")
    first_id = int(first_rows[-1]["id"])

    store.update_dk_weights("s2p", [[3.0, 4.0]], 2, 20.0)
    second_rows = _sqlite_rows(store, "s2p")
    second_id = int(second_rows[-1]["id"])

    store.update_dk_weights("s2p", [[5.0, 6.0]], 3, 30.0)
    rows = _sqlite_rows(store, "s2p")
    current_rows = [row for row in rows if bool(row["is_current"])]

    assert len(rows) == 3
    assert len(current_rows) == 1
    assert rows[0]["supersedes_id"] is None
    assert int(rows[1]["supersedes_id"]) == first_id
    assert int(rows[2]["supersedes_id"]) == second_id
    assert int(rows[1]["supersedes_id"]) != int(rows[1]["id"])
    assert int(rows[2]["supersedes_id"]) != int(rows[2]["id"])
    assert not bool(rows[0]["is_current"])
    assert not bool(rows[1]["is_current"])
    assert bool(rows[2]["is_current"])

    current = store.get_dk_weights("s2p")
    assert current is not None
    assert current["weight_json"] == [[5.0, 6.0]]
    assert current["n_decisions_used"] == 3
    assert current["computed_at"] == 30.0


def test_domain_isolation_and_reset(store: Any) -> None:
    store.update_dk_weights("s2p", [[1.0]], 1, 1.0)
    store.update_dk_weights("s2p", [[2.0]], 2, 2.0)
    store.update_dk_weights("trading", [[9.0]], 9, 9.0)

    assert store.get_dk_weights("trading")["weight_json"] == [[9.0]]

    store.domain_scoped_reset("s2p")

    assert store.get_dk_weights("s2p") is None
    assert store.get_dk_weights("trading")["weight_json"] == [[9.0]]
    assert _sqlite_rows(store, "s2p") == []
    assert len(_sqlite_rows(store, "trading")) == 1


def test_in_memory_reset_clears_all_dk_weights() -> None:
    store = InMemoryGraphStore()
    store.update_dk_weights("s2p", [[1.0]], 1, 1.0)
    store.update_dk_weights("trading", [[2.0]], 2, 2.0)

    store.reset()

    assert store.get_dk_weights("s2p") is None
    assert store.get_dk_weights("trading") is None
    assert store._l5_dk_weight_counter == 0


def test_get_dk_weights_returns_copy_safe_tensor(store: Any) -> None:
    tensor = [[1.0, 2.0]]
    store.update_dk_weights("s2p", tensor, 1, 1.0)
    tensor[0].append(99.0)

    first = store.get_dk_weights("s2p")
    assert first is not None
    first["weight_json"][0].append(42.0)

    second = store.get_dk_weights("s2p")
    assert second is not None
    assert second["weight_json"] == [[1.0, 2.0]]


def test_sqlite_get_dk_weights_rejects_corrupt_ragged_json(tmp_path: Path) -> None:
    store = SQLiteGraphStore(tmp_path / "corrupt.sqlite")
    store.update_dk_weights("s2p", [[0.1, 0.2], [0.3, 0.4]], 2, 11.0)
    store.connection.execute(
        """
        UPDATE l5_dk_weights
        SET weight_json = ?
        WHERE domain = ? AND is_current = 1
        """,
        ("[[0.1],[0.2,0.3]]", "s2p"),
    )
    store.connection.commit()

    with pytest.raises((TypeError, ValueError)):
        store.get_dk_weights("s2p")


def test_sqlite_schema_current_index_and_no_welford(tmp_path: Path) -> None:
    store = SQLiteGraphStore(tmp_path / "schema.sqlite")
    tables = {
        row["name"]
        for row in store.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    assert "l5_dk_weights" in tables

    columns = {
        row["name"]
        for row in store.connection.execute("PRAGMA table_info(l5_dk_weights)").fetchall()
    }
    assert {
        "id",
        "domain",
        "weight_json",
        "n_decisions_used",
        "computed_at",
        "supersedes_id",
        "is_current",
        "created_at",
    } <= columns
    assert FORBIDDEN_WELFORD.isdisjoint(columns)

    indexes = {
        row["name"]
        for row in store.connection.execute("PRAGMA index_list(l5_dk_weights)").fetchall()
    }
    assert "idx_l5_dk_weights_current_domain" in indexes
    create_sql = store.connection.execute(
        """
        SELECT sql FROM sqlite_master
        WHERE type = 'table' AND name = 'l5_dk_weights'
        """
    ).fetchone()["sql"]
    assert "UNIQUE(domain)" not in create_sql


@pytest.mark.parametrize(
    ("tensor", "expected"),
    [
        ([[1, 2.5], [3, 4]], [[1.0, 2.5], [3.0, 4.0]]),
        (((1, 2), (3, 4)), [[1.0, 2.0], [3.0, 4.0]]),
    ],
)
def test_tensor_validation_accepts_numeric_2d_iterables(
    store: Any,
    tensor: Any,
    expected: list[list[float]],
) -> None:
    store.update_dk_weights("s2p", tensor, 1, 1.0)

    assert store.get_dk_weights("s2p")["weight_json"] == expected


@pytest.mark.parametrize(
    "bad_tensor",
    [
        [0.1, 0.2],
        [],
        [[]],
        [[1.0], [2.0, 3.0]],
        "12",
        b"12",
        {"row": [1.0]},
        ["12"],
        [b"12"],
        [{"row": 1.0}],
        object(),
        [[1.0, "bad"]],
    ],
)
def test_tensor_validation_rejects_bad_tensors(store: Any, bad_tensor: Any) -> None:
    with pytest.raises((TypeError, ValueError)):
        store.update_dk_weights("s2p", bad_tensor, 1, 1.0)


def test_scalar_validation(store: Any) -> None:
    store.update_dk_weights("s2p", [[1.0]], 0, 1.0)
    assert store.get_dk_weights("s2p")["n_decisions_used"] == 0

    with pytest.raises((TypeError, ValueError)):
        store.update_dk_weights("s2p", [[1.0]], -1, 1.0)
    with pytest.raises((TypeError, ValueError)):
        store.update_dk_weights("s2p", [[1.0]], 1, "bad-time")
