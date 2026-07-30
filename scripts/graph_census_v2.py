"""Graph census v2 for the shared AGE graph."""

from __future__ import annotations

import argparse
from typing import Any

import psycopg


DEFAULT_DSN = "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres"
EXPECTED_DOMAINS = {"soc", "s2p", "trading", "purchasing", "dataops"}


def _queries(graph_name: str) -> list[tuple[str, str]]:
    graph = str(graph_name).replace("'", "''")
    prefix = f"SELECT * FROM cypher('{graph}', $$ "
    suffix = " $$)"
    return [
        ("DECISIONS PER DOMAIN", prefix + "MATCH (d:Decision) RETURN d.domain AS d_domain, count(d) AS cnt" + suffix + " AS (d_domain agtype, cnt agtype)"),
        ("CONSERVATION SNAPSHOTS PER DOMAIN", prefix + "MATCH (cs:ConservationStatus) RETURN cs.domain AS d_domain, count(cs) AS cnt" + suffix + " AS (d_domain agtype, cnt agtype)"),
        ("CHECKPOINTS PER DOMAIN", prefix + "MATCH (cp:CentroidCheckpoint) RETURN cp.domain AS d_domain, count(cp) AS cnt" + suffix + " AS (d_domain agtype, cnt agtype)"),
        ("TRANSFER PATTERNS", prefix + "MATCH (tp:TransferPattern) RETURN count(tp) AS cnt" + suffix + " AS (cnt agtype)"),
        ("DOMAIN ANCHORS", prefix + "MATCH (d:Domain) RETURN d.domain_id AS d_id, d.name AS d_name" + suffix + " AS (d_id agtype, d_name agtype)"),
        ("DOMAIN CONTEXT ENTITIES", prefix + "MATCH (dc:DomainContext) RETURN dc.entity_type AS etype, count(dc) AS cnt" + suffix + " AS (etype agtype, cnt agtype)"),
        ("FINGERPRINTS PER DOMAIN", prefix + "MATCH (f:Fingerprint) RETURN f.domain AS d_domain, count(f) AS cnt" + suffix + " AS (d_domain agtype, cnt agtype)"),
        ("EVIDENCE RECEIPTS PER DOMAIN", prefix + "MATCH (r:EvidenceReceipt) RETURN r.domain AS d_domain, count(r) AS cnt" + suffix + " AS (d_domain agtype, cnt agtype)"),
        ("OUTCOMES PER DOMAIN", prefix + "MATCH (o:Outcome) RETURN o.domain AS d_domain, count(o) AS cnt" + suffix + " AS (d_domain agtype, cnt agtype)"),
        ("EVOLUTION EVENTS PER DOMAIN", prefix + "MATCH (e:EvolutionEvent) RETURN e.domain AS d_domain, count(e) AS cnt" + suffix + " AS (d_domain agtype, cnt agtype)"),
        ("TOTAL NODE COUNT", prefix + "MATCH (n) RETURN count(n) AS total" + suffix + " AS (total agtype)"),
    ]


QUERIES = _queries("soc_graph")


def run_census(dsn: str = DEFAULT_DSN, graph_name: str = "soc_graph") -> dict[str, Any]:
    """Run the canonical census queries and return raw rows by section."""
    result: dict[str, Any] = {"graph_name": graph_name, "sections": {}, "errors": []}
    conn: Any = psycopg.connect(dsn, autocommit=True)
    with conn:
        with conn.cursor() as cur:
            cur.execute("LOAD 'age'")
            cur.execute("SET search_path = ag_catalog, '$user', public; SET statement_timeout = '120s'")
            for title, query in _queries(graph_name):
                try:
                    cur.execute(query)
                    result["sections"][title] = [tuple(row) for row in cur.fetchall()]
                except Exception as exc:
                    result["sections"][title] = []
                    result["errors"].append(f"{title}: {exc}")
                    conn.rollback()
    return result


def _clean(value: Any) -> str:
    return str(value).strip('"')


def main() -> None:
    parser = argparse.ArgumentParser(description="Graph census for the shared AGE graph")
    parser.add_argument("--dsn", default=DEFAULT_DSN, help="PostgreSQL DSN")
    parser.add_argument("--graph", default="soc_graph", help="AGE graph name")
    args = parser.parse_args()
    census = run_census(args.dsn, args.graph)

    print("=" * 60)
    print(f"GRAPH CENSUS v2 — {args.graph}")
    print("=" * 60)
    for title, rows in census["sections"].items():
        print(f"\n=== {title} ===")
        if not rows:
            print("  (empty)")
        for row in rows:
            print(f"  {row}")
        for error in census["errors"]:
            if error.startswith(title + ":"):
                print(f"  ERROR: {error.split(': ', 1)[1]}")

    print("\n" + "=" * 60)
    print("PHASE 6 READINESS ASSESSMENT")
    print("=" * 60)
    sections = census["sections"]
    for title, label in (
        ("DECISIONS PER DOMAIN", "DECISIONS"),
        ("CONSERVATION SNAPSHOTS PER DOMAIN", "CONSERVATION"),
        ("CHECKPOINTS PER DOMAIN", "CHECKPOINTS"),
        ("FINGERPRINTS PER DOMAIN", "FINGERPRINTS"),
        ("EVIDENCE RECEIPTS PER DOMAIN", "EVIDENCE RECEIPTS"),
    ):
        values = {_clean(row[0]): _clean(row[1]) for row in sections.get(title, [])}
        missing = EXPECTED_DOMAINS - set(values)
        print(f"  {label}: {'missing ' + ', '.join(sorted(missing)) if missing else 'all 5 domains present'}")
        for domain in sorted(EXPECTED_DOMAINS):
            print(f"    {domain}: {values.get(domain, 'NONE')}")

    transfer_rows = sections.get("TRANSFER PATTERNS", [])
    print(f"  TRANSFERS: {_clean(transfer_rows[0][0]) if transfer_rows else '0'}")
    anchors = {_clean(row[0]) for row in sections.get("DOMAIN ANCHORS", [])}
    missing = EXPECTED_DOMAINS - anchors
    print(f"  DOMAIN ANCHORS: {'missing ' + ', '.join(sorted(missing)) if missing else 'all 5 present'}")
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
