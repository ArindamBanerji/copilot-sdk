"""Phase 3 Step 3 — verify Trading migration in AGE + SOC V unchanged."""
import sys
import psycopg2

DSN = "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres"
EXPECTED_TRADING = 150
EXPECTED_SOC_V = 4862

conn = psycopg2.connect(DSN)
conn.autocommit = True
cur = conn.cursor()
cur.execute("LOAD 'age'")
cur.execute('SET search_path = ag_catalog, "$user", public')

checks = [
    ("Trading Decisions",       "MATCH (d:Decision {domain:'trading'}) RETURN count(d)",                                    EXPECTED_TRADING),
    ("Trading Outcomes",        "MATCH (o:Outcome {domain:'trading'}) RETURN count(o)",                                     EXPECTED_TRADING),
    ("Trading HAS_OUTCOME",     "MATCH (d:Decision {domain:'trading'})-[r:HAS_OUTCOME]->(o:Outcome) RETURN count(r)",       EXPECTED_TRADING),
    ("Trading migration_source","MATCH (d:Decision {domain:'trading', migration_source:'sqlite'}) RETURN count(d)",         EXPECTED_TRADING),
    ("SOC V_soc",               "MATCH (d:Decision {domain:'soc'}) WHERE (d.archived IS NULL OR d.archived <> true) AND ((d.status IS NOT NULL AND d.status IN ['confirmed','overridden']) OR (d.status IS NULL AND d.outcome IS NOT NULL)) RETURN count(DISTINCT d.decision_id)", EXPECTED_SOC_V),
    ("Total decisions",         "MATCH (d:Decision) RETURN count(d)",                                                       EXPECTED_TRADING + EXPECTED_SOC_V),
]

gate = True
print("=" * 60)
print("PHASE 3 — TRADING MIGRATION VERIFICATION")
print("=" * 60)

for label, query, expected in checks:
    cur.execute(f"SELECT * FROM cypher('soc_graph', $$ {query} $$) as (c agtype)")
    actual = cur.fetchone()[0]
    # AGE returns agtype — normalize to int for comparison
    actual_int = int(str(actual).strip('"'))
    match = actual_int == expected
    status = "✅" if match else "❌"
    if not match:
        gate = False
    print(f"  {label}: {actual_int} (expected {expected}) {status}")

conn.close()

print()
print("=" * 60)
if gate:
    print("GATE: ✅ PASS — Trading migration verified. SOC V unchanged.")
else:
    print("GATE: ❌ FAIL — check mismatches above.")
print("=" * 60)

sys.exit(0 if gate else 1)
