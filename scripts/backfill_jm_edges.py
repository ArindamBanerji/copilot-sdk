"""Backfill canonical JM topology edges in an AGE graph.

The default mode is read-only.  Use ``--apply`` to create missing
``IN_DOMAIN`` and ``HAS_FACTOR_VECTOR`` topology in batches.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from typing import Any

import psycopg


_GRAPH_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")


def _literal(value: Any) -> str:
    """Return an AGE-safe literal without query parameters."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    escaped = str(value).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def _domain_where(domain: str | None, alias: str = "d") -> str:
    if domain is None:
        return ""
    return f" AND {alias}.domain = {_literal(domain)}"


def _cypher(
    connection: Any,
    graph_name: str,
    body: str,
    columns: str,
) -> list[tuple[Any, ...]]:
    sql = (
        f"SELECT * FROM cypher({_literal(graph_name)}, "
        f"$$ {body} $$) AS ({columns})"
    )
    return list(connection.execute(sql).fetchall())


def _count_missing(
    connection: Any,
    graph_name: str,
    edge: str,
    domain: str | None,
    query: Callable[..., list[tuple[Any, ...]]] = _cypher,
) -> int:
    rows = query(
        connection,
        graph_name,
        f"""
        MATCH (d:Decision)
        WHERE d.domain IS NOT NULL{_domain_where(domain)}
        OPTIONAL MATCH (d)-[existing:{edge}]->()
        WITH d, count(existing) AS edge_count
        WHERE edge_count = 0
        RETURN count(d) AS missing
        """,
        "missing agtype",
    )
    return int(rows[0][0]) if rows else 0


def _factor_candidates(
    connection: Any,
    graph_name: str,
    domain: str | None,
    batch_size: int,
    query: Callable[..., list[tuple[Any, ...]]] = _cypher,
) -> list[tuple[Any, ...]]:
    rows = query(
        connection,
        graph_name,
        f"""
        MATCH (d:Decision)
        WHERE d.domain IS NOT NULL
          AND d.factor_vector IS NOT NULL{_domain_where(domain)}
        OPTIONAL MATCH (d)-[existing:HAS_FACTOR_VECTOR]->()
        WITH d, count(existing) AS edge_count
        WHERE edge_count = 0
        RETURN d.decision_id AS decision_id,
               d.domain AS domain,
               d.factor_vector AS factor_vector,
               d.factor_names AS factor_names,
               d.factors AS factors
        LIMIT {int(batch_size)}
        """,
        "decision_id agtype, domain agtype, factor_vector agtype, "
        "factor_names agtype, factors agtype",
    )
    return rows


def _decode(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    candidate = value.strip()
    for _ in range(2):
        try:
            decoded = json.loads(candidate)
        except (TypeError, ValueError):
            return value
        if not isinstance(decoded, str):
            return decoded
        candidate = decoded
    return candidate


def _vector_payload(
    factor_vector: Any,
    factor_names: Any,
    factors: Any,
) -> tuple[list[str], list[float]]:
    vector = _decode(factor_vector)
    names = _decode(factor_names)
    factor_map = _decode(factors)
    if not isinstance(vector, list) and isinstance(factor_map, dict):
        scalar_items = [
            (str(key), value)
            for key, value in factor_map.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        ]
        names = [key for key, _ in scalar_items]
        vector = [float(value) for _, value in scalar_items]
    if not isinstance(vector, list):
        return [], []
    values = [float(value) for value in vector]
    if not isinstance(names, list) or len(names) != len(values):
        names = [f"factor_{index}" for index in range(len(values))]
    return [str(name) for name in names], values


def _create_factor_vector(
    connection: Any,
    graph_name: str,
    decision_id: str,
    domain: str,
    factor_names: list[str],
    factor_values: list[float],
) -> None:
    vector_id = f"{decision_id}:fv"
    names_json = json.dumps(factor_names, sort_keys=True)
    values_json = json.dumps(factor_values, sort_keys=True)
    names_hash = hashlib.sha256(names_json.encode("utf-8")).hexdigest()
    shape_json = json.dumps([len(factor_values)])
    created_at = datetime.now(timezone.utc).isoformat()
    props = (
        "{"
        f"vector_id: {_literal(vector_id)}, "
        f"decision_id: {_literal(decision_id)}, "
        f"domain: {_literal(domain)}, "
        f"dimension: {len(factor_values)}, "
        f"factor_names: {_literal(names_json)}, "
        f"factor_values: {_literal(values_json)}, "
        f"factor_names_hash: {_literal(names_hash)}, "
        f"shape: {_literal(shape_json)}, "
        f"created_at: {_literal(created_at)}, "
        "schema_version: 'protocol_v2'"
        "}"
    )
    existing = _cypher(
        connection,
        graph_name,
        f"MATCH (f:FactorVector {{vector_id: {_literal(vector_id)}}}) RETURN f LIMIT 1",
        "f agtype",
    )
    if not existing:
        _cypher(connection, graph_name, f"CREATE (f:FactorVector {props}) RETURN f", "f agtype")
    _cypher(
        connection,
        graph_name,
        f"""
        MATCH (d:Decision {{decision_id: {_literal(decision_id)}}})
        MATCH (f:FactorVector {{vector_id: {_literal(vector_id)}}})
        WHERE d.domain = {_literal(domain)} AND f.domain = {_literal(domain)}
        OPTIONAL MATCH (d)-[existing:HAS_FACTOR_VECTOR]->(f)
        WITH d, f, count(existing) AS edge_count
        WHERE edge_count = 0
        CREATE (d)-[:HAS_FACTOR_VECTOR]->(f)
        RETURN f
        """,
        "f agtype",
    )


def run_backfill(
    connection: Any,
    graph_name: str,
    *,
    apply: bool = False,
    domain: str | None = None,
    batch_size: int = 100,
    query: Callable[..., list[tuple[Any, ...]]] = _cypher,
) -> dict[str, int]:
    """Report or apply missing JM edges using an injectable query function."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    if not _GRAPH_RE.fullmatch(graph_name):
        raise ValueError("graph_name must be a simple AGE graph identifier")

    in_domain_before = _count_missing(connection, graph_name, "IN_DOMAIN", domain, query)
    factor_before = _count_missing(connection, graph_name, "HAS_FACTOR_VECTOR", domain, query)
    report = {
        "in_domain_missing": in_domain_before,
        "has_factor_vector_missing": factor_before,
        "in_domain_created": 0,
        "has_factor_vector_created": 0,
    }
    if not apply:
        return report

    while True:
        rows = query(
            connection,
            graph_name,
            f"""
            MATCH (d:Decision)
            WHERE d.domain IS NOT NULL{_domain_where(domain)}
            OPTIONAL MATCH (d)-[existing:IN_DOMAIN]->()
            WITH d, count(existing) AS edge_count
            WHERE edge_count = 0
            RETURN d.decision_id AS decision_id, d.domain AS domain
            LIMIT {int(batch_size)}
            """,
            "decision_id agtype, domain agtype",
        )
        if not rows:
            break
        for decision_id, row_domain in rows:
            query(
                connection,
                graph_name,
                f"""
                MATCH (d:Decision {{decision_id: {_literal(_decode(decision_id))}}})
                MATCH (domain:Domain {{domain_id: {_literal(_decode(row_domain))}}})
                WHERE d.domain = {_literal(_decode(row_domain))}
                OPTIONAL MATCH (d)-[existing:IN_DOMAIN]->(domain)
                WITH d, domain, count(existing) AS edge_count
                WHERE edge_count = 0
                CREATE (d)-[:IN_DOMAIN]->(domain)
                RETURN d
                """,
                "d agtype",
            )
            report["in_domain_created"] += 1

    while True:
        rows = _factor_candidates(connection, graph_name, domain, batch_size, query)
        if not rows:
            break
        for decision_id, row_domain, vector, names, factors in rows:
            decoded_id = str(_decode(decision_id))
            decoded_domain = str(_decode(row_domain))
            factor_names, factor_values = _vector_payload(vector, names, factors)
            if factor_names and factor_values:
                _create_factor_vector(
                    connection,
                    graph_name,
                    decoded_id,
                    decoded_domain,
                    factor_names,
                    factor_values,
                )
                report["has_factor_vector_created"] += 1
            else:
                raise ValueError(f"Decision {decoded_id} has no usable factor vector")
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--age-dsn", required=True)
    parser.add_argument("--graph-name", required=True)
    parser.add_argument("--domain")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true", help="report only; this is the default")
    parser.add_argument("--apply", action="store_true", help="create missing nodes and edges")
    args = parser.parse_args(argv)
    if args.dry_run and args.apply:
        parser.error("--dry-run and --apply are mutually exclusive")
    with psycopg.connect(args.age_dsn, autocommit=True) as connection:
        report = run_backfill(
            connection,
            args.graph_name,
            apply=args.apply,
            domain=args.domain,
            batch_size=args.batch_size,
        )
    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"MODE={mode} {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
