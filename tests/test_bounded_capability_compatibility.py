"""The bounded capability must not expand existing store requirements."""

from __future__ import annotations

import inspect
import itertools
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from copilot_sdk import graph
from copilot_sdk.graph import InMemoryGraphStore, protocol, query
from copilot_sdk.graph.protocol import (
    BoundedProjectionStore, GraphStore, GraphTraversalStore, L5LearningStore,
    ProtocolV2GraphStore, ScoringPersistenceStore,
)


@pytest.fixture
def store() -> Iterator[InMemoryGraphStore]:
    value = InMemoryGraphStore()
    try:
        yield value
    finally:
        value.close()


def test_graph_membership(store: InMemoryGraphStore) -> None:
    assert isinstance(store, GraphStore)


def test_v2_membership(store: InMemoryGraphStore) -> None:
    assert isinstance(store, ProtocolV2GraphStore)


def test_no_bounded_membership(store: InMemoryGraphStore) -> None:
    assert isinstance(store, BoundedProjectionStore)


@pytest.mark.parametrize("capability", [
    GraphTraversalStore, L5LearningStore, ScoringPersistenceStore, BoundedProjectionStore,
])
def test_runtime_checkable(capability: Any) -> None:
    assert isinstance(object(), capability) is False


def test_original_count_api(store: InMemoryGraphStore) -> None:
    assert list(inspect.signature(GraphStore.count_decisions).parameters) == ["self", "domain"]
    count = store.count_decisions("test_domain")
    assert type(count) is int and count == 0
    store.write_decision("test_domain", "cat1", "approve", 0.8, {})
    assert store.count_decisions("test_domain") == 1
    assert store.count_decisions("other_domain") == 0


def test_bounded_inherits_graph() -> None:
    assert GraphStore in BoundedProjectionStore.__mro__
    assert ProtocolV2GraphStore not in BoundedProjectionStore.__mro__


def test_bounded_requires_base_contract(store: InMemoryGraphStore) -> None:
    # Structural membership probe only: no production store or inherited stubs.
    def probe(*args: Any, **kwargs: Any) -> None:
        pass

    methods = {name: probe for name in (
        "query_decisions", "count_decisions", "aggregate_decisions", "get_decision_changes",
    )}
    bounded_only = type("BoundedOnly", (), methods)()
    assert not isinstance(bounded_only, GraphStore)
    assert not isinstance(bounded_only, BoundedProjectionStore)
    graph_methods = {
        name: getattr(store, name) for name in dir(GraphStore)
        if not name.startswith("_") and callable(getattr(GraphStore, name))
    }
    complete = type("StructuralProbe", (), {**graph_methods, **methods})()
    assert isinstance(complete, BoundedProjectionStore)
    assert isinstance(complete, GraphStore)


def test_public_exports() -> None:
    names = {"BoundedProjectionStore", *query.__all__}
    assert len(names) == 13
    for name in names:
        expected = BoundedProjectionStore if name == "BoundedProjectionStore" else getattr(query, name)
        assert getattr(graph, name) is expected
        assert getattr(protocol, name) is expected
        assert name in graph.__all__
    assert graph.__all__ == sorted(graph.__all__)
    assert len(graph.__all__) == len(set(graph.__all__))


@pytest.mark.parametrize("order", list(itertools.permutations([
    "copilot_sdk.graph.query", "copilot_sdk.graph.protocol", "copilot_sdk.graph",
])))
def test_import_order_in_fresh_process(order: tuple[str, ...]) -> None:
    script = "import importlib\n" + "\n".join(
        f"importlib.import_module({name!r})" for name in order
    )
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=Path(__file__).resolve().parents[1],
        capture_output=True, text=True, timeout=30, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_factory_memory_composition_preserves_bounded_capability() -> None:
    from copilot_sdk.graph.capabilities import require_bounded_projection_store
    from copilot_sdk.graph.factory import create_graph_store

    composed = create_graph_store(
        backend="memory", domain="bounded-compat", profile="test", env={},
    )
    bounded = require_bounded_projection_store(composed, feature="compatibility")
    decision_id = bounded.write_decision(
        "bounded-compat", "risk", "approve", 0.8, {"cost": 0.2}, {},
    )

    page = bounded.query_decisions("bounded-compat")
    assert [row["decision_id"] for row in page.items] == [decision_id]
    assert bounded.count_decisions("bounded-compat") == 1
    assert bounded.aggregate_decisions("bounded-compat")[0].values["count"] == 1.0
    changes = bounded.get_decision_changes(
        "bounded-compat", after_generation=0,
    )
    assert [event["decision_id"] for event in changes.events] == [decision_id]
