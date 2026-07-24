"""Phase 3 — verify Trading migration in AGE. Auto-discovers expected counts."""
import os
import sqlite3
import sys

import psycopg2

SDK_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQLITE_PATH = os.path.join(SDK_ROOT, "apps", "trading", "backend", "data", "trading.db")
AGE_DSN = "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres"
EXPECTED_SOC_V = 4862


def age_count(cur, query: str) -> int:
    cur.execute(
        f"SELECT * FROM cypher('soc_graph', $$ {query} $$) as (c agtype)"
    )
    return int(str(cur.fetchone()[0]).strip('"'))


# Discover expected from SQLite
if not os.path.exists(SQLITE_PATH):
    print(f"ERROR: SQLite not found at {SQLITE_PATH}")
    sys.exit(1)

sq = sqlite3.connect(SQLITE_PATH)
cur_sq = sq.cursor()
expected_verified = cur_sq.execute(
    "SELECT COUNT(*) FROM decisions WHERE status IN ('confirmed','overridden')"
).fetchone()[0]
expected_outcomes = cur_sq.execute("SELECT COUNT(*) FROM outcomes").fetchone()[0]
sq.close()

print("=" * 60)
print("PHASE 3 — TRADING MIGRATION VERIFICATION")
print("=" * 60)
print(f"Source: {SQLITE_PATH}")
print(f"Expected verified: {expected_verified}, outcomes: {expected_outcomes}")
print()

conn = psycopg2.connect(AGE_DSN)
conn.autocommit = True
cur = conn.cursor()
cur.execute("LOAD 'age'")
cur.execute('SET search_path = ag_catalog, "$user", public')

checks = [
    ("Trading Decisions",   "MATCH (d:Decision {domain:'trading'}) RETURN count(d)", expected_verified),
    ("Trading Outcomes",    "MATCH (o:Outcome {domain:'trading'}) RETURN count(o)", expected_outcomes),
    ("Trading HAS_OUTCOME", "MATCH (d:Decision {domain:'trading'})-[r:HAS_OUTCOME]->(o:Outcome) RETURN count(r)", expected_outcomes),
    ("SOC V_soc",           "MATCH (d:Decision {domain:'soc'}) WHERE (d.archived IS NULL OR d.archived <> true) AND ((d.status IS NOT NULL AND d.status IN ['confirmed','overridden']) OR (d.status IS NULL AND d.outcome IS NOT NULL)) RETURN count(DISTINCT d.decision_id)", EXPECTED_SOC_V),
]

gate = True
for label, query, expected in checks:
    actual = age_count(cur, query)
    match = actual == expected
    status = "PASS" if match else "FAIL"
    if not match:
        gate = False
    print(f"  {label}: {actual} (expected {expected}) {status}")

total = age_count(cur, "MATCH (d:Decision) RETURN count(d)")
expected_total = expected_verified + EXPECTED_SOC_V
match = total == expected_total
if not match:
    gate = False
print(f"  Total decisions: {total} (expected {expected_total}) {'PASS' if match else 'FAIL'}")

conn.close()

print()
print("=" * 60)
if gate:
    print("GATE: PASS — Trading migration verified. SOC V unchanged.")
else:
    print("GATE: FAIL — check mismatches above.")
print("=" * 60)
sys.exit(0 if gate else 1)
