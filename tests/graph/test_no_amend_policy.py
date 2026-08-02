from __future__ import annotations

from collections.abc import Iterator
import os
from pathlib import Path
import time
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
        graph_store = SQLiteGraphStore(tmp_path / "no-amend.sqlite", domain="test")
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


def _write_decision(store: GraphStore) -> str:
    return store.write_decision(
        "test",
        category="quality",
        action="approve",
        confidence=0.9,
        factors={"risk": 0.1},
    )


def _archive_decision(store: GraphStore, decision_id: str) -> int:
    age_store: Any = getattr(store, "_store", None)
    if age_store is not None:
        literal = age_store._S(decision_id)
        rows = age_store._run_query(
            f"MATCH (d:Decision {{decision_id: {literal}}}) "
            f"WHERE d.domain = {age_store._S('test')} AND d.status = 'confirmed' "
            "SET d.archived = true, "
            f"d.archived_at = {time.time()}, "
            "d.archive_reason = 'test_retriage', "
            "d.archive_status = 'archived', "
            "d.archived_from_status = d.status "
            "RETURN count(d) AS cnt"
        )
        return int(rows[0].get("cnt", 0)) if rows else 0

    decision = store.get_decision(decision_id, "test")
    assert decision is not None
    archive_decisions = getattr(store, "archive_decisions")
    return int(
        archive_decisions(
            "test",
            before=float(decision["created_at"]) + 0.001,
            status_filter="confirmed",
            confirm_verified=True,
        )
    )


def test_retriage_correction_preserves_counts(store: GraphStore) -> None:
    first_id = _write_decision(store)
    store.write_outcome(first_id, "approve", True, domain="test")
    assert store.count_verified("test") == 1
    assert store.count_correct("test") == 1

    second_id = _write_decision(store)
    store.write_outcome(second_id, "review", False, domain="test")

    assert _archive_decision(store, first_id) == 1
    assert store.count_verified("test") == 1
    assert store.count_correct("test") == 0
    assert first_id in {row["decision_id"] for row in store.get_archived_decisions("test")}


def test_write_outcome_rejected_on_non_pending(store: GraphStore) -> None:
    decision_id = _write_decision(store)
    store.write_outcome(decision_id, "approve", True, domain="test")

    with pytest.raises((ValueError, RuntimeError)):
        store.write_outcome(decision_id, "review", False, domain="test")

    decision = store.get_decision(decision_id, "test")
    assert decision is not None
    assert decision["status"] == "confirmed"
    assert decision["correct"] is True


def test_archived_decision_not_in_verified(store: GraphStore) -> None:
    decision_id = _write_decision(store)
    store.write_outcome(decision_id, "approve", True, domain="test")

    assert _archive_decision(store, decision_id) == 1
    assert store.count_verified("test") == 0
    assert store.count_correct("test") == 0
    assert decision_id in {row["decision_id"] for row in store.get_archived_decisions("test")}
