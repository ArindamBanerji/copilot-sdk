"""D2 V_soc diagnostic — investigate 4,899 vs 4,862 discrepancy.

Run: python scripts/d2_v_diagnostic.py

Queries the live AGE graph to determine where the 37 missing decisions are.
"""
import psycopg2
import os

DSN = os.environ.get(
    "GRAPH_DSN",
    "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres",
)

QUERIES = [
    ("1. Total SOC decisions (domain='soc' or NULL)",
     "MATCH (d:Decision) WHERE d.domain = 'soc' OR d.domain IS NULL RETURN count(d)"),

    ("2. Branch 1: status IN confirmed/overridden (SOC scope)",
     "MATCH (d:Decision) WHERE (d.domain = 'soc' OR d.domain IS NULL) "
     "AND d.status IS NOT NULL AND d.status IN ['confirmed','overridden'] RETURN count(d)"),

    ("3. Branch 2: status IS NULL AND outcome IS NOT NULL (SOC scope)",
     "MATCH (d:Decision) WHERE (d.domain = 'soc' OR d.domain IS NULL) "
     "AND d.status IS NULL AND d.outcome IS NOT NULL RETURN count(d)"),

    ("4. D2 combined (both branches, DISTINCT)",
     "MATCH (d:Decision) WHERE (d.domain = 'soc' OR d.domain IS NULL) "
     "AND ((d.status IS NOT NULL AND d.status IN ['confirmed','overridden']) "
     "OR (d.status IS NULL AND d.outcome IS NOT NULL)) "
     "RETURN count(DISTINCT d.decision_id)"),

    ("5. Original baseline (d.outcome IS NOT NULL, no domain filter)",
     "MATCH (d:Decision) WHERE d.outcome IS NOT NULL RETURN count(d)"),

    ("6. Decisions with domain NOT soc and NOT NULL (other domains in graph)",
     "MATCH (d:Decision) WHERE d.domain IS NOT NULL AND d.domain <> 'soc' "
     "RETURN d.domain, count(d)"),

    ("7. Decisions with outcome but no domain (leaked from stale data?)",
     "MATCH (d:Decision) WHERE d.domain IS NULL AND d.outcome IS NOT NULL RETURN count(d)"),

    ("8. Decisions with domain='soc' AND outcome IS NOT NULL",
     "MATCH (d:Decision) WHERE d.domain = 'soc' AND d.outcome IS NOT NULL RETURN count(d)"),

    ("9. Decisions with domain IS NULL AND status IS NOT NULL",
     "MATCH (d:Decision) WHERE d.domain IS NULL AND d.status IS NOT NULL "
     "RETURN d.status, count(d)"),

    ("10. Total decisions in graph (all domains)",
     "MATCH (d:Decision) RETURN count(d)"),
]


def main():
    conn = psycopg2.connect(DSN)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("LOAD 'age'")
    cur.execute('SET search_path = ag_catalog, "$user", public')

    print("=" * 60)
    print("D2 V_soc DIAGNOSTIC")
    print("=" * 60)

    for label, cypher in QUERIES:
        try:
            # Queries 6 and 9 return multiple columns
            if "d.domain, count" in cypher or "d.status, count" in cypher:
                if "d.domain" in cypher and "d.status" not in cypher:
                    cur.execute(
                        f"SELECT * FROM cypher('soc_graph', $$ {cypher} $$) "
                        f"as (domain agtype, c agtype)"
                    )
                else:
                    cur.execute(
                        f"SELECT * FROM cypher('soc_graph', $$ {cypher} $$) "
                        f"as (status agtype, c agtype)"
                    )
                rows = cur.fetchall()
                print(f"\n{label}:")
                for row in rows:
                    print(f"  {row[0]}: {row[1]}")
            else:
                cur.execute(
                    f"SELECT * FROM cypher('soc_graph', $$ {cypher} $$) "
                    f"as (c agtype)"
                )
                result = cur.fetchone()[0]
                print(f"\n{label}: {result}")
        except Exception as e:
            print(f"\n{label}: ERROR — {e}")
            conn.rollback()
            cur.execute("LOAD 'age'")
            cur.execute('SET search_path = ag_catalog, "$user", public')

    print("\n" + "=" * 60)
    print("ANALYSIS")
    print("=" * 60)
    print("If query 5 > query 4: the delta is non-SOC decisions with outcomes.")
    print("If query 4 < 4,899: SOC data changed since the July 19-20 measurement.")
    print("If query 7 > 0: domain backfill hasn't run yet (expected).")
    print("If query 8 + query 7 != query 4: predicate logic issue.")
    print("=" * 60)

    conn.close()


if __name__ == "__main__":
    main()
