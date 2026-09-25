from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import pytest
from tests.age_probe import MigrationProbe

import copilot_sdk.migrate.sqlite_to_age as migration


def _source_db(tmp_path: Path, total: int = 25) -> Path:
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
    verified = min(10, total)
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


def _run(monkeypatch, path: Path, conn: MigrationProbe, **kwargs):
    monkeypatch.setattr(migration, "_connect_age", lambda *args: conn.open())
    return migration.run_migration(
        "trading", str(path), conn.dsn, conn.graph, all_decisions=True, verify=False, **kwargs
    )


def _count(conn: MigrationProbe, label: str, *, edges: bool = False) -> int:
    values = conn.edges if edges else conn.nodes
    return sum(1 for value in values if value["label"] == label)


@pytest.mark.age
def test_normal_completion_three_batches_and_topology(tmp_path, monkeypatch, migration_probe):
    path = _source_db(tmp_path)
    conn = migration_probe()
    result = _run(monkeypatch, path, conn, batch_size=10)
    checkpoint = json.loads(Path(result["checkpoint_file"]).read_text())
    assert result["status"] == "PASS"
    assert result["batches"] == 3
    assert _count(conn, "Decision") == 25
    assert _count(conn, "Outcome") == _count(conn, "HAS_OUTCOME", edges=True) == 10
    assert _count(conn, "CentroidCheckpoint") == 10
    assert _count(conn, "EvidenceReceipt") == 4
    assert checkpoint["status"] == "complete"


@pytest.mark.age
def test_checkpoint_is_published_after_each_committed_batch(tmp_path, monkeypatch, migration_probe):
    path = _source_db(tmp_path)
    conn = migration_probe(fail_on_decision_create=11)
    result = _run(monkeypatch, path, conn, batch_size=10)
    checkpoint = json.loads(Path(result["checkpoint_file"]).read_text())
    assert result["status"] == "FAIL"
    assert conn.commits == 1
    assert checkpoint == {**checkpoint, "last_rowid": 10, "batch_number": 1, "status": "in_progress"}


@pytest.mark.age
def test_resume_after_failed_second_batch_is_duplicate_free(tmp_path, monkeypatch, migration_probe):
    path = _source_db(tmp_path)
    conn = migration_probe(fail_on_decision_create=11)
    first = _run(monkeypatch, path, conn, batch_size=5)
    checkpoint = json.loads(Path(first["checkpoint_file"]).read_text())
    assert checkpoint["last_rowid"] == 10 and checkpoint["batch_number"] == 2
    conn.fail_on_decision_create = None
    resumed = _run(monkeypatch, path, conn, batch_size=5, resume=True)
    final_checkpoint = json.loads(Path(resumed["checkpoint_file"]).read_text())
    assert resumed["status"] == "PASS"
    assert _count(conn, "Decision") == 25
    assert len({node["decision_id"] for node in conn.nodes if node["label"] == "Decision"}) == 25
    assert final_checkpoint["decisions_written"] == 25
    assert final_checkpoint["outcomes_written"] == 10


@pytest.mark.age
def test_interrupt_mid_batch_rolls_back_the_uncommitted_batch(tmp_path, monkeypatch, migration_probe):
    path = _source_db(tmp_path)
    conn = migration_probe(fail_on_decision_create=14)
    result = _run(monkeypatch, path, conn, batch_size=10)
    checkpoint = json.loads(Path(result["checkpoint_file"]).read_text())
    assert result["status"] == "FAIL"
    assert _count(conn, "Decision") == 10
    assert conn.rollbacks == 1
    assert checkpoint["last_rowid"] == 10
    assert checkpoint["status"] == "in_progress"


@pytest.mark.age
def test_already_complete_resume_performs_no_writes(tmp_path, monkeypatch, migration_probe):
    path = _source_db(tmp_path, total=7)
    conn = migration_probe()
    _run(monkeypatch, path, conn, batch_size=3)
    creates = conn.decision_creates
    resumed = _run(monkeypatch, path, conn, batch_size=3, resume=True)
    assert resumed["already_complete"] is True
    assert conn.decision_creates == creates


@pytest.mark.age
def test_resume_retries_committed_batch_without_duplicates(tmp_path, monkeypatch, migration_probe):
    path = _source_db(tmp_path, total=7)
    conn = migration_probe()
    first = _run(monkeypatch, path, conn, batch_size=3)
    checkpoint_path = Path(first["checkpoint_file"])
    checkpoint_path.write_text(
        json.dumps(
            {
                "domain": "trading",
                "source_db_path": str(path.resolve()),
                "graph_name": conn.graph,
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


@pytest.mark.age
def test_batch_size_edge_case_three_three_one(tmp_path, monkeypatch, migration_probe):
    path = _source_db(tmp_path, total=7)
    conn = migration_probe()
    result = _run(monkeypatch, path, conn, batch_size=3)
    checkpoint = json.loads(Path(result["checkpoint_file"]).read_text())
    assert result["batches"] == 3
    assert _count(conn, "Decision") == 7
    assert checkpoint["batch_number"] == 3


@pytest.mark.age
def test_failed_batch_rollback_preserves_preexisting_nonmigration_node(tmp_path, monkeypatch, migration_probe):
    path = _source_db(tmp_path, total=7)
    conn = migration_probe(fail_on_decision_create=4)
    conn.seed_node("Decision", {"decision_id": "preexisting", "domain": "trading"})
    result = _run(monkeypatch, path, conn, batch_size=3)
    assert result["status"] == "FAIL"
    assert _count(conn, "Decision") == 4  # Three committed migration nodes plus the pre-existing node.
    assert any(node["decision_id"] == "preexisting" and not node.get("migration_source") for node in conn.nodes)


def test_resume_with_scratch_graph_is_rejected(tmp_path):
    path = _source_db(tmp_path, total=1)
    result = migration.run_migration(
        "trading", str(path), "dsn", "graph", all_decisions=True,
        verify=False, resume=True, use_scratch=True,
    )
    assert result["status"] == "FAIL"
    assert result["fail_reason"] == "Cannot resume a scratch-graph migration. Use direct-write mode."


@pytest.mark.age
def test_resume_rejects_checkpoint_from_different_graph(tmp_path, monkeypatch, migration_probe):
    path = _source_db(tmp_path, total=2)
    conn = migration_probe()
    _run(monkeypatch, path, conn, batch_size=1)
    result = migration.run_migration(
        "trading", str(path), "dsn", "other_graph", all_decisions=True,
        verify=False, resume=True,
    )
    assert result["status"] == "FAIL"
    assert f"Checkpoint was created for graph '{conn.graph}' but current target is 'other_graph'" in result["fail_reason"]


@pytest.mark.age
def test_resume_rejects_checkpoint_from_different_domain(tmp_path, monkeypatch, migration_probe):
    path = _source_db(tmp_path, total=2)
    conn = migration_probe()
    _run(monkeypatch, path, conn, batch_size=1)

    result = migration.run_migration(
        "purchasing", str(path), conn.dsn, conn.graph, all_decisions=True,
        verify=False, resume=True,
        checkpoint_file=str(migration._checkpoint_path(path, "trading")),
    )

    assert result["status"] == "FAIL"
    assert result["fail_reason"] == (
        "Checkpoint domain 'trading' does not match current domain 'purchasing'. "
        "Delete checkpoint to start fresh."
    )


@pytest.mark.age
def test_corrupt_checkpoint_reports_recoverable_migration_failure(tmp_path, monkeypatch, migration_probe):
    path = _source_db(tmp_path, total=2)
    checkpoint_path = migration._checkpoint_path(path, "trading")
    checkpoint_path.write_text("not valid JSON", encoding="utf-8")
    result = _run(monkeypatch, path, migration_probe(), resume=True)
    assert result["status"] == "FAIL"
    assert result["fail_reason"] == (
        f"Checkpoint file corrupted: {checkpoint_path}. Delete it to start fresh, or restore from backup."
    )


@pytest.mark.age
def test_empty_source_completes_and_publishes_zero_checkpoint(tmp_path, monkeypatch, migration_probe):
    path = _source_db(tmp_path, total=0)
    result = _run(monkeypatch, path, migration_probe(), batch_size=10)
    checkpoint = json.loads(Path(result["checkpoint_file"]).read_text())
    assert result["status"] == "PASS"
    assert result["empty_source"] is True
    assert result["write"] == {"written": 0, "skipped": 0, "errors": 0}
    assert checkpoint["status"] == "complete"
    assert checkpoint["decisions_written"] == checkpoint["outcomes_written"] == 0


@pytest.mark.age
def test_batch_size_one_creates_one_batch_per_decision(tmp_path, monkeypatch, migration_probe):
    path = _source_db(tmp_path, total=3)
    conn = migration_probe()
    result = _run(monkeypatch, path, conn, batch_size=1)
    assert result["status"] == "PASS"
    assert result["batches"] == 3
    assert _count(conn, "Decision") == 3


@pytest.mark.age
def test_total_below_batch_size_completes_in_one_batch(tmp_path, monkeypatch, migration_probe):
    path = _source_db(tmp_path, total=2)
    conn = migration_probe()
    result = _run(monkeypatch, path, conn, batch_size=10)
    assert result["status"] == "PASS"
    assert result["batches"] == 1
    assert _count(conn, "Decision") == 2


@pytest.mark.age
def test_resume_without_checkpoint_starts_fresh(tmp_path, monkeypatch, migration_probe):
    path = _source_db(tmp_path, total=2)
    conn = migration_probe()
    result = _run(monkeypatch, path, conn, batch_size=1, resume=True)
    assert result["status"] == "PASS"
    assert "resumed_from" not in result
    assert _count(conn, "Decision") == 2


@pytest.mark.age
def test_domain_scoped_tagged_rollback_preserves_nonmigration_decision(migration_probe):
    conn = migration_probe()
    for index in range(3):
        conn.seed_node("Decision", {"decision_id": f"migrated-{index}", "domain": "trading", "migration_source": "sqlite"})
    conn.seed_node("Decision", {"decision_id": "live", "domain": "trading"})
    deleted = conn.read(
        """
        MATCH (d:Decision {domain: 'trading', migration_source: 'sqlite'})
        OPTIONAL MATCH (d)-[:HAS_OUTCOME]->(o:Outcome)
        OPTIONAL MATCH (d)-[:HAS_CENTROID_CHECKPOINT]->(c:CentroidCheckpoint)
        OPTIONAL MATCH (d)-[:EMITTED_RECEIPT]->(r:EvidenceReceipt)
        DETACH DELETE d, o, r, c
        RETURN count(*) AS deleted
        """
    )[0]["deleted"]
    assert deleted == 3
    assert [(row["decision_id"], row.get("migration_source")) for row in conn.nodes] == [("live", None)]
