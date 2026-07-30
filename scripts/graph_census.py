"""Graph census — check what exists in soc_graph per domain.

Usage:
    python graph_census.py
    python graph_census.py --dsn "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres"
"""

import argparse
import psycopg


DEFAULT_DSN = "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres"

QUERIES = [
    (
        "DECISIONS PER DOMAIN",
        "SELECT * FROM cypher('soc_graph', $$"
        "MATCH (d:Decision) RETURN d.domain AS domain, count(d) AS count"
        "$$) AS (domain agtype, count agtype)",
    ),
    (
        "CONSERVATION SNAPSHOTS PER DOMAIN",
        "SELECT * FROM cypher('soc_graph', $$"
        "MATCH (cs:ConservationStatus) RETURN cs.domain AS domain, count(cs) AS count"
        "$$) AS (domain agtype, count agtype)",
    ),
    (
        "CHECKPOINTS PER DOMAIN",
        "SELECT * FROM cypher('soc_graph', $$"
        "MATCH (cp:CentroidCheckpoint) RETURN cp.domain AS domain, count(cp) AS count"
        "$$) AS (domain agtype, count agtype)",
    ),
    (
        "TRANSFER PATTERNS",
        "SELECT * FROM cypher('soc_graph', $$"
        "MATCH (tp:TransferPattern) RETURN count(tp) AS count"
        "$$) AS (count agtype)",
    ),
    (
        "DOMAIN ANCHORS",
        "SELECT * FROM cypher('soc_graph', $$"
        "MATCH (d:Domain) RETURN d.domain_id AS domain, d.name AS name"
        "$$) AS (domain agtype, name agtype)",
    ),
    (
        "DOMAIN CONTEXT ENTITIES",
        "SELECT * FROM cypher('soc_graph', $$"
        "MATCH (dc:DomainContext) RETURN dc.entity_type AS type, count(dc) AS count"
        "$$) AS (type agtype, count agtype)",
    ),
    (
        "FINGERPRINTS PER DOMAIN",
        "SELECT * FROM cypher('soc_graph', $$"
        "MATCH (f:Fingerprint) RETURN f.domain AS domain, count(f) AS count"
        "$$) AS (domain agtype, count agtype)",
    ),
    (
        "EVIDENCE RECEIPTS PER DOMAIN",
        "SELECT * FROM cypher('soc_graph', $$"
        "MATCH (r:EvidenceReceipt) RETURN r.domain AS domain, count(r) AS count"
        "$$) AS (domain agtype, count agtype)",
    ),
    (
        "OUTCOMES PER DOMAIN",
        "SELECT * FROM cypher('soc_graph', $$"
        "MATCH (o:Outcome) RETURN o.domain AS domain, count(o) AS count"
        "$$) AS (domain agtype, count agtype)",
    ),
    (
        "EVOLUTION EVENTS PER DOMAIN",
        "SELECT * FROM cypher('soc_graph', $$"
        "MATCH (e:EvolutionEvent) RETURN e.domain AS domain, count(e) AS count"
        "$$) AS (domain agtype, count agtype)",
    ),
    (
        "TOTAL NODE COUNT",
        "SELECT * FROM cypher('soc_graph', $$"
        "MATCH (n) RETURN count(n) AS total"
        "$$) AS (total agtype)",
    ),
]


def main():
    parser = argparse.ArgumentParser(description="Graph census for soc_graph")
    parser.add_argument("--dsn", default=DEFAULT_DSN, help="PostgreSQL DSN")
    args = parser.parse_args()

    conn = psycopg.connect(args.dsn)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SET search_path = ag_catalog, public")

    print("=" * 60)
    print("GRAPH CENSUS — soc_graph")
    print("=" * 60)

    for title, query in QUERIES:
        print(f"\n=== {title} ===")
        try:
            cur.execute(query)
            rows = cur.fetchall()
            if not rows:
                print("  (empty)")
            for row in rows:
                print(f"  {row}")
        except Exception as e:
            print(f"  ERROR: {e}")
            conn.rollback()

    # Summary
    print("\n" + "=" * 60)
    print("PHASE 6 READINESS ASSESSMENT")
    print("=" * 60)

    expected_domains = {"soc", "s2p", "trading", "purchasing", "dataops"}

    # Check decisions
    try:
        cur.execute(
            "SELECT * FROM cypher('soc_graph', $$"
            "MATCH (d:Decision) RETURN d.domain AS domain, count(d) AS count"
            "$$) AS (domain agtype, count agtype)"
        )
        decision_domains = set()
        for row in cur.fetchall():
            domain = str(row[0]).strip('"')
            decision_domains.add(domain)
        missing = expected_domains - decision_domains
        if missing:
            print(f"  DECISIONS MISSING FOR: {', '.join(sorted(missing))}")
        else:
            print(f"  DECISIONS: all 5 domains present")
    except Exception as e:
        print(f"  DECISIONS CHECK ERROR: {e}")
        conn.rollback()

    # Check conservation
    try:
        cur.execute(
            "SELECT * FROM cypher('soc_graph', $$"
            "MATCH (cs:ConservationStatus) RETURN cs.domain AS domain, count(cs) AS count"
            "$$) AS (domain agtype, count agtype)"
        )
        conservation_domains = set()
        for row in cur.fetchall():
            domain = str(row[0]).strip('"')
            conservation_domains.add(domain)
        missing = expected_domains - conservation_domains
        if missing:
            print(f"  CONSERVATION MISSING FOR: {', '.join(sorted(missing))}")
        else:
            print(f"  CONSERVATION: all 5 domains present")
    except Exception as e:
        print(f"  CONSERVATION CHECK ERROR: {e}")
        conn.rollback()

    # Check checkpoints
    try:
        cur.execute(
            "SELECT * FROM cypher('soc_graph', $$"
            "MATCH (cp:CentroidCheckpoint) RETURN cp.domain AS domain, count(cp) AS count"
            "$$) AS (domain agtype, count agtype)"
        )
        checkpoint_domains = set()
        for row in cur.fetchall():
            domain = str(row[0]).strip('"')
            checkpoint_domains.add(domain)
        missing = expected_domains - checkpoint_domains
        if missing:
            print(f"  CHECKPOINTS MISSING FOR: {', '.join(sorted(missing))}")
        else:
            print(f"  CHECKPOINTS: all 5 domains present")
    except Exception as e:
        print(f"  CHECKPOINTS CHECK ERROR: {e}")
        conn.rollback()

    # Check domain context for $604K
    try:
        cur.execute(
            "SELECT * FROM cypher('soc_graph', $$"
            "MATCH (dc:DomainContext) "
            "WHERE dc.entity_type = 'sap_change' "
            "OR dc.entity_type = 'celonis_process' "
            "OR dc.entity_type = 'operations_context' "
            "RETURN dc.entity_type AS type, count(dc) AS count"
            "$$) AS (type agtype, count agtype)"
        )
        rows = cur.fetchall()
        if not rows:
            print("  $604K SEED: NO monetary entities (sap_change/celonis_process/operations_context)")
        else:
            for row in rows:
                print(f"  $604K SEED: {row[0]} = {row[1]}")
    except Exception as e:
        print(f"  $604K CHECK ERROR: {e}")
        conn.rollback()

    # Check transfer patterns
    try:
        cur.execute(
            "SELECT * FROM cypher('soc_graph', $$"
            "MATCH (tp:TransferPattern) RETURN count(tp) AS count"
            "$$) AS (count agtype)"
        )
        row = cur.fetchone()
        count = int(str(row[0])) if row else 0
        if count == 0:
            print("  TRANSFERS: none (warm_start has not emitted yet)")
        else:
            print(f"  TRANSFERS: {count} patterns")
    except Exception as e:
        print(f"  TRANSFERS CHECK ERROR: {e}")
        conn.rollback()

    conn.close()
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
