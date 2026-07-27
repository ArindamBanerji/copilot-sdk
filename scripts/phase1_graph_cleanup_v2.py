"""Phase 1 §5.8 — Drop scratch/diagnostic graphs.

Run: python scripts/phase1_graph_cleanup.py

Keeps only soc_graph and protocol_v2_test.
"""
import re
import sys
import psycopg2

DSN = "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres"
KEEP = {"soc_graph", "protocol_v2_test"}
SAFE_NAME = re.compile(r"^[a-zA-Z0-9_]+$")

conn = psycopg2.connect(DSN)
conn.autocommit = True
cur = conn.cursor()
cur.execute("LOAD 'age'")
cur.execute('SET search_path = ag_catalog, "$user", public')

cur.execute("SELECT name FROM ag_catalog.ag_graph ORDER BY name")
graphs = [r[0] for r in cur.fetchall()]

print("=" * 60)
print(f"§5.8: DIAGNOSTIC GRAPH CLEANUP")
print(f"Total graphs: {len(graphs)}")
print("=" * 60)
for g in graphs:
    print(f"  {g}{' (KEEP)' if g in KEEP else ''}")

to_drop = [g for g in graphs if g not in KEEP]
if not to_drop:
    print("\nNothing to drop.")
else:
    print(f"\nDropping {len(to_drop)}:")
    dropped = 0
    for g in to_drop:
        if not SAFE_NAME.match(g):
            print(f"  SKIPPED {g} — unsafe name")
            continue
        try:
            cur.execute(f"SELECT drop_graph('{g}', true)")
            print(f"  dropped {g}")
            dropped += 1
        except Exception as e:
            print(f"  FAILED {g}: {e}")
            conn.rollback()
            conn.autocommit = True
            cur.execute("LOAD 'age'")
            cur.execute('SET search_path = ag_catalog, "$user", public')
    print(f"\nDropped: {dropped}/{len(to_drop)}")

cur.execute("SELECT name FROM ag_catalog.ag_graph ORDER BY name")
remaining = [r[0] for r in cur.fetchall()]

print(f"\nRemaining ({len(remaining)}):")
for g in remaining:
    print(f"  {g}")

gate = set(remaining) == KEEP
print(f"\n{'=' * 60}")
if gate:
    print("GATE: PASS — Only soc_graph and protocol_v2_test remain.")
else:
    extra = set(remaining) - KEEP
    missing = KEEP - set(remaining)
    if extra:
        print(f"GATE: FAIL — {len(extra)} unexpected graphs remain.")
    if missing:
        print(f"GATE: FAIL — Missing: {missing}")
print("=" * 60)

conn.close()
sys.exit(0 if gate else 1)
