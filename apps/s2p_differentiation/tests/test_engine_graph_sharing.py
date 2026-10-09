from __future__ import annotations

import inspect

from apps.s2p_differentiation import engine
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.namespace import GraphStoreNamespace


def test_arms_share_one_store() -> None:
    shared = InMemoryGraphStore(domain="s2p")
    arm_a = engine._make_scorer(
        shared,
        graph_namespace="s2p:run:ci",
        enable_rl=True,
    )
    arm_b = engine._make_scorer(
        shared,
        graph_namespace="s2p:run:hand",
        enable_rl=False,
    )
    try:
        store_a = arm_a._graph_store
        store_b = arm_b._graph_store
        assert isinstance(store_a, GraphStoreNamespace)
        assert isinstance(store_b, GraphStoreNamespace)
        assert id(store_a._store) == id(store_b._store)
    finally:
        arm_a.close()
        arm_b.close()
        shared.close()


def test_arm_namespace_isolation() -> None:
    shared = InMemoryGraphStore(domain="s2p")
    arm_a = engine._make_scorer(
        shared,
        graph_namespace="s2p:run:ci",
        enable_rl=False,
    )
    arm_b = engine._make_scorer(
        shared,
        graph_namespace="s2p:run:hand",
        enable_rl=False,
    )
    try:
        store_a = arm_a._graph_store
        store_b = arm_b._graph_store
        assert isinstance(store_a, GraphStoreNamespace)
        assert isinstance(store_b, GraphStoreNamespace)
        decision_id = store_a.write_decision(
            "s2p", "cat1", "approve", 0.9, {"f1": 0.5}
        )
        store_a.write_outcome(
            decision_id,
            "approve",
            True,
            domain="s2p",
        )
        assert store_a.count_verified("s2p") == 1
        assert store_b.count_verified("s2p") == 0
    finally:
        arm_a.close()
        arm_b.close()
        shared.close()


def test_no_per_arm_store_construction() -> None:
    source = inspect.getsource(engine)
    assert source.count("InMemoryGraphStore(") == 1
