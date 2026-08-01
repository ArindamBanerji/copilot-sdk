from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.protocol import GraphStore
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore


@pytest.fixture(params=["memory", "sqlite"])
def store(request: pytest.FixtureRequest, tmp_path: Path) -> Iterator[GraphStore]:
    graph_store: GraphStore
    if request.param == "memory":
        graph_store = InMemoryGraphStore(domain="test")
    else:
        graph_store = SQLiteGraphStore(tmp_path / "extended.sqlite", domain="test")
    try:
        yield graph_store
    finally:
        graph_store.close()


def _write_decision(store: GraphStore) -> str:
    return store.write_decision(
        "test",
        category="quality",
        action="approve",
        confidence=0.9,
        factors={"risk": 0.1},
    )


def test_write_outcome_sets_quality_signal(store: GraphStore) -> None:
    decision_id = _write_decision(store)

    store.write_outcome(
        decision_id,
        "approve",
        True,
        domain="test",
        quality_signal=0.75,
    )

    decision = store.get_decision(decision_id, domain="test")
    assert decision is not None
    assert decision["quality_signal"] == 0.75


def test_write_outcome_sets_soc_metadata(store: GraphStore) -> None:
    decision_id = _write_decision(store)

    store.write_outcome(
        decision_id,
        "review",
        False,
        domain="test",
        outcome="incorrect",
        verified_at_epoch=1_700_000_000_000,
        override_comment="analyst override",
        verified_by="analyst-1",
        analyst_action="review",
        final_action="review",
        recommended_action="approve",
        was_override=True,
    )

    decision = store.get_decision(decision_id, domain="test")
    assert decision is not None
    assert decision["outcome"] == "incorrect"
    assert decision["verified_at_epoch"] == 1_700_000_000_000
    assert decision["override_comment"] == "analyst override"
    assert decision["verified_by"] == "analyst-1"
    assert decision["analyst_action"] == "review"
    assert decision["final_action"] == "review"
    assert decision["recommended_action"] == "approve"
    assert decision["was_override"] is True


def test_write_outcome_without_soc_metadata_still_sets_core_projection(
    store: GraphStore,
) -> None:
    decision_id = _write_decision(store)

    store.write_outcome(decision_id, "approve", True, domain="test")

    decision = store.get_decision(decision_id, domain="test")
    assert decision is not None
    assert decision["correct"] is True
    assert decision["status"] == "confirmed"
    assert decision.get("quality_signal") is None
