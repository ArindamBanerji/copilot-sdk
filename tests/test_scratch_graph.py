from __future__ import annotations

import ast
import json
import pytest
from uuid import uuid4

from copilot_sdk.migrate.sqlite_to_age import _S, _compare_json
from copilot_sdk.migrate.scratch_graph import (
    copy_to_live,
    create_scratch_graph,
    drop_scratch_graph,
    verify_scratch_clean,
)


def _can_roundtrip(payload: str, serialized: str) -> bool:
    restored = ast.literal_eval(serialized)
    return _compare_json(payload, restored)


@pytest.mark.age
def test_create_scratch_graph_uses_safe_timestamped_name(disposable_age):
    domain = "Trading Ops " + uuid4().hex[:8]
    graph = create_scratch_graph(disposable_age.dsn, domain)
    try:
        assert graph.startswith("scratch_migration_trading_ops_")
        with disposable_age.connect() as conn:
            assert conn.execute("SELECT count(*) FROM ag_catalog.ag_graph WHERE name = %s", (graph,)).fetchone()[0] == 1
    finally:
        drop_scratch_graph(disposable_age.dsn, graph)
    with disposable_age.connect() as conn:
        assert conn.execute("SELECT count(*) FROM ag_catalog.ag_graph WHERE name = %s", (graph,)).fetchone()[0] == 0


@pytest.mark.age
def test_drop_scratch_graph_ignores_missing_graph_errors(disposable_age):
    graph = "scratch_migration_missing_" + uuid4().hex[:12]
    drop_scratch_graph(disposable_age.dsn, graph)
    with disposable_age.connect() as conn:
        assert conn.execute("SELECT count(*) FROM ag_catalog.ag_graph WHERE name = %s", (graph,)).fetchone()[0] == 0


@pytest.mark.age
def test_verify_scratch_clean_true_when_no_decisions(migration_probe):
    conn = migration_probe()
    assert verify_scratch_clean(conn, conn.graph) is True


@pytest.mark.age
def test_verify_scratch_clean_false_when_decisions_exist(migration_probe):
    conn = migration_probe()
    conn.seed_node("Decision", {"decision_id": "d1", "domain": "trading"})
    assert verify_scratch_clean(conn, conn.graph) is False


@pytest.mark.age
def test_copy_to_live_uses_match_then_create_for_missing_decision(migration_probe):
    conn = migration_probe()
    transformed = [
        {
            "decision_id": "d1",
            "domain": "trading",
            "category": "cat",
            "factors_json": '{"signal_alignment": 0.88}',
        }
    ]

    result = copy_to_live(
        conn,
        transformed,
        conn.graph,
        "trading",
    )

    assert result == {"copied": 1, "skipped": 0, "errors": 0}
    assert any("MATCH (d:Decision {decision_id:" in query and "domain:" in query for query in conn.queries)
    assert any("CREATE (d:Decision" in query for query in conn.queries)
    assert not any("MERGE" in query for query in conn.queries)
    assert conn.commit_count == 1
    assert conn.read("MATCH (d:Decision {domain: 'trading'}) RETURN d.decision_id AS decision_id") == [{"decision_id": "d1"}]


@pytest.mark.age
def test_copy_to_live_same_domain_skipped(migration_probe):
    conn = migration_probe()
    conn.seed_node("Decision", {"decision_id": "d1", "domain": "trading"})
    transformed = [{"decision_id": "d1", "domain": "trading", "category": "cat"}]

    result = copy_to_live(
        conn,
        transformed,
        conn.graph,
        "trading",
    )

    assert result == {"copied": 0, "skipped": 1, "errors": 0}
    assert not any("CREATE (d:Decision" in query for query in conn.queries)


@pytest.mark.age
def test_copy_to_live_different_domain_not_skipped(migration_probe):
    conn = migration_probe()
    conn.seed_node("Decision", {"decision_id": "d1", "domain": "trading"})
    transformed = [{"decision_id": "d1", "domain": "purchasing", "category": "cat"}]

    result = copy_to_live(
        conn,
        transformed,
        conn.graph,
        "purchasing",
    )

    assert result == {"copied": 1, "skipped": 0, "errors": 0}
    assert any("CREATE (d:Decision" in query for query in conn.queries)


@pytest.mark.age
def test_copy_to_live_uses_original_transforms(monkeypatch, migration_probe):
    conn = migration_probe()
    transformed = [{"decision_id": "d1", "domain": "trading", "factors_json": '{"x": "raw"}'}]
    calls = []

    def fake_write_batch(conn_arg, batch_arg, graph_arg):
        calls.append((conn_arg, batch_arg, graph_arg))
        return {"written": 1, "skipped": 0, "errors": 0}

    monkeypatch.setattr("copilot_sdk.migrate.sqlite_to_age._write_batch", fake_write_batch)

    result = copy_to_live(conn, transformed, conn.graph, "trading")

    assert result == {"copied": 1, "skipped": 0, "errors": 0}
    assert calls == [(conn, transformed, conn.graph)]
    assert conn.queries == []


def test_factors_json_roundtrip():
    payloads = [
        '{"signal_alignment": 0.88, "notes": "it\'s a test"}',
        '{"empty": {}, "nested": {"a": {"b": 1}}}',
        '{"unicode": "café ñ 日本語"}',
        "{}",
    ]
    for payload in payloads:
        assert _can_roundtrip(payload, _S(payload))


def test_factor_vector_json_roundtrip():
    payloads = [
        "[0.1, -0.0, 1e-7, 0.999999999]",
        "[0.0, 0.0, 0.0, 0.0, 0.0, 0.0]",
        json.dumps([0.5] * 144),
    ]
    for payload in payloads:
        assert _can_roundtrip(payload, _S(payload))


def test_probabilities_json_roundtrip():
    payloads = [
        "[0.7751, 0.074967, 0.074967, 0.074966]",
        "[1.0]",
        "[0.25, 0.25, 0.25, 0.25]",
    ]
    for payload in payloads:
        assert _can_roundtrip(payload, _S(payload))


def test_context_json_roundtrip():
    payloads = [
        '{"actual_source": "seed", "override": true}',
        '{"nested": {"level2": {"level3": [1, 2, 3]}}}',
        "{}",
        "null",
    ]
    for payload in payloads:
        assert _can_roundtrip(payload, _S(payload))
