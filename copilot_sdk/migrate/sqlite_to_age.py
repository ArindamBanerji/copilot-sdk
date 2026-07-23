"""SQLite decision-log to AGE topology migration.

Verified decisions are the default migration set; ``--all-decisions`` also
copies pending work. Learned L5/DK/conservation state is intentionally not
migrated and is re-derived from the ordered decision log.
"""

from __future__ import annotations

import json
import logging
import math
import os
import random
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import psycopg

from ci_platform.graph.agtype import normalize_agtype_value
from copilot_sdk.migrate.scratch_graph import (
    copy_to_live,
    create_scratch_graph,
    drop_scratch_graph,
    verify_scratch_clean,
)
from ci_platform.graph.age_client import AGEClient

_S = AGEClient.serialize_for_age
logger = logging.getLogger(__name__)

DECISION_COLUMNS = (
    "decision_id",
    "domain",
    "category",
    "category_index",
    "factors_json",
    "factor_vector_json",
    "recommended_action",
    "recommended_index",
    "confidence",
    "probabilities_json",
    "status",
    "created_at",
)

OUTCOME_COLUMNS = (
    "decision_id",
    "domain",
    "actual_action",
    "actual_index",
    "is_correct",
    "verified_at",
    "context_json",
)

_SAFE_DOMAIN_RE = re.compile(r"^[a-zA-Z0-9_-]{1,200}$")
_VERIFIED_STATUSES = frozenset({"confirmed", "overridden"})


def _validated_domain(domain: str) -> str:
    """Return a domain that is safe to interpolate into AGE Cypher."""
    value = str(domain)
    if not _SAFE_DOMAIN_RE.fullmatch(value):
        raise ValueError(f"unsupported graph domain: {value}")
    return value


def _default_source_path(domain: str) -> Path:
    return Path(os.path.expanduser("~")) / ".ci-platform" / domain / f"{domain}.db"


def _connect_age(dsn: str, graph_name: str) -> psycopg.Connection:
    """Create an AGE connection for migration with bounded statements."""
    _ = graph_name
    if "sslmode" not in dsn:
        dsn += " sslmode=disable"
    conn: psycopg.Connection = psycopg.connect(dsn, autocommit=False, connect_timeout=10)
    conn.execute("LOAD 'age'")
    conn.execute("SET search_path = ag_catalog, '$user', public")
    conn.execute("SET statement_timeout = '120s'")
    return conn


def _read_verified_decisions(db_path: str, domain: str | None = None) -> list[dict[str, Any]]:
    """Read verified decisions in path-sensitive replay order."""
    query = f"""
        SELECT {", ".join(DECISION_COLUMNS)}
        FROM decisions
        WHERE status IN ('confirmed', 'overridden')
        {"AND domain = ?" if domain is not None else ""}
        ORDER BY created_at ASC
    """
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(query, (domain,) if domain is not None else ()).fetchall()]


def _read_outcomes(db_path: str) -> dict[str, dict[str, Any]]:
    """Read outcomes keyed by decision_id, returning empty when absent."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'outcomes'"
        ).fetchone()
        if table is None:
            return {}
        query = f"SELECT {', '.join(OUTCOME_COLUMNS)} FROM outcomes"
        return {str(row["decision_id"]): dict(row) for row in conn.execute(query).fetchall()}


def _table_columns(conn: sqlite3.Connection, table: str) -> tuple[str, ...]:
    """Read a fixed SQLite table's columns without assuming schema versions."""
    return tuple(str(row[1]) for row in conn.execute(f"PRAGMA table_info({table})").fetchall())


def _table_rows(
    conn: sqlite3.Connection,
    table: str,
    domain: str,
) -> list[dict[str, Any]]:
    columns = _table_columns(conn, table)
    if not columns:
        return []
    where = " WHERE domain = ?" if "domain" in columns else ""
    return [dict(row) for row in conn.execute(f"SELECT * FROM {table}{where}", (domain,) if where else ()).fetchall()]


def _group_by_decision(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        decision_id = row.get("decision_id")
        if decision_id is not None:
            grouped.setdefault(str(decision_id), []).append(row)
    return grouped


def _migration_decision_properties(
    decision: Mapping[str, Any], domain: str, migration_ts: float
) -> dict[str, Any]:
    """Produce governed Decision properties while retaining SQLite source fields."""
    properties = {key: value for key, value in decision.items() if key != "_migration_rowid"}
    properties.update(
        {
            "decision_id": _as_text(decision.get("decision_id")),
            "domain": domain,
            "category": _as_text(decision.get("category")),
            "category_index": _as_int(decision.get("category_index")),
            "recommended_action": _as_text(decision.get("recommended_action")),
            "recommended_index": _as_int(decision.get("recommended_index")),
            "confidence": _as_float(decision.get("confidence")),
            "probabilities": _as_text(decision.get("probabilities_json"), "{}"),
            "factor_vector": _as_text(decision.get("factor_vector_json"), "[]"),
            "factor_names": "[]",
            "source": "migration",
            "scorer_version": "",
            "preset_version": "",
            "factor_schema_version": "",
            "metadata": "{}",
            "status": _as_text(decision.get("status"), "pending"),
            "created_at": _as_float(decision.get("created_at")),
            "migration_source": "sqlite",
            "migration_ts": migration_ts,
        }
    )
    return properties


def _read_migration_records(
    db_path: str, domain: str, *, all_decisions: bool = False
) -> list[dict[str, Any]]:
    """Read schema-adaptive decision topology records in SQLite rowid order."""
    domain = _validated_domain(domain)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        decision_columns = _table_columns(conn, "decisions")
        if not decision_columns:
            raise ValueError(f"decisions table missing in {db_path}")
        decisions = [
            dict(row)
            for row in conn.execute(
                "SELECT rowid AS _migration_rowid, * FROM decisions WHERE domain = ? ORDER BY rowid ASC",
                (domain,),
            ).fetchall()
        ]
        outcomes = _group_by_decision(_table_rows(conn, "outcomes", domain))
        checkpoints = _group_by_decision(_table_rows(conn, "centroid_checkpoints", domain))
        receipts = _group_by_decision(_table_rows(conn, "evidence_receipts", domain))
        if _table_columns(conn, "decision_entity_edges"):
            edge_count = conn.execute(
                "SELECT COUNT(*) FROM decision_entity_edges WHERE domain = ?", (domain,)
            ).fetchone()[0]
            if edge_count:
                logger.warning("Deferring %s decision_entity_edges for domain %s (OD-1)", edge_count, domain)

    migration_ts = time.time()
    records: list[dict[str, Any]] = []
    for decision in decisions:
        decision_id = str(decision.get("decision_id") or "")
        status = decision.get("status")
        outcome_rows = outcomes.get(decision_id, [])
        verified = status in _VERIFIED_STATUSES
        pending = (status == "pending" or status is None) and not outcome_rows
        if not verified and not (all_decisions and pending):
            continue
        props = _migration_decision_properties(decision, domain, migration_ts)
        props["status"] = str(status) if verified else "pending"
        if verified and not outcome_rows:
            logger.error(
                "Verified decision %s in domain %s has no outcome row; migration record will fail",
                decision_id,
                domain,
            )
            records.append(
                {
                    "rowid": int(decision["_migration_rowid"]),
                    "decision": props,
                    "error": "missing verified outcome",
                }
            )
            continue
        records.append(
            {
                "rowid": int(decision["_migration_rowid"]),
                "decision": props,
                "outcome": outcome_rows[0] if verified and outcome_rows else None,
                "checkpoints": checkpoints.get(decision_id, []) if verified else [],
                "receipts": receipts.get(decision_id, []) if verified else [],
            }
        )
    return records


def _as_text(value: Any, default: str = "") -> str:
    return default if value is None else str(value)


def _as_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    return int(value)


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


def _as_bool(value: Any) -> bool:
    """Normalize SQLite INTEGER/TEXT truth values for AGE Outcome properties."""
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "no", ""}
    if isinstance(value, (int, float)):
        return bool(value)
    return bool(value)


def _transform_decision(
    decision: Mapping[str, Any],
    outcome: Mapping[str, Any] | None,
    domain: str,
) -> dict[str, Any]:
    """Map SQLite decision/outcome columns to AGE Decision properties."""
    transformed: dict[str, Any] = {
        "decision_id": _as_text(decision.get("decision_id")),
        "domain": _as_text(decision.get("domain"), domain) or domain,
        "category": _as_text(decision.get("category")),
        "category_index": _as_int(decision.get("category_index")),
        "factors_json": _as_text(decision.get("factors_json"), "{}"),
        "factor_vector_json": _as_text(decision.get("factor_vector_json"), "[]"),
        "recommended_action": _as_text(decision.get("recommended_action")),
        "recommended_index": _as_int(decision.get("recommended_index")),
        "confidence": _as_float(decision.get("confidence")),
        "probabilities_json": _as_text(decision.get("probabilities_json"), "{}"),
        "status": _as_text(decision.get("status"), "confirmed"),
        "created_at": _as_float(decision.get("created_at")),
    }
    if outcome is not None:
        transformed.update(
            {
                "actual_action": _as_text(outcome.get("actual_action")),
                "actual_index": _as_int(outcome.get("actual_index")),
                "is_correct": _as_int(outcome.get("is_correct")),
                "verified_at": _as_float(outcome.get("verified_at")),
                "context_json": _as_text(outcome.get("context_json"), "{}"),
            }
        )
    return transformed


def _age_sql(graph_name: str, cypher: str, columns: str) -> str:
    return f"SELECT * FROM cypher({_S(graph_name)}, $$ {cypher} $$) AS ({columns})"


def _row_value(row: Any, key: str, index: int = 0) -> Any:
    if row is None:
        return None
    if isinstance(row, Mapping):
        return row.get(key)
    try:
        return row[key]
    except (TypeError, KeyError):
        return row[index]


def _age_level1_summary(
    conn: psycopg.Connection,
    graph_name: str,
    domain: str,
) -> dict[str, Any]:
    cypher = (
        f"MATCH (d:Decision {{domain: {_S(domain)}}}) "
        "WHERE d.status IN ['confirmed', 'overridden'] "
        "RETURN count(d) AS cnt, min(d.created_at) AS first_created_at, "
        "max(d.created_at) AS last_created_at"
    )
    cursor = conn.execute(
        _age_sql(graph_name, cypher, "cnt agtype, first_created_at agtype, last_created_at agtype")
    )
    row = cursor.fetchone()
    return {
        "count": _row_value(row, "cnt", 0),
        "first_created_at": _row_value(row, "first_created_at", 1),
        "last_created_at": _row_value(row, "last_created_at", 2),
    }


def _topology_expected(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Return source-derived topology counts for the selected migration domain."""
    valid_records = [record for record in records if not record.get("error")]
    verified_ids = [
        str(record["decision"]["decision_id"])
        for record in valid_records
        if record.get("outcome") is not None
    ]
    return {
        "Decision": len(valid_records),
        "Outcome": len(verified_ids),
        "HAS_OUTCOME": len(verified_ids),
        "CentroidCheckpoint": sum(len(record.get("checkpoints", [])) for record in valid_records),
        "EvidenceReceipt": sum(len(record.get("receipts", [])) for record in valid_records),
        "verified_ids": verified_ids,
    }


def _age_topology_count(conn: psycopg.Connection, graph_name: str, cypher: str) -> int:
    row = conn.execute(_age_sql(graph_name, cypher, "cnt agtype")).fetchone()
    return int(normalize_agtype_value(_row_value(row, "cnt", 0)) or 0)


def _verify_topology(
    records: list[dict[str, Any]],
    conn: psycopg.Connection,
    graph_name: str,
    domain: str,
) -> dict[str, Any]:
    """Verify migration-tagged node/edge topology before field comparison."""
    expected = _topology_expected(records)
    domain_literal = _S(domain)
    actual = {
        "Decision": _age_topology_count(conn, graph_name, f"MATCH (d:Decision {{domain: {domain_literal}, migration_source: 'sqlite'}}) RETURN count(d) AS cnt"),
        "Outcome": _age_topology_count(conn, graph_name, f"MATCH (o:Outcome {{domain: {domain_literal}, migration_source: 'sqlite'}}) RETURN count(o) AS cnt"),
        "HAS_OUTCOME": _age_topology_count(conn, graph_name, f"MATCH (d:Decision {{domain: {domain_literal}, migration_source: 'sqlite'}})-[r:HAS_OUTCOME]->(o:Outcome {{domain: {domain_literal}, migration_source: 'sqlite'}}) RETURN count(r) AS cnt"),
        "CentroidCheckpoint": _age_topology_count(conn, graph_name, f"MATCH (c:CentroidCheckpoint {{domain: {domain_literal}, migration_source: 'sqlite'}}) RETURN count(c) AS cnt"),
        "EvidenceReceipt": _age_topology_count(conn, graph_name, f"MATCH (r:EvidenceReceipt {{domain: {domain_literal}, migration_source: 'sqlite'}}) RETURN count(r) AS cnt"),
    }
    mismatches = [
        {"element": element, "expected": expected[element], "actual": actual[element]}
        for element in actual
        if actual[element] != expected[element]
    ]
    sample_failures: list[dict[str, Any]] = []
    for decision_id in expected["verified_ids"][:10]:
        row = conn.execute(
            _age_sql(
                graph_name,
                f"MATCH (d:Decision {{domain: {domain_literal}, decision_id: {_S(decision_id)}, migration_source: 'sqlite'}}) "
                "OPTIONAL MATCH (d)-[r:HAS_OUTCOME]->(o:Outcome) "
                "RETURN count(DISTINCT o) AS outcomes, count(r) AS edges",
                "outcomes agtype, edges agtype",
            )
        ).fetchone()
        outcomes = int(normalize_agtype_value(_row_value(row, "outcomes", 0)) or 0)
        edges = int(normalize_agtype_value(_row_value(row, "edges", 1)) or 0)
        if outcomes != 1 or edges != 1:
            sample_failures.append(
                {"decision_id": decision_id, "expected_outcomes": 1, "actual_outcomes": outcomes,
                 "expected_edges": 1, "actual_edges": edges}
            )
    return {
        "passed": not mismatches and not sample_failures,
        "expected": {key: value for key, value in expected.items() if key != "verified_ids"},
        "actual": actual,
        "mismatches": mismatches,
        "sample_failures": sample_failures,
    }


def _age_decision_by_id(
    conn: psycopg.Connection,
    graph_name: str,
    decision_id: str,
    domain: str,
) -> dict[str, Any] | None:
    cypher = (
        f"MATCH (d:Decision {{domain: {_S(domain)}, decision_id: {_S(decision_id)}}}) "
        "RETURN d.category AS category, d.recommended_action AS recommended_action, "
        "d.confidence AS confidence, d.factors_json AS factors_json"
    )
    cursor = conn.execute(
        _age_sql(
            graph_name,
            cypher,
            "category agtype, recommended_action agtype, confidence agtype, factors_json agtype",
        )
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return {
        "category": normalize_agtype_value(_row_value(row, "category", 0)),
        "recommended_action": normalize_agtype_value(_row_value(row, "recommended_action", 1)),
        "confidence": normalize_agtype_value(_row_value(row, "confidence", 2)),
        "factors_json": normalize_agtype_value(_row_value(row, "factors_json", 3)),
    }


def _write_batch(
    conn: psycopg.Connection,
    batch: list[dict[str, Any]],
    graph_name: str,
) -> dict[str, int]:
    """Write decision topology with MATCH-then-CREATE; never uses MERGE."""
    written = 0
    skipped = 0
    errors = 0
    commit = not bool(getattr(conn, "_migration_defer_commit", False))
    for record in batch:
        if record.get("error"):
            errors += 1
            logger.error(
                "Skipping decision %s in domain %s: %s",
                record.get("decision", {}).get("decision_id"),
                record.get("decision", {}).get("domain"),
                record["error"],
            )
            continue
        properties = dict(record.get("decision", record))
        outcome = record.get("outcome")
        checkpoints = list(record.get("checkpoints", []))
        receipts = list(record.get("receipts", []))
        decision_id = str(properties["decision_id"])
        domain = str(properties.get("domain") or "")
        match = (
            f"MATCH (d:Decision {{decision_id: {_S(decision_id)}, "
            f"domain: {_S(domain)}}}) RETURN d"
        )
        try:
            existing = conn.execute(_age_sql(graph_name, match, "d agtype")).fetchone()
            if existing is not None:
                skipped += 1
                continue
            props = ", ".join(f"{key}: {_S(value)}" for key, value in properties.items())
            create = f"CREATE (d:Decision {{{props}}}) RETURN d"
            conn.execute(_age_sql(graph_name, create, "d agtype"))
            if outcome is not None:
                outcome_properties = dict(outcome)
                if "is_correct" in outcome_properties and outcome_properties["is_correct"] is not None:
                    outcome_properties["is_correct"] = _as_bool(outcome_properties["is_correct"])
                outcome_properties.update(
                    {
                        "decision_id": decision_id,
                        "domain": domain,
                        "reward": None,
                        "verifier": "migration",
                        "override_reason": None,
                        "metadata": "{}",
                        "created_at": properties.get("migration_ts"),
                        "migration_source": "sqlite",
                        "migration_ts": properties.get("migration_ts"),
                    }
                )
                outcome_props = ", ".join(
                    f"{key}: {_S(value)}" for key, value in outcome_properties.items()
                )
                conn.execute(
                    _age_sql(
                        graph_name,
                        f"CREATE (o:Outcome {{{outcome_props}}}) RETURN o",
                        "o agtype",
                    )
                )
                edge = (
                    f"MATCH (d:Decision {{domain: {_S(domain)}, decision_id: {_S(decision_id)}}}), "
                    f"(o:Outcome {{domain: {_S(domain)}, decision_id: {_S(decision_id)}}}) "
                    "CREATE (d)-[:HAS_OUTCOME {decision_id: "
                    f"{_S(decision_id)}, domain: {_S(domain)}" + "}]->(o) RETURN 1"
                )
                conn.execute(_age_sql(graph_name, edge, "created agtype"))
            for checkpoint in checkpoints:
                checkpoint_properties = dict(checkpoint)
                checkpoint_id = checkpoint_properties.get("checkpoint_id") or checkpoint_properties.get("id")
                if checkpoint_id is None:
                    raise ValueError(f"checkpoint for {domain}/{decision_id} has no unique identifier")
                checkpoint_properties.update(
                    {"domain": domain, "decision_id": decision_id, "migration_source": "sqlite", "migration_ts": properties.get("migration_ts")}
                )
                checkpoint_props = ", ".join(
                    f"{key}: {_S(value)}" for key, value in checkpoint_properties.items()
                )
                conn.execute(_age_sql(graph_name, f"CREATE (c:CentroidCheckpoint {{{checkpoint_props}}}) RETURN c", "c agtype"))
                conn.execute(
                    _age_sql(
                        graph_name,
                        f"MATCH (d:Decision {{domain: {_S(domain)}, decision_id: {_S(decision_id)}}}), "
                        f"(c:CentroidCheckpoint {{domain: {_S(domain)}, decision_id: {_S(decision_id)}, checkpoint_id: {_S(checkpoint_id)}}}) "
                        "CREATE (d)-[:HAS_CENTROID_CHECKPOINT {decision_id: "
                        f"{_S(decision_id)}, domain: {_S(domain)}" + "}]->(c) RETURN 1",
                        "created agtype",
                    )
                )
            for receipt in receipts:
                receipt_properties = dict(receipt)
                receipt_id = receipt_properties.get("receipt_intent_id") or receipt_properties.get("id")
                if receipt_id is None:
                    raise ValueError(f"receipt for {domain}/{decision_id} has no unique identifier")
                receipt_properties.update(
                    {"domain": domain, "decision_id": decision_id, "migration_source": "sqlite", "migration_ts": properties.get("migration_ts")}
                )
                receipt_props = ", ".join(
                    f"{key}: {_S(value)}" for key, value in receipt_properties.items()
                )
                conn.execute(_age_sql(graph_name, f"CREATE (r:EvidenceReceipt {{{receipt_props}}}) RETURN r", "r agtype"))
                conn.execute(
                    _age_sql(
                        graph_name,
                        f"MATCH (d:Decision {{domain: {_S(domain)}, decision_id: {_S(decision_id)}}}), "
                        f"(r:EvidenceReceipt {{domain: {_S(domain)}, decision_id: {_S(decision_id)}, receipt_intent_id: {_S(receipt_id)}}}) "
                        "CREATE (d)-[:EMITTED_RECEIPT {decision_id: "
                        f"{_S(decision_id)}, domain: {_S(domain)}" + "}]->(r) RETURN 1",
                        "created agtype",
                    )
                )
            written += 1
        except Exception:
            errors += 1
            if commit:
                conn.rollback()
            else:
                raise
    if commit:
        conn.commit()
    return {"written": written, "skipped": skipped, "errors": errors}


def _checkpoint_path(source_db: str, domain: str) -> Path:
    return Path(source_db).parent / f"{domain}_migration_checkpoint.json"


def _write_checkpoint(path: Path, payload: Mapping[str, Any]) -> None:
    """Atomically publish a checkpoint only after its batch commit."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(dict(payload), indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def _read_checkpoint(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return dict(json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Checkpoint file corrupted: {path}. Delete it to start fresh, or restore from backup."
        ) from exc


def _checkpoint_identity(source_db: str, graph_name: str, all_decisions: bool) -> dict[str, Any]:
    return {
        "source_db_path": str(Path(source_db).resolve()),
        "graph_name": graph_name,
        "all_decisions": bool(all_decisions),
    }


def _checkpoint_payload(
    *,
    domain: str,
    source_db: str,
    graph_name: str,
    all_decisions: bool,
    last_rowid: int,
    batch_number: int,
    decisions_written: int,
    outcomes_written: int,
    status: str,
) -> dict[str, Any]:
    return {
        "domain": domain,
        **_checkpoint_identity(source_db, graph_name, all_decisions),
        "last_rowid": last_rowid,
        "batch_number": batch_number,
        "decisions_written": decisions_written,
        "outcomes_written": outcomes_written,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
    }


def _sqlite_level1_summary(db_path: str, domain: str) -> dict[str, Any]:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt, MIN(created_at) AS first_created_at,
                   MAX(created_at) AS last_created_at
            FROM decisions
            WHERE domain = ? AND status IN ('confirmed', 'overridden')
            """,
            (domain,),
        ).fetchone()
    return {
        "count": int(row[0]),
        "first_created_at": row[1],
        "last_created_at": row[2],
    }


def _float_equal(left: Any, right: Any, tol: float = 0.001) -> bool:
    if left is None or right is None:
        return left is right
    return math.isclose(float(left), float(right), abs_tol=tol)


def _verify_level1(
    db_path: str,
    conn: psycopg.Connection,
    graph_name: str,
    domain: str,
) -> dict[str, Any]:
    """Level 1: verified count plus first/last created_at parity."""
    sqlite_summary = _sqlite_level1_summary(db_path, domain)
    age_summary = _age_level1_summary(conn, graph_name, domain)
    passed = (
        int(age_summary["count"] or 0) == int(sqlite_summary["count"] or 0)
        and _float_equal(age_summary["first_created_at"], sqlite_summary["first_created_at"])
        and _float_equal(age_summary["last_created_at"], sqlite_summary["last_created_at"])
    )
    return {"passed": passed, "details": {"sqlite": sqlite_summary, "age": age_summary}}


def _json_equal(left: Any, right: Any, float_tol: float) -> bool:
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        if set(left.keys()) != set(right.keys()):
            return False
        return all(_json_equal(left[key], right[key], float_tol) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _json_equal(left_value, right_value, float_tol)
            for left_value, right_value in zip(left, right)
        )
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(float(left), float(right), abs_tol=float_tol)
    return bool(left == right)


def _compare_json(a_str: str, b_str: str, float_tol: float = 1e-9) -> bool:
    """Compare JSON values semantically, with float tolerance."""
    try:
        return _json_equal(json.loads(a_str), json.loads(b_str), float_tol)
    except (TypeError, json.JSONDecodeError):
        return False


def _verify_level2(
    db_path: str,
    conn: psycopg.Connection,
    graph_name: str,
    domain: str,
    sample_size: int = 10,
) -> dict[str, Any]:
    """Level 2: content parity for sampled verified decisions."""
    decisions = _read_verified_decisions(db_path, domain)
    if len(decisions) > sample_size:
        decisions = random.Random(0).sample(decisions, sample_size)

    mismatches: list[dict[str, Any]] = []
    for decision in decisions:
        decision_id = str(decision["decision_id"])
        age_decision = _age_decision_by_id(conn, graph_name, decision_id, domain)
        if age_decision is None:
            mismatches.append({"decision_id": decision_id, "field": "missing_age_decision"})
            continue
        checks = {
            "category": age_decision.get("category") == decision.get("category"),
            "recommended_action": age_decision.get("recommended_action")
            == decision.get("recommended_action"),
            "confidence": math.isclose(
                float(age_decision.get("confidence") or 0.0),
                float(decision.get("confidence") or 0.0),
                abs_tol=1e-9,
            ),
            "factors_json": _compare_json(
                str(decision.get("factors_json") or "{}"),
                str(age_decision.get("factors_json") or "{}"),
            ),
        }
        for field, ok in checks.items():
            if not ok:
                mismatches.append({"decision_id": decision_id, "field": field})

    return {
        "passed": not mismatches,
        "details": {"sample_size": len(decisions), "mismatches": mismatches},
    }


def run_migration(
    domain: str,
    source_db: str,
    age_dsn: str,
    graph_name: str,
    dry_run: bool = False,
    batch_size: int = 1000,
    verify: bool = True,
    use_scratch: bool = False,
    verify_l3: bool = False,
    preset_config: Any = None,
    all_decisions: bool = False,
    resume: bool = False,
    checkpoint_file: str | None = None,
) -> dict[str, Any]:
    """Run the decision-log migration, optionally including pending work."""
    if verify and verify_l3 and preset_config is None:
        raise ValueError("preset_config is required when verify_l3=True")

    domain = _validated_domain(domain)
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    if resume and use_scratch:
        return {
            "status": "FAIL",
            "domain": domain,
            "source": source_db,
            "graph_name": graph_name,
            "fail_reason": "Cannot resume a scratch-graph migration. Use direct-write mode.",
        }
    checkpoint = Path(checkpoint_file) if checkpoint_file else _checkpoint_path(source_db, domain)
    try:
        existing_checkpoint = _read_checkpoint(checkpoint) if resume else None
    except ValueError as exc:
        return {
            "status": "FAIL",
            "domain": domain,
            "source": source_db,
            "graph_name": graph_name,
            "checkpoint_file": str(checkpoint),
            "fail_reason": str(exc),
        }
    if existing_checkpoint:
        identity = _checkpoint_identity(source_db, graph_name, all_decisions)
        if existing_checkpoint.get("domain") != domain:
            return {
                "status": "FAIL", "domain": domain, "source": source_db,
                "graph_name": graph_name, "checkpoint_file": str(checkpoint),
                "fail_reason": (
                    f"Checkpoint domain '{existing_checkpoint.get('domain')}' does not match "
                    f"current domain '{domain}'. Delete checkpoint to start fresh."
                ),
            }
        if existing_checkpoint.get("graph_name") != identity["graph_name"]:
            return {
                "status": "FAIL", "domain": domain, "source": source_db,
                "graph_name": graph_name, "checkpoint_file": str(checkpoint),
                "fail_reason": f"Checkpoint was created for graph '{existing_checkpoint.get('graph_name')}' but current target is '{graph_name}'. Delete the checkpoint file to start fresh.",
            }
        for key in ("source_db_path", "all_decisions"):
            if existing_checkpoint.get(key) != identity[key]:
                return {
                    "status": "FAIL", "domain": domain, "source": source_db,
                    "graph_name": graph_name, "checkpoint_file": str(checkpoint),
                    "fail_reason": f"Checkpoint {key} does not match this migration. Delete the checkpoint file to start fresh.",
                }
    transformed = _read_migration_records(source_db, domain, all_decisions=all_decisions)
    verified_records = [record for record in transformed if record["decision"]["status"] in _VERIFIED_STATUSES]
    pending_records = [record for record in transformed if record["decision"]["status"] == "pending"]
    if not transformed:
        # Preserve the established dry-run contract: it is a preflight for a
        # non-empty verified source, whereas a real direct-write migration of
        # an empty source is a successful no-op with a complete checkpoint.
        if dry_run:
            raise ValueError(f"no verified decisions found for domain {domain}")
        _write_checkpoint(
            checkpoint,
            _checkpoint_payload(
                domain=domain, source_db=source_db, graph_name=graph_name,
                all_decisions=all_decisions, last_rowid=0, batch_number=0,
                decisions_written=0, outcomes_written=0, status="complete",
            ),
        )
        return {
            "status": "PASS", "source": source_db, "domain": domain,
            "graph_name": graph_name, "verified_count": 0, "pending_count": 0,
            "all_decisions": bool(all_decisions), "write": {"written": 0, "skipped": 0, "errors": 0},
            "batches": 0, "checkpoint_file": str(checkpoint), "empty_source": True,
        }
    first_created_at = transformed[0]["decision"]["created_at"]
    last_created_at = transformed[-1]["decision"]["created_at"]
    result: dict[str, Any] = {
        "status": "PASS",
        "source": source_db,
        "domain": domain,
        "graph_name": graph_name,
        "verified_count": len(verified_records),
        "pending_count": len(pending_records),
        "all_decisions": bool(all_decisions),
        "first_created_at": first_created_at,
        "last_created_at": last_created_at,
        "dry_run": bool(dry_run),
        "use_scratch": bool(use_scratch),
    }

    result["checkpoint_file"] = str(checkpoint)
    if existing_checkpoint and existing_checkpoint.get("status") == "complete":
        result.update({"already_complete": True, "batches": int(existing_checkpoint.get("batch_number", 0))})
        logger.info("Migration already complete for domain %s: %s", domain, checkpoint)
        return result
    if existing_checkpoint:
        last_rowid = int(existing_checkpoint.get("last_rowid", 0))
        transformed = [record for record in transformed if int(record["rowid"]) > last_rowid]
        result["resumed_from_rowid"] = last_rowid

    if dry_run:
        result["sample"] = transformed[: min(3, len(transformed))]
        print(json.dumps(result, indent=2, sort_keys=True))
        return result

    logger.info(
        "Migrating %s verified + %s pending decisions for domain %s",
        len(verified_records),
        len(pending_records),
        domain,
    )

    conn = _connect_age(age_dsn, graph_name)
    totals = {
        "written": int(existing_checkpoint.get("decisions_written", 0)) if existing_checkpoint else 0,
        "skipped": 0,
        "errors": 0,
    }
    write_graph = graph_name
    scratch_graph: str | None = None
    should_drop_scratch = False
    try:
        if use_scratch:
            scratch_graph = create_scratch_graph(age_dsn, domain)
            should_drop_scratch = True
            result["scratch_graph"] = scratch_graph
            write_graph = scratch_graph
            if not verify_scratch_clean(conn, scratch_graph):
                result["status"] = "FAIL"
                result["fail_reason"] = f"scratch graph is not clean: {scratch_graph}"
                logger.error("SQLite to AGE migration failed: %s", result["fail_reason"])
                return result

        completed_batches = int(existing_checkpoint.get("batch_number", 0)) if existing_checkpoint else 0
        outcomes_written = int(existing_checkpoint.get("outcomes_written", 0)) if existing_checkpoint else 0
        for start in range(0, len(transformed), batch_size):
            batch = transformed[start : start + batch_size]
            batch_number = completed_batches + 1
            try:
                setattr(conn, "_migration_defer_commit", True)
                batch_result = _write_batch(conn, batch, write_graph)
                if batch_result["errors"]:
                    conn.rollback()
                    result["status"] = "FAIL"
                    result["fail_reason"] = f"{batch_result['errors']} write errors"
                    result["write"] = totals
                    return result
                conn.commit()
            except Exception as exc:
                conn.rollback()
                result["status"] = "FAIL"
                result["fail_reason"] = f"batch {batch_number} failed: {type(exc).__name__}: {exc}"
                result["write"] = totals
                logger.error("SQLite to AGE migration failed: %s", result["fail_reason"])
                return result
            finally:
                setattr(conn, "_migration_defer_commit", False)
            for key in totals:
                totals[key] += int(batch_result[key])
            outcomes_in_batch = sum(1 for record in batch if record.get("outcome") is not None)
            outcomes_written += outcomes_in_batch
            completed_batches = batch_number
            last_rowid = int(batch[-1]["rowid"])
            _write_checkpoint(
                checkpoint,
                _checkpoint_payload(
                    domain=domain, source_db=source_db, graph_name=graph_name,
                    all_decisions=all_decisions, last_rowid=last_rowid,
                    batch_number=completed_batches, decisions_written=totals["written"],
                    outcomes_written=outcomes_written, status="in_progress",
                ),
            )
            logger.info(
                "Batch %s: wrote %s decisions, %s outcomes (rowid %s to %s)",
                batch_number,
                batch_result["written"],
                outcomes_in_batch,
                batch[0]["rowid"],
                last_rowid,
            )
        result["write"] = totals
        result["batches"] = completed_batches
        if totals["errors"] > 0:
            result["status"] = "FAIL"
            result["fail_reason"] = f"{totals['errors']} write errors"
            logger.error("SQLite to AGE migration failed: %s", result["fail_reason"])
            return result
        if verify or use_scratch:
            level1 = _verify_level1(source_db, conn, write_graph, domain)
            result["verification"] = {"level1": level1}
            if not level1["passed"]:
                result["status"] = "FAIL"
                result["fail_reason"] = f"Level 1 verification failed: {level1['details']}"
                logger.error("SQLite to AGE migration failed: %s", result["fail_reason"])
                return result

            topology = _verify_topology(transformed, conn, write_graph, domain)
            result["verification"]["topology"] = topology
            if not topology["passed"]:
                result["status"] = "FAIL"
                result["fail_reason"] = f"Topology verification failed: {topology}"
                logger.error("SQLite to AGE migration failed: %s", result["fail_reason"])
                return result

            level2 = _verify_level2(source_db, conn, write_graph, domain)
            result["verification"]["level2"] = level2
            if not level2["passed"]:
                result["status"] = "FAIL"
                result["fail_reason"] = f"Level 2 verification failed: {level2['details']}"
                logger.error("SQLite to AGE migration failed: %s", result["fail_reason"])
                return result

            if verify_l3 and not use_scratch:
                from copilot_sdk.migrate.verify_state import verify_level3

                level3 = verify_level3(source_db, conn, write_graph, domain, preset_config)
                result["verification"]["level3"] = level3
                if not level3["passed"]:
                    result["status"] = "FAIL"
                    result["fail_reason"] = "Level 3 state-vector verification failed"
                    logger.error("SQLite to AGE migration failed: %s", result["fail_reason"])
                    return result
        if use_scratch and scratch_graph is not None:
            should_drop_scratch = False
            try:
                live_copy = copy_to_live(conn, transformed, graph_name, domain)
                result["live_copy"] = live_copy
                live_copy_errors = int(live_copy.get("errors", 0))
                if live_copy_errors:
                    result["status"] = "FAIL"
                    result["fail_reason"] = f"live copy failed: {live_copy_errors} write errors"
                    result["scratch_retained"] = scratch_graph
                    result["scratch_retained_reason"] = "live copy failed"
                    logger.warning(
                        "SQLite to AGE migration retained scratch graph %s after %s live copy errors",
                        scratch_graph,
                        live_copy_errors,
                    )
                    return result
            except Exception as exc:
                result["status"] = "FAIL"
                result["fail_reason"] = f"live copy failed: {type(exc).__name__}: {exc}"
                result["scratch_retained"] = scratch_graph
                result["scratch_retained_reason"] = "live copy failed"
                logger.warning(
                    "SQLite to AGE migration retained scratch graph %s after live copy failure: %s",
                    scratch_graph,
                    exc,
                )
                return result
            if verify_l3:
                from copilot_sdk.migrate.verify_state import verify_level3

                result.setdefault("verification", {})
                level3 = verify_level3(source_db, conn, graph_name, domain, preset_config)
                result["verification"]["level3"] = level3
                if not level3["passed"]:
                    result["status"] = "FAIL"
                    result["fail_reason"] = "Level 3 state-vector verification failed"
                    result["scratch_retained"] = scratch_graph
                    result["scratch_retained_reason"] = "live Level 3 verification failed"
                    logger.error("SQLite to AGE migration failed: %s", result["fail_reason"])
                    return result
            should_drop_scratch = True
        _write_checkpoint(
            checkpoint,
            _checkpoint_payload(
                domain=domain, source_db=source_db, graph_name=graph_name,
                all_decisions=all_decisions,
                last_rowid=int(transformed[-1]["rowid"]) if transformed else int(existing_checkpoint.get("last_rowid", 0)) if existing_checkpoint else 0,
                batch_number=completed_batches, decisions_written=totals["written"],
                outcomes_written=outcomes_written, status="complete",
            ),
        )
        logger.info(
            "Migration complete: %s batches, %s decisions, %s outcomes",
            completed_batches,
            totals["written"],
            outcomes_written,
        )
    finally:
        if scratch_graph is not None and should_drop_scratch:
            drop_scratch_graph(age_dsn, scratch_graph)
        conn.close()
    return result
