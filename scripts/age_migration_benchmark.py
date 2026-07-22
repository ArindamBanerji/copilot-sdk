"""Measure direct SQLite-to-AGE migration throughput on a disposable graph.

Run with ``AGE_INTEGRATION=1`` and ``AGE_TEST_DSN`` set.  This script creates
and drops only a ``benchmark_<timestamp>_<uuid>`` graph; it never uses
``soc_graph``.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
import time
import uuid
from pathlib import Path

import psycopg

from ci_platform.graph.agtype import normalize_agtype_value
from copilot_sdk.migrate import sqlite_to_age as migration


def _create_source(path: Path) -> None:
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
    for index in range(5000):
        status = "confirmed" if index < 1000 else "pending"
        decisions.append(
            (f"benchmark-{index}", "benchmark", "category_a", 0, "{}", "[0.25, 0.75]",
             "approve", 0, 0.9, "[0.9, 0.1]", status, float(index + 1))
        )
    conn.executemany("INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", decisions)
    conn.executemany(
        "INSERT INTO outcomes VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(f"benchmark-{index}", "benchmark", "approve", 0, 1, float(index + 10), "{}") for index in range(1000)],
    )
    conn.executemany(
        "INSERT INTO centroid_checkpoints VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(f"cp-{index}", "benchmark", f"benchmark-{index % 10}", "category_a", "{}", index + 1, float(index)) for index in range(20)],
    )
    conn.executemany(
        "INSERT INTO evidence_receipts VALUES (?, ?, ?, ?, ?, ?)",
        [(f"receipt-{index}", "benchmark", f"benchmark-{index % 4}", index, "{}", float(index)) for index in range(8)],
    )
    conn.commit()
    conn.close()


def _admin_connection(dsn: str) -> psycopg.Connection:
    conn = psycopg.connect(dsn, autocommit=True)
    conn.execute("LOAD 'age'")
    conn.execute('SET search_path = ag_catalog, "$user", public')
    return conn


def _scalar(conn: psycopg.Connection, graph: str, cypher: str) -> int:
    row = conn.execute(f"SELECT * FROM cypher('{graph}', $$ {cypher} $$) AS (cnt agtype)").fetchone()
    return int(normalize_agtype_value(row[0]))


def _counts(conn: psycopg.Connection, graph: str) -> dict[str, int]:
    return {
        "Decision": _scalar(conn, graph, "MATCH (n:Decision) RETURN count(n)"),
        "Outcome": _scalar(conn, graph, "MATCH (n:Outcome) RETURN count(n)"),
        "HAS_OUTCOME": _scalar(conn, graph, "MATCH ()-[r:HAS_OUTCOME]->() RETURN count(r)"),
        "CentroidCheckpoint": _scalar(conn, graph, "MATCH (n:CentroidCheckpoint) RETURN count(n)"),
        "EvidenceReceipt": _scalar(conn, graph, "MATCH (n:EvidenceReceipt) RETURN count(n)"),
    }


def main() -> int:
    if os.environ.get("AGE_INTEGRATION") != "1" or not os.environ.get("AGE_TEST_DSN", "").strip():
        print("SKIPPED: set AGE_INTEGRATION=1 and AGE_TEST_DSN to run the AGE migration benchmark.")
        return 0

    dsn = os.environ["AGE_TEST_DSN"].strip()
    graph = f"benchmark_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    admin = _admin_connection(dsn)
    admin.execute(f"SELECT create_graph('{graph}')")
    batch_seconds: list[float] = []
    original_write_batch = migration._write_batch
    try:
        # Windows can retain a just-closed SQLite handle briefly after a large
        # replay.  The source is disposable; do not turn a successful AGE
        # benchmark into a failure solely because its temporary cleanup races
        # that handle release.
        with tempfile.TemporaryDirectory(prefix="age_migration_benchmark_", ignore_cleanup_errors=True) as temporary:
            source = Path(temporary) / "benchmark.db"
            _create_source(source)

            def timed_write_batch(*args, **kwargs):
                started = time.perf_counter()
                try:
                    return original_write_batch(*args, **kwargs)
                finally:
                    batch_seconds.append(time.perf_counter() - started)

            migration._write_batch = timed_write_batch
            started = time.perf_counter()
            result = migration.run_migration(
                "benchmark", str(source), dsn, graph, all_decisions=True,
                batch_size=1000, verify=False,
            )
            total_seconds = time.perf_counter() - started
            migration._write_batch = original_write_batch
            if result["status"] != "PASS":
                raise RuntimeError(result.get("fail_reason", "migration failed"))

            first_counts = _counts(admin, graph)
            expected = {
                "Decision": 5000, "Outcome": 1000, "HAS_OUTCOME": 1000,
                "CentroidCheckpoint": 20, "EvidenceReceipt": 8,
            }
            counts_verified = first_counts == expected
            second = migration.run_migration(
                "benchmark", str(source), dsn, graph, all_decisions=True,
                batch_size=1000, verify=False,
            )
            if second["status"] != "PASS" or second["write"]["written"] != 0:
                raise RuntimeError("idempotency verification failed")

            for index, elapsed in enumerate(batch_seconds, start=1):
                print(f"Batch {index} (1K): {elapsed:.3f}s")
            print(f"Total 5K: {total_seconds:.3f}s")
            print(f"Estimated 24K: {total_seconds * 24_000 / 5_000:.3f}s")
            print(f"Counts verified: {'YES' if counts_verified else 'NO'}")
            print(f"Counts: {first_counts}")
            return 0 if counts_verified else 1
    finally:
        migration._write_batch = original_write_batch
        admin.execute(f"SELECT drop_graph('{graph}', true)")
        admin.close()


if __name__ == "__main__":
    raise SystemExit(main())
