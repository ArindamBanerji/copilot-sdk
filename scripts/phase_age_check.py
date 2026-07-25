"""Check AGE clean slate for a domain before migration.

Usage:
    python scripts/phase_age_check.py --domain s2p
    MIGRATION_DOMAIN=s2p python scripts/phase_age_check.py

Requires: GRAPH_DSN and GRAPH_NAME env vars.
"""
import argparse
import os
import sys

import psycopg2


def main():
    parser = argparse.ArgumentParser(description="AGE domain check")
    parser.add_argument("--domain", default=os.environ.get("MIGRATION_DOMAIN", "trading"))
    args = parser.parse_args()
    domain = args.domain

    dsn = os.environ.get("GRAPH_DSN", os.environ.get("AGE_DSN", ""))
    graph = os.environ.get("GRAPH_NAME", os.environ.get("AGE_GRAPH_NAME", "soc_graph"))

    if not dsn:
        print("ERROR: set GRAPH_DSN or AGE_DSN")
        sys.exit(1)

    try:
        conn = psycopg2.connect(dsn)
    except Exception as e:
        print(f"ERROR: cannot connect to AGE — {e}")
        sys.exit(1)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("LOAD 'age'")
    cur.execute('SET search_path = ag_catalog, "$user", public')

    # Total decisions for domain
    cur.execute(
        f"SELECT * FROM cypher('{graph}', $$ "
        f"MATCH (d:Decision {{domain:'{domain}'}}) "
        f"WHERE (d.archived IS NULL OR d.archived <> true) "
        f"RETURN count(d) $$) as (c agtype)"
    )
    active = int(str(cur.fetchone()[0]).strip('"'))

    cur.execute(
        f"SELECT * FROM cypher('{graph}', $$ "
        f"MATCH (d:Decision {{domain:'{domain}'}}) "
        f"WHERE d.archived = true "
        f"RETURN count(d) $$) as (c agtype)"
    )
    archived = int(str(cur.fetchone()[0]).strip('"'))

    # Outcomes
    cur.execute(
        f"SELECT * FROM cypher('{graph}', $$ "
        f"MATCH (d:Decision {{domain:'{domain}'}})-[:HAS_OUTCOME]->(o:Outcome) "
        f"RETURN count(o) $$) as (c agtype)"
    )
    outcomes = int(str(cur.fetchone()[0]).strip('"'))

    # SOC V (cross-domain check)
    cur.execute(
        f"SELECT * FROM cypher('{graph}', $$ "
        f"MATCH (d:Decision {{domain:'soc'}}) "
        f"WHERE (d.archived IS NULL OR d.archived <> true) "
        f"AND ((d.status IS NOT NULL AND d.status IN ['confirmed','overridden']) "
        f"OR (d.status IS NULL AND d.outcome IS NOT NULL)) "
        f"RETURN count(DISTINCT d.decision_id) $$) as (c agtype)"
    )
    soc_v = int(str(cur.fetchone()[0]).strip('"'))

    conn.close()

    print(f"AGE check for domain={domain} graph={graph}")
    print(f"  Active decisions:  {active}")
    print(f"  Archived decisions: {archived}")
    print(f"  Total decisions:   {active + archived}")
    print(f"  Outcomes:          {outcomes}")
    print(f"  SOC V_soc:         {soc_v}")

    if active == 0 and archived == 0:
        print(f"\nCLEAN SLATE: no {domain} decisions in AGE.")
    else:
        print(f"\nNOT CLEAN: {active + archived} {domain} decisions exist.")
        print(f"Run phase_reset.py --domain {domain} to clean, or document retained baseline.")

    sys.exit(0)


if __name__ == "__main__":
    main()
