"""Backfill historical SOC Decision statuses from ``Decision.correct``.

The default mode is read-only.  Use ``--apply`` only after reviewing the
classified counts.  The operation is domain-scoped and idempotent: it updates
only SOC Decisions whose status is still NULL.
"""

from __future__ import annotations

import argparse
import os
import re
from collections.abc import Sequence
from typing import Any

import psycopg


_GRAPH_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")


def _literal(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def _validate_graph_name(graph_name: str) -> None:
    if not _GRAPH_RE.fullmatch(graph_name):
        raise ValueError("graph_name must be a simple AGE graph identifier")


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


def _classification_query() -> str:
    return """
        MATCH (d:Decision)
        WHERE d.domain = 'soc'
          AND d.correct IS NOT NULL
          AND d.status IS NULL
        RETURN d.correct AS correct_value, count(d) AS cnt
        """


def _update_query(correct: bool, status: str) -> str:
    expected = "true" if correct else "false"
    return f"""
        MATCH (d:Decision)
        WHERE d.domain = 'soc'
          AND d.correct = {expected}
          AND d.status IS NULL
        SET d.status = {_literal(status)}
        RETURN count(d) AS updated
        """


def _residual_query() -> str:
    return """
        MATCH (d:Decision)
        WHERE d.domain = 'soc'
          AND d.correct IS NOT NULL
          AND d.status IS NULL
        RETURN count(d) AS remaining
        """


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
    return None


def classify_pending_rows(connection: Any, graph_name: str) -> dict[str, int]:
    """Return true, false, and unclassifiable pending SOC counts."""
    _validate_graph_name(graph_name)
    counts = {"confirmed": 0, "overridden": 0, "unclassifiable": 0}
    rows = _cypher(
        connection,
        graph_name,
        _classification_query(),
        "correct_value agtype, cnt bigint",
    )
    for row in rows:
        value = _as_bool(row[0] if row else None)
        count = int(row[1]) if len(row) > 1 else 0
        if value is True:
            counts["confirmed"] += count
        elif value is False:
            counts["overridden"] += count
        else:
            counts["unclassifiable"] += count
    return counts


def run_backfill(
    connection: Any,
    graph_name: str,
    *,
    apply: bool = False,
) -> dict[str, int]:
    """Report or apply the idempotent SOC status backfill."""
    counts = classify_pending_rows(connection, graph_name)
    if apply and counts["unclassifiable"]:
        raise ValueError(
            "Found "
            f"{counts['unclassifiable']} SOC decisions with unclassifiable correct values. "
            "Fix the source data first."
        )
    if not apply:
        return counts

    confirmed_rows = _cypher(
        connection,
        graph_name,
        _update_query(True, "confirmed"),
        "updated bigint",
    )
    overridden_rows = _cypher(
        connection,
        graph_name,
        _update_query(False, "overridden"),
        "updated bigint",
    )
    remaining_rows = _cypher(
        connection,
        graph_name,
        _residual_query(),
        "remaining bigint",
    )
    return {
        "confirmed": int(confirmed_rows[0][0]) if confirmed_rows else 0,
        "overridden": int(overridden_rows[0][0]) if overridden_rows else 0,
        "unclassifiable": counts["unclassifiable"],
        "remaining": int(remaining_rows[0][0]) if remaining_rows else 0,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dsn",
        default=os.environ.get("AGE_DSN") or os.environ.get("GRAPH_DSN"),
        help="AGE PostgreSQL DSN; defaults to AGE_DSN or GRAPH_DSN",
    )
    parser.add_argument("--graph-name", default="soc_graph")
    parser.add_argument("--dry-run", action="store_true", help="report only; this is the default")
    parser.add_argument("--apply", action="store_true", help="set status from correct")
    args = parser.parse_args(argv)
    if args.dry_run and args.apply:
        parser.error("--dry-run and --apply are mutually exclusive")
    if not args.dsn:
        parser.error("--dsn or AGE_DSN/GRAPH_DSN is required")

    connection: Any = psycopg.connect(args.dsn, autocommit=True)
    try:
        connection.execute("LOAD 'age';")
        connection.execute('SET search_path = ag_catalog, "$user", public;')
        report = run_backfill(connection, args.graph_name, apply=args.apply)
    finally:
        connection.close()

    mode = "APPLY" if args.apply else "DRY-RUN"
    print(f"SOURCE=backfill_soc_status MODE={mode} {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
