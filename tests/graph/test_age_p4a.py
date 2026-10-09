"""Live AGE regressions for fresh-label pruning and native decision chronology."""
from __future__ import annotations

import asyncio
import time
from collections.abc import Iterator
from typing import Any
from uuid import uuid4

import pytest

from ci_platform.graph.age_sdk_adapter import AGEGraphStoreAdapter


@pytest.fixture
def fresh_age(disposable_age: Any) -> Iterator[AGEGraphStoreAdapter]:
    # Unlike disposable_age's shared helper, deliberately do not precreate labels.
    graph = "protocol_v2_test_p4a_" + uuid4().hex[:12]
    conn = disposable_age.connect()
    conn.execute("SELECT create_graph(%s)", (graph,))
    store = AGEGraphStoreAdapter(dsn=disposable_age.dsn, graph_name=graph, domain="purchasing")
    try:
        yield store
    finally:
        store.close()
        conn.execute("SELECT drop_graph(%s, true)", (graph,))
        conn.close()


def test_prune_fresh_graph_without_evolution_label(fresh_age: AGEGraphStoreAdapter) -> None:
    assert fresh_age.prune_evolution_events("purchasing", keep_recent=0) == 0
    # A missing label is not a poisoned transaction or a permanently empty cache.
    fresh_age.write_evolution_event("event", "purchasing", "proof_record", "rule", "v")
    assert fresh_age.prune_evolution_events("purchasing", keep_recent=0) == 1
    assert fresh_age.get_evolution_events("purchasing") == []


def test_prune_without_edge_label_preserves_other_domains_and_nonproof(
    fresh_age: AGEGraphStoreAdapter,
) -> None:
    fresh_age.write_evolution_event("other", "trading", "proof_record", "rule", "v")
    fresh_age.write_evolution_event("evolution", "purchasing", "promoted", "rule", "v")
    for index in range(3):
        fresh_age.write_evolution_event(f"proof-{index}", "purchasing", "proof_record", "rule", "v")
    assert fresh_age.prune_evolution_events("purchasing", keep_recent=2) == 2
    assert {r["event_id"] for r in fresh_age.get_evolution_events("purchasing")} == {"evolution", "proof-2"}
    assert [r["event_id"] for r in fresh_age.get_evolution_events("trading")] == ["other"]
    assert fresh_age.prune_evolution_events("purchasing", keep_recent=2) == 0


@pytest.mark.parametrize("transactional", [False, True])
def test_basic_decision_native_chronology_survives_reconnect(
    fresh_age: AGEGraphStoreAdapter, transactional: bool,
) -> None:
    identifiers = []
    start = time.time()
    for index in range(3):
        payload = dict(domain="purchasing", category="produce", action="order",
                       confidence=0.8, factors={"demand": index / 10})
        if transactional:
            identifier = asyncio.run(fresh_age.run_transaction(lambda tx: tx.write_decision(**payload)))
        else:
            identifier = fresh_age.write_decision(**payload)
        identifiers.append(identifier)
        fresh_age.write_outcome(identifier, "order", True, domain="purchasing")
        time.sleep(0.01)
    finish = time.time()
    inner = fresh_age._store
    reopened = AGEGraphStoreAdapter(dsn=inner._client._dsn, graph_name=inner._client._graph, domain="purchasing")
    try:
        for rows in (reopened.get_all_decisions("purchasing"), reopened.get_verified_decisions("purchasing")):
            assert [row["decision_id"] for row in rows] == identifiers
            timestamps = [row["created_at"] for row in rows]
            assert all(isinstance(value, (int, float)) and start <= value <= finish for value in timestamps)
            assert timestamps[0] < timestamps[1] < timestamps[2]
    finally:
        reopened.close()


def test_basic_and_governed_writes_preserve_explicit_created_at(
    fresh_age: AGEGraphStoreAdapter,
) -> None:
    basic = fresh_age.write_decision("purchasing", "produce", "order", 0.8, {"demand": 0.4},
                                    metadata={"created_at": 30.0})
    governed = fresh_age.generate_decision_id("purchasing")
    fresh_age.write_governed_decision(governed, "purchasing", "produce", 0, "order", 0,
                                     0.8, [0.8], [0.4], ["demand"], metadata={"created_at": 10.0})
    for identifier in (basic, governed):
        fresh_age.write_outcome(identifier, "order", True, domain="purchasing")
    rows = fresh_age.get_verified_decisions("purchasing")
    assert [row["decision_id"] for row in rows] == [governed, basic]
    assert [row["created_at"] for row in rows] == [10.0, 30.0]
