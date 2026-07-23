from __future__ import annotations

import sqlite3
import re
from pathlib import Path

import pytest

import copilot_sdk.migrate.__main__ as migrate_main
from copilot_sdk.migrate.__main__ import main
from copilot_sdk.migrate.sqlite_to_age import (
    _compare_json,
    _default_source_path,
    _read_outcomes,
    _read_migration_records,
    _read_verified_decisions,
    _transform_decision,
    _verify_level1,
    _verify_level2,
    _verify_topology,
    _write_batch,
    run_migration,
)


DECISIONS_SCHEMA = """
CREATE TABLE decisions (
    decision_id TEXT PRIMARY KEY,
    domain TEXT,
    category TEXT,
    category_index INTEGER,
    factors_json TEXT,
    factor_vector_json TEXT,
    recommended_action TEXT,
    recommended_index INTEGER,
    confidence REAL,
    probabilities_json TEXT,
    status TEXT DEFAULT 'pending',
    created_at REAL
)
"""

OUTCOMES_SCHEMA = """
CREATE TABLE outcomes (
    decision_id TEXT PRIMARY KEY,
    domain TEXT DEFAULT '',
    actual_action TEXT,
    actual_index INTEGER,
    is_correct INTEGER,
    verified_at REAL,
    context_json TEXT
)
"""

CHECKPOINTS_SCHEMA = """
CREATE TABLE centroid_checkpoints (
    checkpoint_id TEXT, domain TEXT, decision_id TEXT, category TEXT,
    centroids_json TEXT, verified_count INTEGER, created_at REAL
)
"""

RECEIPTS_SCHEMA = """
CREATE TABLE evidence_receipts (
    receipt_intent_id TEXT, domain TEXT, decision_id TEXT, chain_index INTEGER,
    canonical_payload_json TEXT, created_at REAL
)
"""

ENTITY_EDGES_SCHEMA = """
CREATE TABLE decision_entity_edges (
    domain TEXT, decision_id TEXT, entity_id TEXT, entity_type TEXT
)
"""


def _make_db(tmp_path: Path, *, with_outcomes: bool = True) -> Path:
    db_path = tmp_path / "source.db"
    conn = sqlite3.connect(db_path)
    conn.execute(DECISIONS_SCHEMA)
    if with_outcomes:
        conn.execute(OUTCOMES_SCHEMA)
    rows = [
        ("d3", "trading", "cat_c", 2, '{"z": 3}', "[3.0]", "hold", 1, 0.3, '{"hold": 1}', "pending", 3.0),
        ("d1", "trading", "cat_a", 0, '{"a": 1}', "[1.0]", "buy", 0, 0.9, '{"buy": 1}', "confirmed", 1.0),
        ("d2", "trading", "cat_b", 1, '{"b": 2}', "[2.0]", "sell", 1, 0.8, '{"sell": 1}', "overridden", 2.0),
        ("d4", "trading", "cat_d", 3, '{"d": 4}', "[4.0]", "hold", 1, 0.7, '{"hold": 1}', "confirmed", 4.0),
        ("d5", "trading", "cat_e", 4, '{"e": 5}', "[5.0]", "buy", 0, 0.6, '{"buy": 1}', "overridden", 5.0),
        ("d6", "trading", "cat_f", 5, '{"f": 6}', "[6.0]", "buy", 0, 0.5, '{"buy": 1}', "pending", 6.0),
    ]
    conn.executemany(
        """
        INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    if with_outcomes:
        conn.executemany(
            "INSERT INTO outcomes VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                ("d1", "trading", "buy", 0, 1, 10.0, '{"note": "ok"}'),
                ("d2", "trading", "buy", 0, 0, 10.5, '{"note": "override"}'),
                ("d4", "trading", "hold", 1, 1, 11.0, "{}"),
                ("d5", "trading", "buy", 0, 0, 12.0, "{}"),
            ],
        )
    conn.commit()
    conn.close()
    return db_path


class FakeCursor:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row


class FakeConn:
    def __init__(self, *, existing=False, summary=None):
        self.existing = existing
        self.summary = summary
        self.queries: list[str] = []
        self.commit_count = 0
        self.rollback_count = 0
        self.closed = False

    def execute(self, query):
        self.queries.append(query)
        if "RETURN d" in query and "MATCH" in query:
            return FakeCursor(("node",) if self.existing else None)
        if "count(d)" in query:
            return FakeCursor(self.summary)
        return FakeCursor(None)

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1

    def close(self):
        self.closed = True


class TopologyConn(FakeConn):
    """Small in-memory AGE boundary double that records created topology."""

    def __init__(self):
        super().__init__()
        self.nodes: list[dict] = []
        self.edges: list[dict] = []

    @staticmethod
    def _literal(query: str, name: str) -> str | None:
        match = re.search(rf"{name}: '([^']*)'", query)
        return match.group(1) if match else None

    def execute(self, query):
        self.queries.append(query)
        if "MATCH (d:Decision" in query and "RETURN d" in query:
            return FakeCursor(None)
        labels = {
            "CREATE (d:Decision": "Decision",
            "CREATE (o:Outcome": "Outcome",
            "CREATE (c:CentroidCheckpoint": "CentroidCheckpoint",
            "CREATE (r:EvidenceReceipt": "EvidenceReceipt",
        }
        for marker, label in labels.items():
            if marker in query:
                self.nodes.append(
                    {
                        "label": label,
                        "decision_id": self._literal(query, "decision_id"),
                        "checkpoint_id": self._literal(query, "checkpoint_id"),
                        "receipt_intent_id": self._literal(query, "receipt_intent_id"),
                        "is_correct": "is_correct: false" not in query,
                        "has_rowid": "_migration_rowid:" in query,
                    }
                )
                return FakeCursor(None)
        for edge in ("HAS_OUTCOME", "HAS_CENTROID_CHECKPOINT", "EMITTED_RECEIPT"):
            if edge in query:
                self.edges.append(
                    {
                        "label": edge,
                        "checkpoint_id": self._literal(query, "checkpoint_id"),
                        "receipt_intent_id": self._literal(query, "receipt_intent_id"),
                    }
                )
                return FakeCursor(None)
        return FakeCursor(None)


def test_read_verified_only(tmp_path):
    db_path = _make_db(tmp_path)
    decisions = _read_verified_decisions(str(db_path))
    assert len(decisions) == 4
    assert {row["status"] for row in decisions} == {"confirmed", "overridden"}


def test_read_ordering(tmp_path):
    db_path = _make_db(tmp_path)
    decisions = _read_verified_decisions(str(db_path))
    assert [row["decision_id"] for row in decisions] == ["d1", "d2", "d4", "d5"]


def test_read_outcomes(tmp_path):
    db_path = _make_db(tmp_path)
    outcomes = _read_outcomes(str(db_path))
    assert outcomes["d1"]["actual_action"] == "buy"


def test_read_outcomes_missing_table(tmp_path):
    db_path = _make_db(tmp_path, with_outcomes=False)
    assert _read_outcomes(str(db_path)) == {}


def test_transform_all_columns():
    decision = {
        "decision_id": "d1",
        "domain": "trading",
        "category": "cat",
        "category_index": 1,
        "factors_json": '{"x": 1}',
        "factor_vector_json": "[1.0]",
        "recommended_action": "buy",
        "recommended_index": 2,
        "confidence": 0.75,
        "probabilities_json": '{"buy": 0.75}',
        "status": "confirmed",
        "created_at": 1.25,
    }
    outcome = {
        "actual_action": "sell",
        "actual_index": 3,
        "is_correct": 0,
        "verified_at": 2.25,
        "context_json": '{"why": "override"}',
    }
    transformed = _transform_decision(decision, outcome, "fallback")
    assert transformed == {
        **decision,
        "actual_action": "sell",
        "actual_index": 3,
        "is_correct": 0,
        "verified_at": 2.25,
        "context_json": '{"why": "override"}',
    }


def test_transform_no_outcome():
    transformed = _transform_decision({"decision_id": "d1", "domain": "trading"}, None, "trading")
    assert "actual_action" not in transformed
    assert transformed["decision_id"] == "d1"


def test_transform_none_fields():
    transformed = _transform_decision({"decision_id": None, "domain": None}, None, "trading")
    assert transformed["decision_id"] == ""
    assert transformed["domain"] == "trading"
    assert transformed["factors_json"] == "{}"
    assert transformed["factor_vector_json"] == "[]"


def test_dry_run_no_writes(tmp_path, monkeypatch):
    db_path = _make_db(tmp_path)

    def fail_connect(*args, **kwargs):
        raise AssertionError("dry run should not connect")

    monkeypatch.setattr("copilot_sdk.migrate.sqlite_to_age._connect_age", fail_connect)
    result = run_migration("trading", str(db_path), "dsn", "graph", dry_run=True)
    assert result["dry_run"] is True
    assert result["verified_count"] == 4


def test_idempotency():
    conn = FakeConn(existing=True)
    result = _write_batch(conn, [{"decision_id": "d1", "domain": "trading"}], "graph")
    assert result == {"written": 0, "skipped": 1, "errors": 0}
    assert not any("CREATE (d:Decision" in query for query in conn.queries)


def test_batch_commit():
    conn = FakeConn(existing=False)
    result = _write_batch(conn, [{"decision_id": "d1", "domain": "trading"}], "graph")
    assert result["written"] == 1
    assert conn.commit_count == 1


def test_write_errors_fail_migration(tmp_path, monkeypatch):
    db_path = _make_db(tmp_path)
    conn = FakeConn()
    monkeypatch.setattr("copilot_sdk.migrate.sqlite_to_age._connect_age", lambda *args: conn)
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._write_batch",
        lambda *args: {"written": 0, "skipped": 0, "errors": 1},
    )

    result = run_migration("trading", str(db_path), "dsn", "graph", verify=True)

    assert result["status"] == "FAIL"
    assert result["fail_reason"] == "1 write errors"
    assert conn.closed is True


def test_verify_level1_pass(tmp_path, monkeypatch):
    db_path = _make_db(tmp_path)
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._age_level1_summary",
        lambda conn, graph, domain: {"count": 4, "first_created_at": 1.0, "last_created_at": 5.0},
    )
    assert _verify_level1(str(db_path), FakeConn(), "graph", "trading")["passed"] is True


def test_verify_level1_fail_count(tmp_path, monkeypatch):
    db_path = _make_db(tmp_path)
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._age_level1_summary",
        lambda conn, graph, domain: {"count": 3, "first_created_at": 1.0, "last_created_at": 5.0},
    )
    assert _verify_level1(str(db_path), FakeConn(), "graph", "trading")["passed"] is False


def test_l1_failure_fails_migration_and_skips_l2(tmp_path, monkeypatch):
    db_path = _make_db(tmp_path)
    monkeypatch.setattr("copilot_sdk.migrate.sqlite_to_age._connect_age", lambda *args: FakeConn())
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._write_batch",
        lambda *args: {"written": 4, "skipped": 0, "errors": 0},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._verify_level1",
        lambda *args: {"passed": False, "details": {"reason": "count mismatch"}},
    )

    def fail_l2(*args):
        raise AssertionError("Level 2 should not run when Level 1 fails")

    monkeypatch.setattr("copilot_sdk.migrate.sqlite_to_age._verify_level2", fail_l2)

    result = run_migration("trading", str(db_path), "dsn", "graph", verify=True)

    assert result["status"] == "FAIL"
    assert result["fail_reason"].startswith("Level 1 verification failed:")
    assert "level2" not in result["verification"]


def test_verify_level2_pass(tmp_path, monkeypatch):
    db_path = _make_db(tmp_path)

    def age_decision(conn, graph, decision_id, domain):
        row = next(row for row in _read_verified_decisions(str(db_path), domain) if row["decision_id"] == decision_id)
        return {
            "category": row["category"],
            "recommended_action": row["recommended_action"],
            "confidence": row["confidence"],
            "factors_json": row["factors_json"],
        }

    monkeypatch.setattr("copilot_sdk.migrate.sqlite_to_age._age_decision_by_id", age_decision)
    assert _verify_level2(str(db_path), FakeConn(), "graph", "trading")["passed"] is True


def test_l2_handles_agtype_encoded_values(monkeypatch):
    decision = {
        "decision_id": "d1",
        "domain": "trading",
        "category": "trend_following",
        "category_index": 0,
        "factors_json": '{"signal_alignment": 0.69}',
        "factor_vector_json": "[0.69]",
        "recommended_action": "strong_execution",
        "recommended_index": 0,
        "confidence": 0.75,
        "probabilities_json": "[0.75, 0.25]",
        "status": "confirmed",
        "created_at": 1.0,
    }

    class EncodedConn:
        def execute(self, query):
            return FakeCursor(
                (
                    '"trend_following"',
                    '"strong_execution"',
                    0.75,
                    '"{\\"signal_alignment\\": 0.69}"',
                )
            )

    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._read_verified_decisions",
        lambda db_path, domain=None: [decision],
    )

    result = _verify_level2("source.db", EncodedConn(), "graph", "trading")

    assert result["passed"] is True


def test_verify_level2_fail_json(tmp_path, monkeypatch):
    db_path = _make_db(tmp_path)
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._age_decision_by_id",
        lambda conn, graph, decision_id, domain: {
            "category": "cat_a",
            "recommended_action": "buy",
            "confidence": 0.9,
            "factors_json": '{"different": true}',
        },
    )
    assert _verify_level2(str(db_path), FakeConn(), "graph", "trading")["passed"] is False


def test_l2_failure_fails_migration(tmp_path, monkeypatch):
    db_path = _make_db(tmp_path)
    monkeypatch.setattr("copilot_sdk.migrate.sqlite_to_age._connect_age", lambda *args: FakeConn())
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._write_batch",
        lambda *args: {"written": 4, "skipped": 0, "errors": 0},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._verify_level1",
        lambda *args: {"passed": True, "details": {"reason": "ok"}},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._verify_topology",
        lambda *args: {"passed": True, "expected": {}, "actual": {}, "mismatches": [], "sample_failures": []},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._verify_level2",
        lambda *args: {"passed": False, "details": {"mismatches": [{"decision_id": "d1"}]}},
    )

    result = run_migration("trading", str(db_path), "dsn", "graph", verify=True)

    assert result["status"] == "FAIL"
    assert result["fail_reason"].startswith("Level 2 verification failed:")
    assert result["verification"]["level1"]["passed"] is True
    assert result["verification"]["level2"]["passed"] is False


def test_scratch_migration_verifies_then_copies_to_live(tmp_path, monkeypatch):
    db_path = _make_db(tmp_path)
    conn = FakeConn()
    calls: list[tuple] = []
    monkeypatch.setattr("copilot_sdk.migrate.sqlite_to_age._connect_age", lambda *args: conn)
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age.create_scratch_graph",
        lambda dsn, domain: calls.append(("create_scratch", dsn, domain)) or "scratch_migration_trading_20260611_123045",
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age.verify_scratch_clean",
        lambda conn, graph: calls.append(("verify_clean", graph)) or True,
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._write_batch",
        lambda conn, batch, graph: calls.append(("write", graph, len(batch))) or {"written": len(batch), "skipped": 0, "errors": 0},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._verify_level1",
        lambda db, conn, graph, domain: calls.append(("l1", graph)) or {"passed": True, "details": {}},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._verify_topology",
        lambda records, conn, graph, domain: calls.append(("topology", graph)) or {"passed": True, "expected": {}, "actual": {}, "mismatches": [], "sample_failures": []},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._verify_level2",
        lambda db, conn, graph, domain: calls.append(("l2", graph)) or {"passed": True, "details": {}},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age.copy_to_live",
        lambda conn, transformed, live, domain: calls.append(("copy", transformed, live, domain)) or {"copied": 4, "skipped": 0, "errors": 0},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age.drop_scratch_graph",
        lambda dsn, graph: calls.append(("drop", dsn, graph)),
    )

    result = run_migration("trading", str(db_path), "dsn", "live_graph", use_scratch=True)

    scratch = "scratch_migration_trading_20260611_123045"
    assert result["status"] == "PASS"
    assert result["scratch_graph"] == scratch
    assert result["live_copy"] == {"copied": 4, "skipped": 0, "errors": 0}
    assert ("write", scratch, 4) in calls
    assert ("l1", scratch) in calls
    assert ("l2", scratch) in calls
    copy_calls = [call for call in calls if call[0] == "copy"]
    assert len(copy_calls) == 1
    assert len(copy_calls[0][1]) == 4
    assert copy_calls[0][2:] == ("live_graph", "trading")
    assert ("drop", "dsn", scratch) in calls


def test_scratch_migration_drops_scratch_and_skips_copy_on_l1_failure(tmp_path, monkeypatch):
    db_path = _make_db(tmp_path)
    calls: list[tuple] = []
    monkeypatch.setattr("copilot_sdk.migrate.sqlite_to_age._connect_age", lambda *args: FakeConn())
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age.create_scratch_graph",
        lambda dsn, domain: "scratch_migration_trading_20260611_123045",
    )
    monkeypatch.setattr("copilot_sdk.migrate.sqlite_to_age.verify_scratch_clean", lambda *args: True)
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._write_batch",
        lambda *args: {"written": 4, "skipped": 0, "errors": 0},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._verify_level1",
        lambda *args: {"passed": False, "details": {"reason": "count mismatch"}},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age.copy_to_live",
        lambda *args: (_ for _ in ()).throw(AssertionError("copy should not run")),
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age.drop_scratch_graph",
        lambda dsn, graph: calls.append(("drop", dsn, graph)),
    )

    result = run_migration("trading", str(db_path), "dsn", "live_graph", use_scratch=True)

    assert result["status"] == "FAIL"
    assert result["fail_reason"].startswith("Level 1 verification failed:")
    assert calls == [("drop", "dsn", "scratch_migration_trading_20260611_123045")]


def test_scratch_migration_fails_when_scratch_not_clean(tmp_path, monkeypatch):
    db_path = _make_db(tmp_path)
    calls: list[tuple] = []
    monkeypatch.setattr("copilot_sdk.migrate.sqlite_to_age._connect_age", lambda *args: FakeConn())
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age.create_scratch_graph",
        lambda dsn, domain: "scratch_migration_trading_20260611_123045",
    )
    monkeypatch.setattr("copilot_sdk.migrate.sqlite_to_age.verify_scratch_clean", lambda *args: False)
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._write_batch",
        lambda *args: (_ for _ in ()).throw(AssertionError("write should not run")),
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age.drop_scratch_graph",
        lambda dsn, graph: calls.append(("drop", dsn, graph)),
    )

    result = run_migration("trading", str(db_path), "dsn", "live_graph", use_scratch=True)

    assert result["status"] == "FAIL"
    assert result["fail_reason"] == "scratch graph is not clean: scratch_migration_trading_20260611_123045"
    assert calls == [("drop", "dsn", "scratch_migration_trading_20260611_123045")]


def test_scratch_retained_on_copy_failure(tmp_path, monkeypatch):
    db_path = _make_db(tmp_path)
    calls: list[tuple] = []
    monkeypatch.setattr("copilot_sdk.migrate.sqlite_to_age._connect_age", lambda *args: FakeConn())
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age.create_scratch_graph",
        lambda dsn, domain: "scratch_migration_trading_20260611_123045",
    )
    monkeypatch.setattr("copilot_sdk.migrate.sqlite_to_age.verify_scratch_clean", lambda *args: True)
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._write_batch",
        lambda *args: {"written": 4, "skipped": 0, "errors": 0},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._verify_level1",
        lambda *args: {"passed": True, "details": {}},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._verify_topology",
        lambda *args: {"passed": True, "expected": {}, "actual": {}, "mismatches": [], "sample_failures": []},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._verify_level2",
        lambda *args: {"passed": True, "details": {}},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age.copy_to_live",
        lambda *args: (_ for _ in ()).throw(RuntimeError("copy failed")),
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age.drop_scratch_graph",
        lambda dsn, graph: calls.append(("drop", dsn, graph)),
    )

    result = run_migration("trading", str(db_path), "dsn", "live_graph", use_scratch=True)

    assert result["status"] == "FAIL"
    assert result["fail_reason"] == "live copy failed: RuntimeError: copy failed"
    assert result["scratch_retained"] == "scratch_migration_trading_20260611_123045"
    assert result["scratch_retained_reason"] == "live copy failed"
    assert calls == []


def test_scratch_retained_on_copy_write_errors(tmp_path, monkeypatch):
    db_path = _make_db(tmp_path)
    calls: list[tuple] = []
    monkeypatch.setattr("copilot_sdk.migrate.sqlite_to_age._connect_age", lambda *args: FakeConn())
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age.create_scratch_graph",
        lambda dsn, domain: "scratch_migration_trading_20260611_123045",
    )
    monkeypatch.setattr("copilot_sdk.migrate.sqlite_to_age.verify_scratch_clean", lambda *args: True)
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._write_batch",
        lambda *args: {"written": 4, "skipped": 0, "errors": 0},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._verify_level1",
        lambda *args: {"passed": True, "details": {}},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._verify_topology",
        lambda *args: {"passed": True, "expected": {}, "actual": {}, "mismatches": [], "sample_failures": []},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._verify_level2",
        lambda *args: {"passed": True, "details": {}},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age.copy_to_live",
        lambda *args: {"copied": 3, "skipped": 0, "errors": 1},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age.drop_scratch_graph",
        lambda dsn, graph: calls.append(("drop", dsn, graph)),
    )

    result = run_migration("trading", str(db_path), "dsn", "live_graph", use_scratch=True)

    assert result["status"] == "FAIL"
    assert result["fail_reason"] == "live copy failed: 1 write errors"
    assert result["scratch_retained"] == "scratch_migration_trading_20260611_123045"
    assert result["scratch_retained_reason"] == "live copy failed"
    assert calls == []


def test_scratch_dropped_on_copy_success(tmp_path, monkeypatch):
    db_path = _make_db(tmp_path)
    calls: list[tuple] = []
    monkeypatch.setattr("copilot_sdk.migrate.sqlite_to_age._connect_age", lambda *args: FakeConn())
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age.create_scratch_graph",
        lambda dsn, domain: "scratch_migration_trading_20260611_123045",
    )
    monkeypatch.setattr("copilot_sdk.migrate.sqlite_to_age.verify_scratch_clean", lambda *args: True)
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._write_batch",
        lambda *args: {"written": 4, "skipped": 0, "errors": 0},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._verify_level1",
        lambda *args: {"passed": True, "details": {}},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._verify_topology",
        lambda *args: {"passed": True, "expected": {}, "actual": {}, "mismatches": [], "sample_failures": []},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._verify_level2",
        lambda *args: {"passed": True, "details": {}},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age.copy_to_live",
        lambda *args: {"copied": 4, "skipped": 0, "errors": 0},
    )
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age.drop_scratch_graph",
        lambda dsn, graph: calls.append(("drop", dsn, graph)),
    )

    result = run_migration("trading", str(db_path), "dsn", "live_graph", use_scratch=True)

    assert result["status"] == "PASS"
    assert calls == [("drop", "dsn", "scratch_migration_trading_20260611_123045")]


def test_compare_json_float_tolerance():
    assert _compare_json('{"value": 0.1}', '{"value": 0.10000000001}')


def test_compare_json_key_order():
    assert _compare_json('{"a": 1, "b": 2}', '{"b": 2, "a": 1}')


def test_empty_source_rejected(tmp_path):
    db_path = tmp_path / "empty.db"
    conn = sqlite3.connect(db_path)
    conn.execute(DECISIONS_SCHEMA)
    conn.commit()
    conn.close()
    with pytest.raises(ValueError, match="no verified decisions"):
        run_migration("trading", str(db_path), "dsn", "graph", dry_run=True)


def test_cli_help():
    with pytest.raises(SystemExit) as exc_info:
        main(["sqlite_to_age", "--help"])
    assert exc_info.value.code == 0


def test_cli_exits_nonzero_on_failure(monkeypatch):
    monkeypatch.setattr(
        migrate_main,
        "run_migration",
        lambda **kwargs: {"status": "FAIL", "fail_reason": "Level 1 verification failed: {}"},
    )

    with pytest.raises(SystemExit) as exc_info:
        migrate_main.main(
            [
                "sqlite_to_age",
                "--domain",
                "trading",
                "--age-dsn",
                "host=localhost port=5433 dbname=soc_copilot sslmode=disable",
            ]
        )

    assert exc_info.value.code == 1


def test_cli_all_decisions_passes_flag(monkeypatch):
    received: dict = {}

    def success(**kwargs):
        received.update(kwargs)
        return {"status": "PASS"}

    monkeypatch.setattr(migrate_main, "run_migration", success)
    with pytest.raises(SystemExit) as exc_info:
        migrate_main.main(
            [
                "sqlite_to_age",
                "--domain", "trading",
                "--age-dsn", "host=localhost",
                "--all-decisions",
            ]
        )
    assert exc_info.value.code == 0
    assert received["all_decisions"] is True


def test_default_source_path():
    assert _default_source_path("trading") == Path.home() / ".ci-platform" / "trading" / "trading.db"


def _records_with_topology(tmp_path: Path) -> list[dict]:
    db_path = _make_db(tmp_path)
    conn = sqlite3.connect(db_path)
    conn.execute(CHECKPOINTS_SCHEMA)
    conn.execute(RECEIPTS_SCHEMA)
    conn.execute(ENTITY_EDGES_SCHEMA)
    conn.execute(
        "INSERT INTO centroid_checkpoints VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("cp-1", "trading", "d1", "cat_a", "{}", 1, 11.0),
    )
    conn.execute(
        "INSERT INTO evidence_receipts VALUES (?, ?, ?, ?, ?, ?)",
        ("receipt-1", "trading", "d1", 0, "{}", 12.0),
    )
    conn.execute(
        "INSERT INTO decision_entity_edges VALUES (?, ?, ?, ?)",
        ("trading", "d1", "missing-target", "vendor"),
    )
    conn.commit()
    conn.close()
    return _read_migration_records(str(db_path), "trading", all_decisions=True)


def test_verified_record_writes_governed_decision_outcome_and_edge(tmp_path):
    records = _records_with_topology(tmp_path)
    conn = FakeConn()
    result = _write_batch(conn, [next(record for record in records if record["decision"]["decision_id"] == "d1")], "graph")
    queries = "\n".join(conn.queries)
    assert result == {"written": 1, "skipped": 0, "errors": 0}
    assert "status: 'confirmed'" in queries
    assert "CREATE (o:Outcome" in queries
    assert "actual_action: 'buy'" in queries
    assert "HAS_OUTCOME" in queries
    assert "migration_source: 'sqlite'" in queries


def test_overridden_record_preserves_final_status_and_false_outcome(tmp_path):
    records = _records_with_topology(tmp_path)
    conn = FakeConn()
    _write_batch(conn, [next(record for record in records if record["decision"]["decision_id"] == "d2")], "graph")
    queries = "\n".join(conn.queries)
    assert "status: 'overridden'" in queries
    assert "CREATE (o:Outcome" in queries
    assert "is_correct: false" in queries


def test_pending_records_require_all_decisions_and_have_no_outcome(tmp_path):
    db_path = _make_db(tmp_path)
    assert all(record["decision"]["status"] != "pending" for record in _read_migration_records(str(db_path), "trading"))
    pending = next(record for record in _read_migration_records(str(db_path), "trading", all_decisions=True) if record["decision"]["decision_id"] == "d3")
    conn = FakeConn()
    _write_batch(conn, [pending], "graph")
    queries = "\n".join(conn.queries)
    assert "status: 'pending'" in queries
    assert "CREATE (o:Outcome" not in queries
    assert "HAS_OUTCOME" not in queries


def test_factor_vector_is_embedded_not_a_node(tmp_path):
    record = next(record for record in _records_with_topology(tmp_path) if record["decision"]["decision_id"] == "d1")
    conn = FakeConn()
    _write_batch(conn, [record], "graph")
    queries = "\n".join(conn.queries)
    assert "factor_vector: '[1.0]'" in queries
    assert ":FactorVector" not in queries


def test_topology_checkpoint_and_receipt_queries(tmp_path):
    record = next(record for record in _records_with_topology(tmp_path) if record["decision"]["decision_id"] == "d1")
    conn = FakeConn()
    _write_batch(conn, [record], "graph")
    queries = "\n".join(conn.queries)
    assert "CREATE (c:CentroidCheckpoint" in queries
    assert "HAS_CENTROID_CHECKPOINT" in queries
    assert "CREATE (r:EvidenceReceipt" in queries
    assert "EMITTED_RECEIPT" in queries


def test_schema_adaptive_missing_optional_outcome_column(tmp_path):
    db_path = _make_db(tmp_path)
    conn = sqlite3.connect(db_path)
    conn.execute("DROP TABLE outcomes")
    conn.execute("CREATE TABLE outcomes (decision_id TEXT, domain TEXT, actual_action TEXT)")
    conn.execute("INSERT INTO outcomes VALUES ('d1', 'trading', 'buy')")
    conn.commit()
    conn.close()
    record = next(record for record in _read_migration_records(str(db_path), "trading") if record["decision"]["decision_id"] == "d1")
    fake = FakeConn()
    _write_batch(fake, [record], "graph")
    outcome_query = next(query for query in fake.queries if "CREATE (o:Outcome" in query)
    assert "actual_action: 'buy'" in outcome_query
    assert "actual_index:" not in outcome_query


def test_compound_key_and_query_safety(tmp_path):
    record = next(
        record
        for record in _records_with_topology(tmp_path)
        if record["decision"]["decision_id"] == "d1"
    )
    conn = FakeConn()
    _write_batch(conn, [record], "graph")
    queries = "\n".join(conn.queries)
    assert "domain: 'trading', decision_id: 'd1'" in queries
    assert "$params" not in queries
    assert "MERGE" not in queries


def test_domain_isolation_and_deferred_entity_edges(tmp_path, caplog):
    records = _records_with_topology(tmp_path)
    assert all(record["decision"]["domain"] == "trading" for record in records)
    assert "Deferring 1 decision_entity_edges" in caplog.text
    assert all("entity" not in record for record in records)


def test_second_write_skips_existing_decision_without_topology_duplication(tmp_path):
    record = next(record for record in _records_with_topology(tmp_path) if record["decision"]["decision_id"] == "d1")
    conn = FakeConn(existing=True)
    result = _write_batch(conn, [record], "graph")
    assert result == {"written": 0, "skipped": 1, "errors": 0}
    assert not any("CREATE (o:Outcome" in query for query in conn.queries)


def test_verified_decision_missing_outcome_fails_without_creating_that_decision(tmp_path, monkeypatch):
    db_path = _make_db(tmp_path)
    conn = sqlite3.connect(db_path)
    conn.execute("DELETE FROM outcomes WHERE decision_id = 'd4'")
    conn.commit()
    conn.close()
    age = TopologyConn()
    monkeypatch.setattr("copilot_sdk.migrate.sqlite_to_age._connect_age", lambda *args: age)

    result = run_migration("trading", str(db_path), "dsn", "graph", verify=False)

    assert result["status"] == "FAIL"
    assert result["fail_reason"] == "1 write errors"
    assert "d4" not in {node["decision_id"] for node in age.nodes if node["label"] == "Decision"}


def test_multiple_checkpoints_create_one_edge_per_unique_checkpoint(tmp_path):
    db_path = _make_db(tmp_path)
    conn = sqlite3.connect(db_path)
    conn.execute(CHECKPOINTS_SCHEMA)
    conn.executemany(
        "INSERT INTO centroid_checkpoints VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            ("cp-1", "trading", "d1", "cat_a", "{}", 1, 11.0),
            ("cp-2", "trading", "d1", "cat_a", "{}", 2, 12.0),
        ],
    )
    conn.commit()
    conn.close()
    record = next(record for record in _read_migration_records(str(db_path), "trading") if record["decision"]["decision_id"] == "d1")
    age = TopologyConn()

    _write_batch(age, [record], "graph")

    checkpoints = [node for node in age.nodes if node["label"] == "CentroidCheckpoint"]
    edges = [edge for edge in age.edges if edge["label"] == "HAS_CENTROID_CHECKPOINT"]
    assert {node["checkpoint_id"] for node in checkpoints} == {"cp-1", "cp-2"}
    assert {edge["checkpoint_id"] for edge in edges} == {"cp-1", "cp-2"}
    assert len(edges) == 2


def test_multiple_receipts_create_one_edge_per_unique_receipt(tmp_path):
    db_path = _make_db(tmp_path)
    conn = sqlite3.connect(db_path)
    conn.execute(RECEIPTS_SCHEMA)
    conn.executemany(
        "INSERT INTO evidence_receipts VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("receipt-1", "trading", "d1", 0, "{}", 11.0),
            ("receipt-2", "trading", "d1", 1, "{}", 12.0),
        ],
    )
    conn.commit()
    conn.close()
    record = next(record for record in _read_migration_records(str(db_path), "trading") if record["decision"]["decision_id"] == "d1")
    age = TopologyConn()

    _write_batch(age, [record], "graph")

    receipts = [node for node in age.nodes if node["label"] == "EvidenceReceipt"]
    edges = [edge for edge in age.edges if edge["label"] == "EMITTED_RECEIPT"]
    assert {node["receipt_intent_id"] for node in receipts} == {"receipt-1", "receipt-2"}
    assert {edge["receipt_intent_id"] for edge in edges} == {"receipt-1", "receipt-2"}
    assert len(edges) == 2


def test_level2_is_scoped_to_domain_for_duplicate_ids(tmp_path):
    db_path = tmp_path / "compound.db"
    conn = sqlite3.connect(db_path)
    compound_schema = DECISIONS_SCHEMA.replace("decision_id TEXT PRIMARY KEY", "decision_id TEXT")
    compound_schema = compound_schema.replace("\n)", ",\n    PRIMARY KEY (domain, decision_id)\n)")
    conn.execute(compound_schema)
    conn.executemany(
        "INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("same", "trading", "trading_cat", 0, "{}", "[]", "buy", 0, 0.9, "{}", "confirmed", 1.0),
            ("same", "purchasing", "purchasing_cat", 0, "{}", "[]", "reject", 0, 0.9, "{}", "confirmed", 1.0),
        ],
    )
    conn.commit()
    conn.close()

    class DomainConn:
        def __init__(self):
            self.query = ""

        def execute(self, query):
            self.query = query
            return FakeCursor(("trading_cat", "buy", 0.9, "{}"))

    age = DomainConn()
    result = _verify_level2(str(db_path), age, "graph", "trading")
    assert result["passed"] is True
    assert "domain: 'trading', decision_id: 'same'" in age.query
    assert "purchasing" not in age.query


@pytest.mark.parametrize("value", [0, "0"])
def test_outcome_false_values_normalize_to_false(tmp_path, value):
    records = _records_with_topology(tmp_path)
    record = next(record for record in records if record["decision"]["decision_id"] == "d1")
    record["outcome"]["is_correct"] = value
    age = TopologyConn()
    _write_batch(age, [record], "graph")
    outcome = next(node for node in age.nodes if node["label"] == "Outcome")
    assert outcome["is_correct"] is False


def test_behavioral_topology_and_governed_property_shape(tmp_path):
    """Migration differs only by SQLite raw fields and migration provenance."""
    record = next(record for record in _records_with_topology(tmp_path) if record["decision"]["decision_id"] == "d1")
    age = TopologyConn()
    _write_batch(age, [record], "graph")
    assert [node["label"] for node in age.nodes].count("Decision") == 1
    assert [node["label"] for node in age.nodes].count("Outcome") == 1
    assert [edge["label"] for edge in age.edges].count("HAS_OUTCOME") == 1
    decision = next(node for node in age.nodes if node["label"] == "Decision")
    assert decision["has_rowid"] is False
    props = record["decision"]
    governed_fields = {
        "decision_id", "domain", "category", "category_index", "recommended_action",
        "recommended_index", "confidence", "probabilities", "factor_vector", "factor_names",
        "source", "scorer_version", "preset_version", "factor_schema_version", "metadata",
    }
    assert governed_fields <= set(props)
    assert props["source"] == "migration"  # Expected difference from live source="score".
    assert props["migration_source"] == "sqlite"  # Migration-only provenance.


class TopologyVerificationConn:
    """AGE count boundary for topology-verification behavior."""

    def __init__(self, counts: dict[str, int]) -> None:
        self.counts = counts

    def execute(self, query):
        if "count(DISTINCT o) AS outcomes" in query:
            return FakeCursor((1, 1))
        for label in ("HAS_OUTCOME", "CentroidCheckpoint", "EvidenceReceipt", "Outcome", "Decision"):
            if label in query:
                return FakeCursor((self.counts.get(label, 0),))
        raise AssertionError(f"unexpected topology query: {query}")


def test_topology_verification_passes_for_decision_outcome_edge_parity(tmp_path):
    records = _read_migration_records(str(_make_db(tmp_path)), "trading", all_decisions=True)
    result = _verify_topology(
        records,
        TopologyVerificationConn(
            {"Decision": 6, "Outcome": 4, "HAS_OUTCOME": 4, "CentroidCheckpoint": 0, "EvidenceReceipt": 0}
        ),
        "graph",
        "trading",
    )

    assert result["passed"] is True
    assert result["actual"] == result["expected"]


def test_topology_verification_rejects_decisions_without_outcomes(tmp_path):
    records = _read_migration_records(str(_make_db(tmp_path)), "trading", all_decisions=True)
    result = _verify_topology(
        records,
        TopologyVerificationConn(
            {"Decision": 6, "Outcome": 0, "HAS_OUTCOME": 0, "CentroidCheckpoint": 0, "EvidenceReceipt": 0}
        ),
        "graph",
        "trading",
    )

    assert result["passed"] is False
    assert {item["element"] for item in result["mismatches"]} == {"Outcome", "HAS_OUTCOME"}
    assert result["mismatches"][0]["expected"] == 4
    assert result["mismatches"][0]["actual"] == 0
