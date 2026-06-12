"""Scratch AGE graph helpers for SQLite-to-AGE migration validation."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Mapping

import psycopg

from ci_platform.graph.age_client import AGEClient

_S = AGEClient.serialize_for_age

_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]{0,62}$")

_DECISION_PROPERTIES = (
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
    "actual_action",
    "actual_index",
    "is_correct",
    "verified_at",
    "context_json",
)


def _identifier(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9_]+", "_", str(value).strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    if not normalized or normalized[0].isdigit():
        normalized = f"d_{normalized}"
    return normalized[:63]


def _validate_graph_name(graph_name: str) -> str:
    if not _IDENTIFIER_RE.fullmatch(graph_name):
        raise ValueError(f"invalid AGE graph name: {graph_name!r}")
    return graph_name


def _age_sql(graph_name: str, cypher: str, columns: str) -> str:
    return f"SELECT * FROM cypher({_S(_validate_graph_name(graph_name))}, $$ {cypher} $$) AS ({columns})"


def _row_value(row: Any, key: str, index: int = 0) -> Any:
    if row is None:
        return None
    if isinstance(row, Mapping):
        return row.get(key)
    try:
        return row[key]
    except (TypeError, KeyError):
        return row[index]


def _open_ddl_connection(dsn: str) -> psycopg.Connection:
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=10)
    conn.execute("LOAD 'age'")
    conn.execute("SET search_path = ag_catalog, '$user', public")
    return conn


def create_scratch_graph(dsn: str, domain: str) -> str:
    """Create a scratch graph for migration and return its graph name."""
    safe_domain = _identifier(domain)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    graph_name = _validate_graph_name(f"scratch_migration_{safe_domain}_{timestamp}")
    conn = _open_ddl_connection(dsn)
    try:
        try:
            conn.execute(f"SELECT drop_graph('{graph_name}', true)")
        except Exception:
            pass
        conn.execute(f"SELECT create_graph('{graph_name}')")
    finally:
        conn.close()
    return graph_name


def drop_scratch_graph(dsn: str, graph_name: str) -> None:
    """Drop a scratch graph, ignoring missing-graph errors."""
    graph_name = _validate_graph_name(graph_name)
    conn = _open_ddl_connection(dsn)
    try:
        try:
            conn.execute(f"SELECT drop_graph('{graph_name}', true)")
        except Exception:
            pass
    finally:
        conn.close()


def verify_scratch_clean(conn: psycopg.Connection, graph_name: str) -> bool:
    """Return True when the scratch graph has zero Decision nodes."""
    cypher = "MATCH (d:Decision) RETURN count(d) AS cnt"
    row = conn.execute(_age_sql(graph_name, cypher, "cnt agtype")).fetchone()
    return int(_row_value(row, "cnt", 0) or 0) == 0


def _scratch_decisions(
    conn: psycopg.Connection,
    scratch_name: str,
    domain: str,
) -> list[dict[str, Any]]:
    returns = ", ".join(f"d.{prop} AS {prop}" for prop in _DECISION_PROPERTIES)
    columns = ", ".join(f"{prop} agtype" for prop in _DECISION_PROPERTIES)
    cypher = f"MATCH (d:Decision {{domain: {_S(domain)}}}) RETURN {returns} ORDER BY d.created_at ASC"
    rows = conn.execute(_age_sql(scratch_name, cypher, columns)).fetchall()
    decisions: list[dict[str, Any]] = []
    for row in rows:
        properties = {
            prop: _row_value(row, prop, index)
            for index, prop in enumerate(_DECISION_PROPERTIES)
        }
        decisions.append(
            {
                key: value
                for key, value in properties.items()
                if value is not None
            }
        )
    return decisions


def copy_to_live(
    conn: psycopg.Connection,
    transformed_decisions: list[dict[str, Any]],
    live_name: str,
    domain: str,
) -> dict[str, int]:
    """Copy original transformed Decision nodes to live using migration writer."""
    from copilot_sdk.migrate.sqlite_to_age import _write_batch

    batch = [
        properties
        for properties in transformed_decisions
        if str(properties.get("domain") or "") == domain
    ]
    result = _write_batch(conn, batch, live_name)
    return {
        "copied": int(result["written"]),
        "skipped": int(result["skipped"]),
        "errors": int(result["errors"]),
    }
