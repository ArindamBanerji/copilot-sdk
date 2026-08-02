from __future__ import annotations

from collections.abc import Iterator
import os
from pathlib import Path
from typing import Any

import pytest

from copilot_sdk.config import GraphConfig
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.protocol import GraphStore
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
from copilot_sdk.testing import age_available


@pytest.fixture(params=["memory", "sqlite", "age"])
def store(request: pytest.FixtureRequest, tmp_path: Path) -> Iterator[GraphStore]:
    graph_store: GraphStore
    if request.param == "memory":
        graph_store = InMemoryGraphStore(domain="test")
    elif request.param == "sqlite":
        graph_store = SQLiteGraphStore(tmp_path / "verified-count.sqlite", domain="test")
    else:
        if not age_available():
            pytest.skip("AGE not available")
        age_graph = request.getfixturevalue("age_test_graph")
        dsn = os.getenv("AGE_TEST_DSN", "").strip() or (GraphConfig.load("trading").dsn or "").strip()
        if not dsn:
            pytest.skip("AGE test DSN is required")
        from ci_platform.graph import AGEGraphStoreAdapter

        graph_store = AGEGraphStoreAdapter(dsn=dsn, graph_name=age_graph)
    try:
        yield graph_store
    finally:
        if request.param == "age":
            age_store: Any = getattr(graph_store, "_store", None)
            if age_store is not None:
                age_store._run_query("MATCH (n) DETACH DELETE n")
        graph_store.close()


def _write_decision(store: GraphStore, index: int = 0) -> str:
    return store.write_decision(
        "test",
        category="quality",
        action="approve",
        confidence=0.9,
        factors={"risk": float(index)},
    )


def _clear_status(store: GraphStore, decision_id: str) -> None:
    if isinstance(store, InMemoryGraphStore):
        store._decisions[decision_id]["status"] = None
        return
    if isinstance(store, SQLiteGraphStore):
        store.connection.execute(
            # SQLite keeps status non-null; an unrecognized legacy value
            # represents the same non-verified state for this invariant.
            "UPDATE decisions SET status = ? WHERE decision_id = ?",
            ("legacy", decision_id),
        )
        store.connection.commit()
        return
    age_store = getattr(store, "_store", None)
    if age_store is not None:
        literal = age_store._S(decision_id)
        age_store._run_query(
            f"MATCH (d:Decision {{decision_id: {literal}}}) "
            "SET d.status = 'legacy' RETURN d"
        )
        return
    raise AssertionError(f"unsupported test store: {type(store)!r}")


def _set_correct(store: GraphStore, decision_id: str, value: bool) -> None:
    if isinstance(store, InMemoryGraphStore):
        store._decisions[decision_id]["correct"] = value
        return
    if isinstance(store, SQLiteGraphStore):
        store.connection.execute(
            "UPDATE decisions SET correct = ? WHERE decision_id = ?",
            (int(value), decision_id),
        )
        store.connection.commit()
        return
    age_store: Any = getattr(store, "_store", None)
    if age_store is not None:
        literal = age_store._S(decision_id)
        age_store._run_query(
            f"MATCH (d:Decision {{decision_id: {literal}}}) "
            f"SET d.correct = {'true' if value else 'false'} RETURN d"
        )
        return
    raise AssertionError(f"unsupported test store: {type(store)!r}")


def test_decision_with_outcome_but_no_status_not_counted(store: GraphStore) -> None:
    decision_id = _write_decision(store)
    store.write_outcome(decision_id, "approve", True, domain="test")
    _clear_status(store, decision_id)

    assert store.count_verified_decisions("test") == 0
    assert store.count_verified("test") == 0


def test_confirmed_decision_counted(store: GraphStore) -> None:
    decision_id = _write_decision(store)
    store.write_outcome(decision_id, "approve", True, domain="test")

    assert store.count_verified_decisions("test") == 1


def test_overridden_decision_counted(store: GraphStore) -> None:
    decision_id = _write_decision(store)
    store.write_outcome(decision_id, "review", False, domain="test")

    assert store.count_verified_decisions("test") == 1


def test_pending_decision_not_counted(store: GraphStore) -> None:
    _write_decision(store)

    assert store.count_verified_decisions("test") == 0


def test_count_verified_matches_count_correct_upper_bound(store: GraphStore) -> None:
    decision_ids = [_write_decision(store, index) for index in range(5)]
    store.write_outcome(decision_ids[0], "approve", True, domain="test")
    store.write_outcome(decision_ids[1], "approve", True, domain="test")
    store.write_outcome(decision_ids[2], "review", False, domain="test")

    verified = store.count_verified_decisions("test")
    correct = store.count_correct("test")
    assert verified == 3
    assert correct == 2
    assert correct <= verified


def test_pending_with_correct_flag_not_counted_correct(store: GraphStore) -> None:
    decision_id = _write_decision(store)
    _set_correct(store, decision_id, True)

    correct = store.count_correct("test")
    verified = store.count_verified("test")
    assert correct == 0
    assert verified == 0
    assert correct <= verified


def test_confirmed_correct_counted(store: GraphStore) -> None:
    decision_id = _write_decision(store)
    store.write_outcome(decision_id, "approve", True, domain="test")

    assert store.count_correct("test") == 1
    assert store.count_verified("test") == 1


def test_overridden_incorrect_not_counted_correct(store: GraphStore) -> None:
    decision_id = _write_decision(store)
    store.write_outcome(decision_id, "review", False, domain="test")

    assert store.count_correct("test") == 0
    assert store.count_verified("test") == 1
