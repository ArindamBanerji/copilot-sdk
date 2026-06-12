from __future__ import annotations

import ast
import json

from copilot_sdk.migrate.sqlite_to_age import _S, _compare_json
from copilot_sdk.migrate.scratch_graph import (
    copy_to_live,
    create_scratch_graph,
    drop_scratch_graph,
    verify_scratch_clean,
)


class FakeCursor:
    def __init__(self, row=None, rows=None):
        self.row = row
        self.rows = rows or []

    def fetchone(self):
        return self.row

    def fetchall(self):
        return self.rows


class FakeConn:
    def __init__(self):
        self.queries: list[str] = []
        self.commit_count = 0
        self.rollback_count = 0
        self.scratch_rows = []
        self.live_existing = False
        self.clean_count = 0

    def execute(self, query):
        self.queries.append(query)
        if "count(d) AS cnt" in query:
            return FakeCursor((self.clean_count,))
        if "ORDER BY d.created_at ASC" in query:
            return FakeCursor(rows=self.scratch_rows)
        if "MATCH (d:Decision" in query and "RETURN d" in query:
            return FakeCursor(("node",) if self.live_existing else None)
        return FakeCursor(None)

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1


def _can_roundtrip(payload: str, serialized: str) -> bool:
    restored = ast.literal_eval(serialized)
    return _compare_json(payload, restored)


def test_create_scratch_graph_uses_safe_timestamped_name(monkeypatch):
    conn = FakeConn()
    monkeypatch.setattr(
        "copilot_sdk.migrate.scratch_graph.datetime",
        type(
            "FixedDateTime",
            (),
            {
                "now": staticmethod(lambda tz=None: __import__("datetime").datetime(2026, 6, 11, 12, 30, 45)),
            },
        ),
    )

    graph_name = create_scratch_graph(conn, "Trading Ops!")

    assert graph_name.startswith("scratch_migration_trading_ops_20260611_123045")
    assert any(query.startswith("SELECT drop_graph('scratch_migration_trading_ops_20260611_123045") for query in conn.queries)
    assert any(query.startswith("SELECT create_graph('scratch_migration_trading_ops_20260611_123045") for query in conn.queries)


def test_drop_scratch_graph_ignores_missing_graph_errors():
    class FailingConn(FakeConn):
        def execute(self, query):
            self.queries.append(query)
            raise RuntimeError("graph does not exist")

    conn = FailingConn()

    drop_scratch_graph(conn, "scratch_migration_test_20260611_123045")

    assert conn.rollback_count == 1


def test_verify_scratch_clean_true_when_no_decisions():
    conn = FakeConn()
    conn.clean_count = 0

    assert verify_scratch_clean(conn, "scratch_migration_test_20260611_123045") is True


def test_verify_scratch_clean_false_when_decisions_exist():
    conn = FakeConn()
    conn.clean_count = 1

    assert verify_scratch_clean(conn, "scratch_migration_test_20260611_123045") is False


def test_copy_to_live_uses_match_then_create_for_missing_decision():
    conn = FakeConn()
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
        "soc_graph",
        "trading",
    )

    assert result == {"copied": 1, "skipped": 0, "errors": 0}
    assert any("MATCH (d:Decision {decision_id:" in query and "domain:" in query for query in conn.queries)
    assert any("CREATE (d:Decision" in query for query in conn.queries)
    assert not any("MERGE" in query for query in conn.queries)
    assert conn.commit_count == 1


def test_copy_to_live_same_domain_skipped():
    conn = FakeConn()
    conn.live_existing = True
    transformed = [{"decision_id": "d1", "domain": "trading", "category": "cat"}]

    result = copy_to_live(
        conn,
        transformed,
        "soc_graph",
        "trading",
    )

    assert result == {"copied": 0, "skipped": 1, "errors": 0}
    assert not any("CREATE (d:Decision" in query for query in conn.queries)


def test_copy_to_live_different_domain_not_skipped():
    class DomainAwareConn(FakeConn):
        def execute(self, query):
            self.queries.append(query)
            if "MATCH (d:Decision" in query and "RETURN d" in query:
                return FakeCursor(("node",) if "domain: 'trading'" in query else None)
            return FakeCursor(None)

    conn = DomainAwareConn()
    transformed = [{"decision_id": "d1", "domain": "purchasing", "category": "cat"}]

    result = copy_to_live(
        conn,
        transformed,
        "soc_graph",
        "purchasing",
    )

    assert result == {"copied": 1, "skipped": 0, "errors": 0}
    assert any("CREATE (d:Decision" in query for query in conn.queries)


def test_copy_to_live_uses_original_transforms(monkeypatch):
    conn = FakeConn()
    transformed = [{"decision_id": "d1", "domain": "trading", "factors_json": '{"x": "raw"}'}]
    calls = []

    def fake_write_batch(conn_arg, batch_arg, graph_arg):
        calls.append((conn_arg, batch_arg, graph_arg))
        return {"written": 1, "skipped": 0, "errors": 0}

    monkeypatch.setattr("copilot_sdk.migrate.sqlite_to_age._write_batch", fake_write_batch)

    result = copy_to_live(conn, transformed, "soc_graph", "trading")

    assert result == {"copied": 1, "skipped": 0, "errors": 0}
    assert calls == [(conn, transformed, "soc_graph")]
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
