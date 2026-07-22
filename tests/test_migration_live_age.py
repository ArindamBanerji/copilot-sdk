"""Live AGE integration coverage for the direct SQLite-to-AGE migration writer.

Every test owns and drops a graph named ``mig_test_<uuid>``.  The suite never
queries or mutates ``soc_graph``.
"""

from __future__ import annotations

import os
import json
import sqlite3
import uuid
from pathlib import Path

import psycopg
import pytest

from ci_platform.graph import AGEGraphStoreAdapter
from ci_platform.graph.agtype import normalize_agtype_value
from copilot_sdk.migrate import sqlite_to_age as migration


pytestmark = pytest.mark.skipif(
    not os.environ.get("AGE_INTEGRATION"),
    reason="AGE_INTEGRATION=1 required for live migration tests",
)


def _dsn_or_skip() -> str:
    dsn = os.environ.get("AGE_TEST_DSN", "").strip()
    if not dsn:
        pytest.skip("AGE_TEST_DSN is required for live migration tests")
    return dsn


def _admin_connection(dsn: str) -> psycopg.Connection:
    conn = psycopg.connect(dsn, autocommit=True)
    conn.execute("LOAD 'age'")
    conn.execute('SET search_path = ag_catalog, "$user", public')
    return conn


@pytest.fixture()
def age_graph():
    dsn = _dsn_or_skip()
    graph = f"mig_test_{uuid.uuid4().hex[:8]}"
    conn = _admin_connection(dsn)
    conn.execute(f"SELECT create_graph('{graph}')")
    try:
        yield dsn, graph, conn
    finally:
        conn.execute(f"SELECT drop_graph('{graph}', true)")
        conn.close()


def _cypher(conn: psycopg.Connection, graph: str, cypher: str, columns: str):
    return conn.execute(
        f"SELECT * FROM cypher('{graph}', $$ {cypher} $$) AS ({columns})"
    ).fetchall()


def _scalar(rows) -> int:
    return int(normalize_agtype_value(rows[0][0]))


def _properties(value) -> dict:
    normalized = normalize_agtype_value(value)
    return json.loads(normalized) if isinstance(normalized, str) else dict(normalized)


def _counts(conn: psycopg.Connection, graph: str) -> dict[str, int]:
    return {
        "Decision": _scalar(_cypher(conn, graph, "MATCH (n:Decision) RETURN count(n)", "cnt agtype")),
        "Outcome": _scalar(_cypher(conn, graph, "MATCH (n:Outcome) RETURN count(n)", "cnt agtype")),
        "HAS_OUTCOME": _scalar(_cypher(conn, graph, "MATCH ()-[r:HAS_OUTCOME]->() RETURN count(r)", "cnt agtype")),
        "CentroidCheckpoint": _scalar(_cypher(conn, graph, "MATCH (n:CentroidCheckpoint) RETURN count(n)", "cnt agtype")),
        "EvidenceReceipt": _scalar(_cypher(conn, graph, "MATCH (n:EvidenceReceipt) RETURN count(n)", "cnt agtype")),
        "HAS_CENTROID_CHECKPOINT": _scalar(_cypher(conn, graph, "MATCH ()-[r:HAS_CENTROID_CHECKPOINT]->() RETURN count(r)", "cnt agtype")),
        "EMITTED_RECEIPT": _scalar(_cypher(conn, graph, "MATCH ()-[r:EMITTED_RECEIPT]->() RETURN count(r)", "cnt agtype")),
    }


def _make_source(
    path: Path,
    domain: str,
    *,
    verified: int,
    pending: int,
    checkpoints: int = 0,
    receipts: int = 0,
) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE decisions (
            decision_id TEXT, domain TEXT, category TEXT, category_index INTEGER,
            factors_json TEXT, factor_vector_json TEXT, recommended_action TEXT,
            recommended_index INTEGER, confidence REAL, probabilities_json TEXT,
            status TEXT, created_at REAL
        );
        CREATE TABLE outcomes (
            decision_id TEXT, domain TEXT, actual_action TEXT, actual_index INTEGER,
            is_correct INTEGER, verified_at REAL, context_json TEXT
        );
        CREATE TABLE centroid_checkpoints (
            checkpoint_id TEXT, domain TEXT, decision_id TEXT, category TEXT,
            centroids_json TEXT, verified_count INTEGER, created_at REAL
        );
        CREATE TABLE evidence_receipts (
            receipt_intent_id TEXT, domain TEXT, decision_id TEXT, chain_index INTEGER,
            canonical_payload_json TEXT, created_at REAL
        );
        CREATE TABLE decision_entity_edges (
            domain TEXT, decision_id TEXT, entity_id TEXT, entity_type TEXT
        );
        """
    )
    decisions = []
    for index in range(verified + pending):
        status = "confirmed" if index < verified else "pending"
        decisions.append(
            (f"d{index}", domain, "category_a", 0, "{}", "[0.25, 0.75]", "approve", 0,
             0.9, "[0.9, 0.1]", status, float(index + 1))
        )
    conn.executemany("INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", decisions)
    conn.executemany(
        "INSERT INTO outcomes VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(f"d{index}", domain, "approve", 0, 1, float(index + 10), "{}") for index in range(verified)],
    )
    conn.executemany(
        "INSERT INTO centroid_checkpoints VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(f"cp{index}", domain, "d0", "category_a", "{}", index + 1, float(index + 20)) for index in range(checkpoints)],
    )
    conn.executemany(
        "INSERT INTO evidence_receipts VALUES (?, ?, ?, ?, ?, ?)",
        [(f"receipt{index}", domain, "d0", index, "{}", float(index + 30)) for index in range(receipts)],
    )
    conn.commit()
    conn.close()


def _migrate(dsn: str, graph: str, source: Path, domain: str, **kwargs):
    return migration.run_migration(
        domain, str(source), dsn, graph, all_decisions=True, verify=False, **kwargs
    )


def test_verified_decision_topology(age_graph, tmp_path):
    dsn, graph, conn = age_graph
    source = tmp_path / "verified.db"
    _make_source(source, "test_verified", verified=3, pending=0)

    result = _migrate(dsn, graph, source, "test_verified")

    assert result["status"] == "PASS"
    assert _counts(conn, graph) == {
        "Decision": 3, "Outcome": 3, "HAS_OUTCOME": 3,
        "CentroidCheckpoint": 0, "EvidenceReceipt": 0,
        "HAS_CENTROID_CHECKPOINT": 0, "EMITTED_RECEIPT": 0,
    }
    decisions = _cypher(conn, graph, "MATCH (d:Decision) RETURN properties(d)", "props agtype")
    assert all(_properties(row[0])["status"] == "confirmed" for row in decisions)
    assert all(_properties(row[0])["migration_source"] == "sqlite" for row in decisions)
    outcomes = _cypher(conn, graph, "MATCH (o:Outcome) RETURN properties(o)", "props agtype")
    assert all({"is_correct", "actual_action", "verified_at"} <= set(_properties(row[0])) for row in outcomes)


def test_pending_decisions_have_no_outcome_topology(age_graph, tmp_path):
    dsn, graph, conn = age_graph
    source = tmp_path / "pending.db"
    _make_source(source, "test_pending", verified=0, pending=2)

    assert _migrate(dsn, graph, source, "test_pending")["status"] == "PASS"
    assert _counts(conn, graph)["Decision"] == 2
    assert _counts(conn, graph)["Outcome"] == _counts(conn, graph)["HAS_OUTCOME"] == 0
    rows = _cypher(conn, graph, "MATCH (d:Decision) RETURN d.status", "status agtype")
    assert [normalize_agtype_value(row[0]) for row in rows] == ["pending", "pending"]


def test_mixed_batch_writes_two_batches(age_graph, tmp_path):
    dsn, graph, conn = age_graph
    source = tmp_path / "mixed.db"
    _make_source(source, "test_mixed", verified=5, pending=3)

    result = _migrate(dsn, graph, source, "test_mixed", batch_size=4)

    assert result["status"] == "PASS"
    assert result["batches"] == 2
    counts = _counts(conn, graph)
    assert (counts["Decision"], counts["Outcome"], counts["HAS_OUTCOME"]) == (8, 5, 5)


def test_second_migration_is_idempotent(age_graph, tmp_path):
    dsn, graph, conn = age_graph
    source = tmp_path / "idempotent.db"
    _make_source(source, "test_idempotent", verified=3, pending=0)

    assert _migrate(dsn, graph, source, "test_idempotent")["status"] == "PASS"
    second = _migrate(dsn, graph, source, "test_idempotent")

    assert second["status"] == "PASS"
    assert second["write"]["written"] == 0
    assert (_counts(conn, graph)["Decision"], _counts(conn, graph)["Outcome"]) == (3, 3)


def test_checkpoint_and_receipt_topology_has_no_cross_product(age_graph, tmp_path):
    dsn, graph, conn = age_graph
    source = tmp_path / "topology.db"
    _make_source(source, "test_topology", verified=1, pending=0, checkpoints=2, receipts=1)

    assert _migrate(dsn, graph, source, "test_topology")["status"] == "PASS"
    counts = _counts(conn, graph)
    assert (counts["Decision"], counts["Outcome"], counts["CentroidCheckpoint"], counts["EvidenceReceipt"]) == (1, 1, 2, 1)
    assert (counts["HAS_CENTROID_CHECKPOINT"], counts["EMITTED_RECEIPT"]) == (2, 1)
    checkpoint_ids = _cypher(conn, graph, "MATCH (n:CentroidCheckpoint) RETURN n.checkpoint_id", "id agtype")
    receipt_ids = _cypher(conn, graph, "MATCH (n:EvidenceReceipt) RETURN n.receipt_intent_id", "id agtype")
    assert {normalize_agtype_value(row[0]) for row in checkpoint_ids} == {"cp0", "cp1"}
    assert {normalize_agtype_value(row[0]) for row in receipt_ids} == {"receipt0"}


def test_resume_replays_only_after_last_committed_batch(age_graph, tmp_path, monkeypatch):
    dsn, graph, conn = age_graph
    source = tmp_path / "resume.db"
    _make_source(source, "test_resume", verified=5, pending=5)
    original = migration._write_batch
    calls = 0

    def fail_second_batch(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("intentional live resume fault")
        return original(*args, **kwargs)

    monkeypatch.setattr(migration, "_write_batch", fail_second_batch)
    first = _migrate(dsn, graph, source, "test_resume", batch_size=3)
    assert first["status"] == "FAIL"
    monkeypatch.setattr(migration, "_write_batch", original)

    resumed = _migrate(dsn, graph, source, "test_resume", batch_size=3, resume=True)
    checkpoint = Path(resumed["checkpoint_file"]).read_text(encoding="utf-8")
    assert resumed["status"] == "PASS"
    assert _counts(conn, graph)["Decision"] == 10
    assert '"status": "complete"' in checkpoint


def test_domain_isolation_uses_domain_scoped_verified_counts(age_graph, tmp_path):
    dsn, graph, _ = age_graph
    source = tmp_path / "domains.db"
    _make_source(source, "test_a", verified=3, pending=0)
    conn = sqlite3.connect(source)
    conn.execute("INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                 ("b0", "test_b", "category_b", 0, "{}", "[]", "reject", 0, 0.8, "[0.8,0.2]", "confirmed", 99.0))
    conn.execute("INSERT INTO outcomes VALUES (?, ?, ?, ?, ?, ?, ?)", ("b0", "test_b", "reject", 0, 1, 100.0, "{}"))
    conn.execute("INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                 ("b1", "test_b", "category_b", 0, "{}", "[]", "reject", 0, 0.8, "[0.8,0.2]", "confirmed", 101.0))
    conn.execute("INSERT INTO outcomes VALUES (?, ?, ?, ?, ?, ?, ?)", ("b1", "test_b", "reject", 0, 1, 102.0, "{}"))
    conn.commit()
    conn.close()

    assert _migrate(dsn, graph, source, "test_a")["status"] == "PASS"
    assert _migrate(dsn, graph, source, "test_b")["status"] == "PASS"
    store = AGEGraphStoreAdapter(dsn=dsn, graph_name=graph)
    try:
        assert store.count_verified("test_a") == 3
        assert store.count_verified("test_b") == 2
    finally:
        store.close()


def test_output_equivalence_for_core_decision_fields(age_graph, tmp_path):
    dsn, graph, conn = age_graph
    source = tmp_path / "equivalence.db"
    _make_source(source, "test_equivalence", verified=1, pending=0)
    assert _migrate(dsn, graph, source, "test_equivalence")["status"] == "PASS"

    store = AGEGraphStoreAdapter(dsn=dsn, graph_name=graph)
    try:
        store.write_governed_decision(
            "live_equivalent", "test_equivalence", "category_a", 0, "approve", 0, 0.9,
            [0.9, 0.1], [0.25, 0.75], ["factor_0", "factor_1"], metadata={"created_at": 1.0},
        )
        store.write_outcome("live_equivalent", "approve", True, {"actual_index": 0, "verified_at": 10.0})
    finally:
        store.close()
    rows = _cypher(conn, graph, "MATCH (d:Decision) RETURN properties(d)", "props agtype")
    by_id = {_properties(row[0])["decision_id"]: _properties(row[0]) for row in rows}
    migrated, live = by_id["d0"], by_id["live_equivalent"]
    for field in ("domain", "category", "status", "confidence"):
        assert migrated[field] == live[field]
    # Expected differences: migration_source/migration_ts are migration-only;
    # factor_names, source, and version fields are unavailable in SQLite.
    assert migrated["migration_source"] == "sqlite"
    assert "migration_source" not in live
