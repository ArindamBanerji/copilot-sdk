from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import pytest

import copilot_sdk.migrate.sqlite_to_age as migration


class Cursor:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row


class TransactionTopologyConn:
    """In-memory transaction boundary used to exercise direct migration Cypher."""

    def __init__(self, fail_on_decision_create: int | None = None):
        self.nodes: list[dict] = []
        self.edges: list[dict] = []
        self._staged_nodes: list[dict] = []
        self._staged_edges: list[dict] = []
        self.decision_creates = 0
        self.fail_on_decision_create = fail_on_decision_create
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    @staticmethod
    def _value(query: str, name: str) -> str | None:
        match = re.search(rf"{name}: '([^']*)'", query)
        return match.group(1) if match else None

    def execute(self, query):
        if "DETACH DELETE d, o, r, c" in query:
            domain = self._value(query, "domain")
            before = len(self.nodes)
            self.nodes = [
                node
                for node in self.nodes
                if not (
                    node.get("domain") == domain
                    and node.get("migration_source") is True
                )
            ]
            return Cursor((before - len(self.nodes),))

        if "MATCH (d:Decision" in query and "RETURN d" in query:
            decision_id = self._value(query, "decision_id")
            existing = any(node["label"] == "Decision" and node["decision_id"] == decision_id for node in self.nodes + self._staged_nodes)
            return Cursor(("node",) if existing else None)
        for marker, label in (
            ("CREATE (d:Decision", "Decision"),
            ("CREATE (o:Outcome", "Outcome"),
            ("CREATE (c:CentroidCheckpoint", "CentroidCheckpoint"),
            ("CREATE (r:EvidenceReceipt", "EvidenceReceipt"),
        ):
            if marker in query:
                if label == "Decision":
                    self.decision_creates += 1
                    if self.fail_on_decision_create == self.decision_creates:
                        raise RuntimeError("injected batch failure")
                self._staged_nodes.append(
                    {
                        "label": label,
                        "decision_id": self._value(query, "decision_id"),
                        "domain": self._value(query, "domain"),
                        "migration_source": "migration_source: 'sqlite'" in query,
                    }
                )
                return Cursor()
        for edge in ("HAS_OUTCOME", "HAS_CENTROID_CHECKPOINT", "EMITTED_RECEIPT"):
            if edge in query:
                self._staged_edges.append({"label": edge})
                return Cursor()
        return Cursor()

    def commit(self):
        self.nodes.extend(self._staged_nodes)
        self.edges.extend(self._staged_edges)
        self._staged_nodes.clear()
        self._staged_edges.clear()
        self.commits += 1

    def rollback(self):
        self._staged_nodes.clear()
        self._staged_edges.clear()
        self.rollbacks += 1

    def close(self):
        self.closed = True


def _source_db(tmp_path: Path, total: int = 2500) -> Path:
    path = tmp_path / "migration.db"
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE decisions (decision_id TEXT PRIMARY KEY, domain TEXT, category TEXT,
          category_index INTEGER, factors_json TEXT, factor_vector_json TEXT,
          recommended_action TEXT, recommended_index INTEGER, confidence REAL,
          probabilities_json TEXT, status TEXT, created_at REAL);
        CREATE TABLE outcomes (decision_id TEXT PRIMARY KEY, domain TEXT, actual_action TEXT,
          actual_index INTEGER, is_correct INTEGER, verified_at REAL, context_json TEXT);
        CREATE TABLE centroid_checkpoints (checkpoint_id TEXT, domain TEXT, decision_id TEXT,
          category TEXT, centroids_json TEXT, verified_count INTEGER, created_at REAL);
        CREATE TABLE evidence_receipts (receipt_intent_id TEXT, domain TEXT, decision_id TEXT,
          chain_index INTEGER, canonical_payload_json TEXT, created_at REAL);
        """
    )
    verified = min(500, total)
    rows = []
    for index in range(1, total + 1):
        status = "confirmed" if index <= verified else "pending"
        rows.append((f"d{index}", "trading", "cat", 0, "{}", "[1.0]", "buy", 0, 0.9, "[1.0]", status, float(index)))
    conn.executemany("INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    conn.executemany(
        "INSERT INTO outcomes VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(f"d{index}", "trading", "buy", 0, 1, float(index), "{}") for index in range(1, verified + 1)],
    )
    conn.executemany(
        "INSERT INTO centroid_checkpoints VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(f"cp{index}", "trading", f"d{index}", "cat", "{}", index, float(index)) for index in range(1, 11)],
    )
    conn.executemany(
        "INSERT INTO evidence_receipts VALUES (?, ?, ?, ?, ?, ?)",
        [(f"r{index}", "trading", f"d{index}", index, "{}", float(index)) for index in range(1, 5)],
    )
    conn.commit()
    conn.close()
    return path


def _run(monkeypatch, path: Path, conn: TransactionTopologyConn, **kwargs):
    monkeypatch.setattr(migration, "_connect_age", lambda *args: conn)
    return migration.run_migration(
        "trading", str(path), "dsn", "graph", all_decisions=True, verify=False, **kwargs
    )


def _count(conn: TransactionTopologyConn, label: str, *, edges: bool = False) -> int:
    values = conn.edges if edges else conn.nodes
    return sum(1 for value in values if value["label"] == label)


def test_normal_completion_three_batches_and_topology(tmp_path, monkeypatch):
    path = _source_db(tmp_path)
    conn = TransactionTopologyConn()
    result = _run(monkeypatch, path, conn, batch_size=1000)
    checkpoint = json.loads(Path(result["checkpoint_file"]).read_text())
    assert result["status"] == "PASS"
    assert result["batches"] == 3
    assert _count(conn, "Decision") == 2500
    assert _count(conn, "Outcome") == _count(conn, "HAS_OUTCOME", edges=True) == 500
    assert _count(conn, "CentroidCheckpoint") == 10
    assert _count(conn, "EvidenceReceipt") == 4
    assert checkpoint["status"] == "complete"


def test_checkpoint_is_published_after_each_committed_batch(tmp_path, monkeypatch):
    path = _source_db(tmp_path)
    conn = TransactionTopologyConn(fail_on_decision_create=1001)
    result = _run(monkeypatch, path, conn, batch_size=1000)
    checkpoint = json.loads(Path(result["checkpoint_file"]).read_text())
    assert result["status"] == "FAIL"
    assert conn.commits == 1
    assert checkpoint == {**checkpoint, "last_rowid": 1000, "batch_number": 1, "status": "in_progress"}


def test_resume_after_failed_second_batch_is_duplicate_free(tmp_path, monkeypatch):
    path = _source_db(tmp_path)
    conn = TransactionTopologyConn(fail_on_decision_create=1001)
    first = _run(monkeypatch, path, conn, batch_size=500)
    checkpoint = json.loads(Path(first["checkpoint_file"]).read_text())
    assert checkpoint["last_rowid"] == 1000 and checkpoint["batch_number"] == 2
    conn.fail_on_decision_create = None
    resumed = _run(monkeypatch, path, conn, batch_size=500, resume=True)
    final_checkpoint = json.loads(Path(resumed["checkpoint_file"]).read_text())
    assert resumed["status"] == "PASS"
    assert _count(conn, "Decision") == 2500
    assert len({node["decision_id"] for node in conn.nodes if node["label"] == "Decision"}) == 2500
    assert final_checkpoint["decisions_written"] == 2500
    assert final_checkpoint["outcomes_written"] == 500


def test_interrupt_mid_batch_rolls_back_the_uncommitted_batch(tmp_path, monkeypatch):
    path = _source_db(tmp_path)
    conn = TransactionTopologyConn(fail_on_decision_create=1004)
    result = _run(monkeypatch, path, conn, batch_size=1000)
    checkpoint = json.loads(Path(result["checkpoint_file"]).read_text())
    assert result["status"] == "FAIL"
    assert _count(conn, "Decision") == 1000
    assert conn.rollbacks == 1
    assert checkpoint["last_rowid"] == 1000
    assert checkpoint["status"] == "in_progress"


def test_already_complete_resume_performs_no_writes(tmp_path, monkeypatch):
    path = _source_db(tmp_path, total=7)
    conn = TransactionTopologyConn()
    _run(monkeypatch, path, conn, batch_size=3)
    creates = conn.decision_creates
    resumed = _run(monkeypatch, path, conn, batch_size=3, resume=True)
    assert resumed["already_complete"] is True
    assert conn.decision_creates == creates


def test_resume_retries_committed_batch_without_duplicates(tmp_path, monkeypatch):
    path = _source_db(tmp_path, total=7)
    conn = TransactionTopologyConn()
    first = _run(monkeypatch, path, conn, batch_size=3)
    checkpoint_path = Path(first["checkpoint_file"])
    checkpoint_path.write_text(
        json.dumps(
            {
                "domain": "trading",
                "source_db_path": str(path.resolve()),
                "graph_name": "graph",
                "all_decisions": True,
                "last_rowid": 3,
                "batch_number": 1,
                "decisions_written": 3, "outcomes_written": 3, "status": "in_progress",
            }
        )
    )
    creates = conn.decision_creates
    resumed = _run(monkeypatch, path, conn, batch_size=3, resume=True)
    assert resumed["status"] == "PASS"
    assert conn.decision_creates == creates
    assert _count(conn, "Decision") == 7


def test_batch_size_edge_case_three_three_one(tmp_path, monkeypatch):
    path = _source_db(tmp_path, total=7)
    conn = TransactionTopologyConn()
    result = _run(monkeypatch, path, conn, batch_size=3)
    checkpoint = json.loads(Path(result["checkpoint_file"]).read_text())
    assert result["batches"] == 3
    assert _count(conn, "Decision") == 7
    assert checkpoint["batch_number"] == 3


def test_failed_batch_rollback_preserves_preexisting_nonmigration_node(tmp_path, monkeypatch):
    path = _source_db(tmp_path, total=7)
    conn = TransactionTopologyConn(fail_on_decision_create=4)
    conn.nodes.append({"label": "Decision", "decision_id": "preexisting", "migration_source": False})
    result = _run(monkeypatch, path, conn, batch_size=3)
    assert result["status"] == "FAIL"
    assert _count(conn, "Decision") == 4  # Three committed migration nodes plus the pre-existing node.
    assert any(node["decision_id"] == "preexisting" and not node["migration_source"] for node in conn.nodes)


def test_resume_with_scratch_graph_is_rejected(tmp_path):
    path = _source_db(tmp_path, total=1)
    result = migration.run_migration(
        "trading", str(path), "dsn", "graph", all_decisions=True,
        verify=False, resume=True, use_scratch=True,
    )
    assert result["status"] == "FAIL"
    assert result["fail_reason"] == "Cannot resume a scratch-graph migration. Use direct-write mode."


def test_resume_rejects_checkpoint_from_different_graph(tmp_path, monkeypatch):
    path = _source_db(tmp_path, total=2)
    conn = TransactionTopologyConn()
    _run(monkeypatch, path, conn, batch_size=1)
    result = migration.run_migration(
        "trading", str(path), "dsn", "other_graph", all_decisions=True,
        verify=False, resume=True,
    )
    assert result["status"] == "FAIL"
    assert "Checkpoint was created for graph 'graph' but current target is 'other_graph'" in result["fail_reason"]


def test_corrupt_checkpoint_reports_recoverable_migration_failure(tmp_path, monkeypatch):
    path = _source_db(tmp_path, total=2)
    checkpoint_path = migration._checkpoint_path(path, "trading")
    checkpoint_path.write_text("not valid JSON", encoding="utf-8")
    result = _run(monkeypatch, path, TransactionTopologyConn(), resume=True)
    assert result["status"] == "FAIL"
    assert result["fail_reason"] == (
        f"Checkpoint file corrupted: {checkpoint_path}. Delete it to start fresh, or restore from backup."
    )


def test_empty_source_completes_and_publishes_zero_checkpoint(tmp_path, monkeypatch):
    path = _source_db(tmp_path, total=0)
    result = _run(monkeypatch, path, TransactionTopologyConn(), batch_size=1000)
    checkpoint = json.loads(Path(result["checkpoint_file"]).read_text())
    assert result["status"] == "PASS"
    assert result["empty_source"] is True
    assert result["write"] == {"written": 0, "skipped": 0, "errors": 0}
    assert checkpoint["status"] == "complete"
    assert checkpoint["decisions_written"] == checkpoint["outcomes_written"] == 0


def test_batch_size_one_creates_one_batch_per_decision(tmp_path, monkeypatch):
    path = _source_db(tmp_path, total=3)
    conn = TransactionTopologyConn()
    result = _run(monkeypatch, path, conn, batch_size=1)
    assert result["status"] == "PASS"
    assert result["batches"] == 3
    assert _count(conn, "Decision") == 3


def test_total_below_batch_size_completes_in_one_batch(tmp_path, monkeypatch):
    path = _source_db(tmp_path, total=2)
    conn = TransactionTopologyConn()
    result = _run(monkeypatch, path, conn, batch_size=1000)
    assert result["status"] == "PASS"
    assert result["batches"] == 1
    assert _count(conn, "Decision") == 2


def test_resume_without_checkpoint_starts_fresh(tmp_path, monkeypatch):
    path = _source_db(tmp_path, total=2)
    conn = TransactionTopologyConn()
    result = _run(monkeypatch, path, conn, batch_size=1, resume=True)
    assert result["status"] == "PASS"
    assert "resumed_from" not in result
    assert _count(conn, "Decision") == 2


def test_domain_scoped_tagged_rollback_preserves_nonmigration_decision():
    conn = TransactionTopologyConn()
    conn.nodes.extend(
        [
            {"label": "Decision", "decision_id": f"migrated-{index}", "domain": "trading", "migration_source": True}
            for index in range(3)
        ]
        + [{"label": "Decision", "decision_id": "live", "domain": "trading", "migration_source": False}]
    )
    deleted = conn.execute(
        """
        MATCH (d:Decision {domain: 'trading', migration_source: 'sqlite'})
        OPTIONAL MATCH (d)-[:HAS_OUTCOME]->(o:Outcome)
        OPTIONAL MATCH (d)-[:HAS_CENTROID_CHECKPOINT]->(c:CentroidCheckpoint)
        OPTIONAL MATCH (d)-[:EMITTED_RECEIPT]->(r:EvidenceReceipt)
        DETACH DELETE d, o, r, c
        RETURN count(*)
        """
    ).fetchone()[0]
    assert deleted == 3
    assert conn.nodes == [{"label": "Decision", "decision_id": "live", "domain": "trading", "migration_source": False}]
