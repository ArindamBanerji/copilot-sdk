"""Backfill the Decision correctness read-model from SDK Outcome nodes.

The default mode is read-only.  Use ``--apply`` to set ``Decision.correct``
for existing SDK outcomes whose decision has no derived correctness value.

TIMING NOTE: This backfill must run after a copilot's rows land in AGE
(post-migration), not as a one-time standalone. Each copilot migration step
should include a backfill gate: (1) migrate copilot rows to AGE, (2) run the
backfill for that domain, (3) assert the backfill count is non-zero so rows
were fixed, and (4) only then trust ``count_correct`` for that domain.
Running the backfill before migration produces zero rows and silently no-ops;
freshly migrated rows can then arrive with ``Decision.correct`` NULL and the
undercount reappears.
"""

from __future__ import annotations

import argparse
import os
import re
from collections.abc import Sequence
from typing import Any

import psycopg


SDK_DOMAINS = ("s2p", "trading", "purchasing", "dataops")
SUPPORTED_DOMAINS = SDK_DOMAINS + ("soc",)
_GRAPH_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,62}$")


def _literal(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


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


def _validate_graph_name(graph_name: str) -> None:
    if not _GRAPH_RE.fullmatch(graph_name):
        raise ValueError("graph_name must be a simple AGE graph identifier")


def _backfill_query(domain: str) -> str:
    quoted_domain = _literal(domain)
    return f"""
        MATCH (d:Decision)-[:HAS_OUTCOME]->(o:Outcome)
        WHERE d.domain = {quoted_domain}
          AND d.correct IS NULL
          AND (
              o.is_correct = true OR o.is_correct = 1 OR o.is_correct = 'true'
              OR o.is_correct = false OR o.is_correct = 0 OR o.is_correct = 'false'
          )
        SET d.correct = CASE
            WHEN o.is_correct = true THEN true
            WHEN o.is_correct = 1 THEN true
            WHEN o.is_correct = 'true' THEN true
            WHEN o.is_correct = false THEN false
            WHEN o.is_correct = 0 THEN false
            WHEN o.is_correct = 'false' THEN false
        END
        RETURN count(DISTINCT d) AS backfilled
        """


def _unclassifiable_query(domain: str) -> str:
    quoted_domain = _literal(domain)
    return f"""
        MATCH (d:Decision)-[:HAS_OUTCOME]->(o:Outcome)
        WHERE d.domain = {quoted_domain}
          AND d.correct IS NULL
          AND NOT (
              o.is_correct = true OR o.is_correct = 1 OR o.is_correct = 'true'
              OR o.is_correct = false OR o.is_correct = 0 OR o.is_correct = 'false'
          )
        RETURN count(DISTINCT d) AS unclassifiable
        """


def _dry_run_query(domain: str) -> str:
    return f"""
        MATCH (d:Decision)-[:HAS_OUTCOME]->(o:Outcome)
        WHERE d.domain = {_literal(domain)} AND d.correct IS NULL
        RETURN count(d) AS pending
        """


def run_backfill(
    connection: Any,
    graph_name: str,
    *,
    apply: bool = False,
    force: bool = False,
    domains: Sequence[str] = SDK_DOMAINS,
) -> dict[str, int]:
    """Report or apply correctness read-model backfills by domain."""
    _validate_graph_name(graph_name)
    selected = tuple(domains)
    invalid = set(selected).difference(SUPPORTED_DOMAINS)
    if invalid:
        raise ValueError(f"unsupported domain(s): {sorted(invalid)}")
    if apply and "soc" in selected:
        raise ValueError("soc is already authoritative and is read-only for this backfill")

    report: dict[str, int] = {}
    unclassifiable_total = 0
    for domain in selected:
        rows = _cypher(
            connection,
            graph_name,
            _unclassifiable_query(domain),
            "unclassifiable agtype",
        )
        unclassifiable = int(rows[0][0]) if rows else 0
        report[f"{domain}_unclassifiable"] = unclassifiable
        unclassifiable_total += unclassifiable

    if apply and unclassifiable_total and not force:
        raise ValueError(
            f"Found {unclassifiable_total} decisions with unclassifiable is_correct values. "
            "Fix the source data first."
        )

    for domain in selected:
        query = _backfill_query(domain) if apply else _dry_run_query(domain)
        column = "backfilled agtype" if apply else "pending agtype"
        rows = _cypher(connection, graph_name, query, column)
        report[domain] = int(rows[0][0]) if rows else 0
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--age-dsn",
        default=os.environ.get("AGE_DSN") or os.environ.get("GRAPH_DSN"),
    )
    parser.add_argument("--graph-name", default="soc_graph")
    parser.add_argument("--domain", "--domains", action="append", dest="domains")
    parser.add_argument("--dry-run", action="store_true", help="report only; this is the default")
    parser.add_argument("--apply", action="store_true", help="update Decision.correct")
    parser.add_argument(
        "--force",
        action="store_true",
        help="apply classifiable values while leaving unclassifiable values NULL",
    )
    args = parser.parse_args(argv)
    if args.dry_run and args.apply:
        parser.error("--dry-run and --apply are mutually exclusive")
    if args.force and not args.apply:
        parser.error("--force requires --apply")
    if not args.age_dsn:
        parser.error("--age-dsn or AGE_DSN/GRAPH_DSN is required")

    domains = tuple(args.domains) if args.domains else SDK_DOMAINS
    connection: Any = psycopg.connect(args.age_dsn, autocommit=True)
    try:
        connection.execute("LOAD 'age';")
        connection.execute('SET search_path = ag_catalog, "$user", public;')
        report = run_backfill(
            connection,
            args.graph_name,
            apply=args.apply,
            force=args.force,
            domains=domains,
        )
    finally:
        connection.close()

    mode = "APPLY" if args.apply else "DRY-RUN"
    source_tag = "backfill_d_correct"
    print(f"SOURCE={source_tag} MODE={mode} {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
