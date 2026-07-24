"""Phase 3 reset — clean stale Trading data from AGE.

Run from copilot-sdk root: python scripts/phase3_reset_v3.py
"""
import os
import sqlite3
import sys

import psycopg2

AGE_DSN = "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres"

SDK_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORRECT_DB = os.path.join(SDK_ROOT, "apps", "trading", "backend", "data", "trading.db")
STALE_CHECKPOINT = os.path.expanduser(
    "~/.ci-platform/trading/trading_migration_checkpoint.json"
)


def _cypher(cur, query: str):
    """Execute Cypher via AGE SQL wrapper, return all rows."""
    cur.execute(
        f"SELECT * FROM cypher('soc_graph', $$ {query} $$) as (c agtype)"
    )
    return cur.fetchall()


def age_count(cur, query: str) -> int:
    """Run RETURN count() Cypher, return int."""
    rows = _cypher(cur, query)
    return int(str(rows[0][0]).strip('"'))


print("=" * 60)
print("PHASE 3 RESET — clean stale Trading migration")
print("=" * 60)

# Verify correct DB
if not os.path.exists(CORRECT_DB):
    print(f"ERROR: correct DB not found at {CORRECT_DB}")
    sys.exit(1)

conn_sq = sqlite3.connect(CORRECT_DB)
cur_sq = conn_sq.cursor()
total = cur_sq.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
verified = cur_sq.execute(
    "SELECT COUNT(*) FROM decisions WHERE status IN ('confirmed','overridden')"
).fetchone()[0]
outcomes = cur_sq.execute("SELECT COUNT(*) FROM outcomes").fetchone()[0]
conn_sq.close()
print(f"Correct DB: {CORRECT_DB}")
print(f"  {total} total, {verified} verified, {outcomes} outcomes")

# Connect to AGE
conn = psycopg2.connect(AGE_DSN)
conn.autocommit = True
cur = conn.cursor()
cur.execute("LOAD 'age'")
cur.execute('SET search_path = ag_catalog, "$user", public')

# Pre-cleanup counts
stale_decisions = age_count(cur,
    "MATCH (d:Decision {domain:'trading'}) RETURN count(d)"
)
stale_outcomes = age_count(cur,
    "MATCH (o:Outcome {domain:'trading'}) RETURN count(o)"
)
soc_v_before = age_count(cur,
    "MATCH (d:Decision {domain:'soc'}) "
    "WHERE (d.archived IS NULL OR d.archived <> true) "
    "AND ((d.status IS NOT NULL AND d.status IN ['confirmed','overridden']) "
    "OR (d.status IS NULL AND d.outcome IS NOT NULL)) "
    "RETURN count(DISTINCT d.decision_id)"
)

print(f"\nAGE before cleanup:")
print(f"  Trading Decisions: {stale_decisions}")
print(f"  Trading Outcomes:  {stale_outcomes}")
print(f"  SOC V_soc:         {soc_v_before}")

if stale_decisions == 0 and stale_outcomes == 0:
    print("\nNo stale Trading data. Proceed to migration.")
    conn.close()
    sys.exit(0)

# Confirm
print(f"\nWill delete {stale_decisions} Decisions + {stale_outcomes} Outcomes + edges.")
confirm = input("Type YES to proceed: ")
if confirm.strip() != "YES":
    print("Aborted.")
    conn.close()
    sys.exit(1)

# Delete using proven Phase 1 pattern: DETACH DELETE + RETURN count(*)
# Domain-scoped: only trading. SOC data untouched.
print("\nDeleting stale Trading data...")

for label, desc in [
    ("Outcome", "Outcome nodes"),
    ("CentroidCheckpoint", "CentroidCheckpoint nodes"),
    ("EvidenceReceipt", "EvidenceReceipt nodes"),
    ("Decision", "Decision nodes"),
]:
    rows = _cypher(cur,
        f"MATCH (n:{label} {{domain:'trading'}}) DETACH DELETE n RETURN count(*)"
    )
    count = int(str(rows[0][0]).strip('"'))
    print(f"  {desc}: {count} deleted")

# Verify
remaining_d = age_count(cur,
    "MATCH (d:Decision {domain:'trading'}) RETURN count(d)"
)
remaining_o = age_count(cur,
    "MATCH (o:Outcome {domain:'trading'}) RETURN count(o)"
)
soc_v_after = age_count(cur,
    "MATCH (d:Decision {domain:'soc'}) "
    "WHERE (d.archived IS NULL OR d.archived <> true) "
    "AND ((d.status IS NOT NULL AND d.status IN ['confirmed','overridden']) "
    "OR (d.status IS NULL AND d.outcome IS NOT NULL)) "
    "RETURN count(DISTINCT d.decision_id)"
)

conn.close()

print(f"\nAGE after cleanup:")
print(f"  Trading Decisions: {remaining_d}")
print(f"  Trading Outcomes:  {remaining_o}")
print(f"  SOC V_soc:         {soc_v_after} (was {soc_v_before})")

if remaining_d == 0 and remaining_o == 0 and soc_v_after == soc_v_before:
    print("\nCLEANUP: PASS")
else:
    print("\nCLEANUP: FAIL — verify manually")
    sys.exit(1)

# Delete stale checkpoint
if os.path.exists(STALE_CHECKPOINT):
    os.remove(STALE_CHECKPOINT)
    print(f"Deleted stale checkpoint: {STALE_CHECKPOINT}")

# Also check for checkpoint next to correct DB
correct_checkpoint = os.path.join(
    os.path.dirname(CORRECT_DB), "trading_migration_checkpoint.json"
)
if os.path.exists(correct_checkpoint):
    os.remove(correct_checkpoint)
    print(f"Deleted checkpoint: {correct_checkpoint}")

print()
print("=" * 60)
print("CLEANUP COMPLETE. Next:")
print(f"  python -m copilot_sdk.migrate sqlite_to_age \\")
print(f'    --domain=trading --source="{CORRECT_DB}" \\')
print(f'    --age-dsn="{AGE_DSN}" \\')
print(f"    --graph-name=soc_graph --batch-size=500")
print("=" * 60)
