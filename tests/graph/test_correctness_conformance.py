from __future__ import annotations

import inspect
from pathlib import Path
from collections.abc import Iterator

import pytest

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.protocol import GraphStore
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore


@pytest.fixture(params=["memory", "sqlite"])
def store(request: pytest.FixtureRequest, tmp_path: Path) -> Iterator[GraphStore]:
    if request.param == "memory":
        graph_store: GraphStore = InMemoryGraphStore(domain="test")
    else:
        graph_store = SQLiteGraphStore(tmp_path / "correctness.sqlite", domain="test")
    try:
        yield graph_store
    finally:
        graph_store.close()


def _write_decision(store: GraphStore, index: int) -> str:
    return store.write_decision(
        "test",
        category="correctness",
        action=f"action-{index}",
        confidence=0.9,
        factors={"index": index},
    )


def test_write_outcome_sets_d_correct(store) -> None:
    decision_id = _write_decision(store, 1)

    store.write_outcome(decision_id, "action-1", True, domain="test")

    decision = store.get_decision(decision_id, domain="test")
    assert decision is not None
    assert decision["correct"] is True
    assert decision["status"] in ("confirmed", "overridden")


def test_write_outcome_false_sets_d_correct_false(store) -> None:
    decision_id = _write_decision(store, 2)

    store.write_outcome(decision_id, "action-2", False, domain="test")

    decision = store.get_decision(decision_id, domain="test")
    assert decision is not None
    assert decision["correct"] is False
    assert decision["status"] in ("confirmed", "overridden")


def test_count_correct_equals_property_count(store) -> None:
    decision_ids = [_write_decision(store, index) for index in range(5)]
    for index, decision_id in enumerate(decision_ids):
        store.write_outcome(
            decision_id,
            f"action-{index}",
            index < 3,
            domain="test",
        )

    assert store.count_correct("test") == 3
    assert store.count_correct("test") <= store.count_verified("test")


def test_count_correct_has_no_outcome_traversal(store) -> None:
    source = inspect.getsource(type(store).count_correct)
    assert "HAS_OUTCOME" not in source
    assert "outcomes" not in source.lower()
    assert "_outcomes" not in source
    assert "correct" in source.lower()


def test_age_count_correct_query_is_property_only() -> None:
    age_store_path = (
        Path(__file__).resolve().parents[3]
        / "ci-platform"
        / "ci_platform"
        / "graph"
        / "age_graph_store.py"
    )
    source = age_store_path.read_text(encoding="utf-8")
    method_source = source.split("    def count_correct(", 1)[1].split(
        "    def count_decisions(", 1
    )[0]
    assert "HAS_OUTCOME" not in method_source
    assert "o.is_correct" not in method_source
    assert "d.correct = true" in method_source
