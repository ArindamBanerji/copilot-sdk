from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import copilot_sdk.migrate.__main__ as migrate_main
from copilot_sdk.migrate.__main__ import main
from copilot_sdk.migrate.sqlite_to_age import (
    _compare_json,
    _default_source_path,
    _read_outcomes,
    _read_verified_decisions,
    _transform_decision,
    _verify_level1,
    _verify_level2,
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
        conn.execute(
            "INSERT INTO outcomes VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("d1", "trading", "buy", 0, 1, 10.0, '{"note": "ok"}'),
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

    def age_decision(conn, graph, decision_id):
        row = next(row for row in _read_verified_decisions(str(db_path)) if row["decision_id"] == decision_id)
        return {
            "category": row["category"],
            "recommended_action": row["recommended_action"],
            "confidence": row["confidence"],
            "factors_json": row["factors_json"],
        }

    monkeypatch.setattr("copilot_sdk.migrate.sqlite_to_age._age_decision_by_id", age_decision)
    assert _verify_level2(str(db_path), FakeConn(), "graph", "trading")["passed"] is True


def test_verify_level2_fail_json(tmp_path, monkeypatch):
    db_path = _make_db(tmp_path)
    monkeypatch.setattr(
        "copilot_sdk.migrate.sqlite_to_age._age_decision_by_id",
        lambda conn, graph, decision_id: {
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
        "copilot_sdk.migrate.sqlite_to_age._verify_level2",
        lambda *args: {"passed": False, "details": {"mismatches": [{"decision_id": "d1"}]}},
    )

    result = run_migration("trading", str(db_path), "dsn", "graph", verify=True)

    assert result["status"] == "FAIL"
    assert result["fail_reason"].startswith("Level 2 verification failed:")
    assert result["verification"]["level1"]["passed"] is True
    assert result["verification"]["level2"]["passed"] is False


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
                "host=localhost port=5433 dbname=soc_copilot",
            ]
        )

    assert exc_info.value.code == 1


def test_default_source_path():
    assert _default_source_path("trading") == Path.home() / ".ci-platform" / "trading" / "trading.db"
