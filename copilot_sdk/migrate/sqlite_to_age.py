"""SQLite verified decision-log to AGE migration.

This migrates only the verified decision log. Learned L5/DK/conservation
state is intentionally not migrated; it is re-derived by replaying the
ordered verified log.
"""

from __future__ import annotations

import json
import logging
import math
import os
import random
import sqlite3
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


def _read_verified_decisions(db_path: str) -> list[dict[str, Any]]:
    """Read verified decisions in path-sensitive replay order."""
    query = f"""
        SELECT {", ".join(DECISION_COLUMNS)}
        FROM decisions
        WHERE status IN ('confirmed', 'overridden')
        ORDER BY created_at ASC
    """
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(query).fetchall()]


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


def _age_decision_by_id(
    conn: psycopg.Connection,
    graph_name: str,
    decision_id: str,
) -> dict[str, Any] | None:
    cypher = (
        f"MATCH (d:Decision {{decision_id: {_S(decision_id)}}}) "
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
    """Write one idempotent batch with MATCH-then-CREATE; never uses MERGE."""
    written = 0
    skipped = 0
    errors = 0
    for properties in batch:
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
            written += 1
        except Exception:
            errors += 1
            conn.rollback()
    conn.commit()
    return {"written": written, "skipped": skipped, "errors": errors}


def _sqlite_level1_summary(db_path: str, domain: str) -> dict[str, Any]:
    _ = domain
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS cnt, MIN(created_at) AS first_created_at,
                   MAX(created_at) AS last_created_at
            FROM decisions
            WHERE status IN ('confirmed', 'overridden')
            """
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
    decisions = _read_verified_decisions(db_path)
    if len(decisions) > sample_size:
        decisions = random.Random(0).sample(decisions, sample_size)

    mismatches: list[dict[str, Any]] = []
    for decision in decisions:
        decision_id = str(decision["decision_id"])
        age_decision = _age_decision_by_id(conn, graph_name, decision_id)
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
    batch_size: int = 50,
    verify: bool = True,
    use_scratch: bool = False,
    verify_l3: bool = False,
    preset_config: Any = None,
) -> dict[str, Any]:
    """Run the verified-decision-log migration."""
    if verify and verify_l3 and preset_config is None:
        raise ValueError("preset_config is required when verify_l3=True")

    decisions = _read_verified_decisions(source_db)
    if not decisions:
        raise ValueError(f"no verified decisions found in {source_db}")

    outcomes = _read_outcomes(source_db)
    transformed = [
        _transform_decision(decision, outcomes.get(str(decision["decision_id"])), domain)
        for decision in decisions
    ]
    first_created_at = transformed[0]["created_at"]
    last_created_at = transformed[-1]["created_at"]
    result: dict[str, Any] = {
        "status": "PASS",
        "source": source_db,
        "domain": domain,
        "graph_name": graph_name,
        "verified_count": len(transformed),
        "first_created_at": first_created_at,
        "last_created_at": last_created_at,
        "dry_run": bool(dry_run),
        "use_scratch": bool(use_scratch),
    }

    if dry_run:
        result["sample"] = transformed[: min(3, len(transformed))]
        print(json.dumps(result, indent=2, sort_keys=True))
        return result

    conn = _connect_age(age_dsn, graph_name)
    totals = {"written": 0, "skipped": 0, "errors": 0}
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

        for start in range(0, len(transformed), batch_size):
            batch_result = _write_batch(conn, transformed[start : start + batch_size], write_graph)
            for key in totals:
                totals[key] += int(batch_result[key])
        result["write"] = totals
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
    finally:
        if scratch_graph is not None and should_drop_scratch:
            drop_scratch_graph(age_dsn, scratch_graph)
        conn.close()
    return result
