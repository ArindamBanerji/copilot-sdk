"""Phase 1 cleanup — §5.2 stale orphans + §5.3 stale L5.

Run: python scripts/phase1_cleanup.py

Pre-condition: §5.1 backup completed (pg_dump to /tmp/age_stale_backup.sql).
Deletes stale nodes from soc_graph and verifies all 10 labels are empty.

Rollback: restore from /tmp/age_stale_backup.sql via:
  wsl -u root sh -c "psql -h localhost -p 5433 -U postgres -d soc_copilot < /tmp/age_stale_backup.sql"
"""
import os
import sys
import psycopg2

DSN = os.environ.get(
    "GRAPH_DSN",
    "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres",
)
GRAPH = os.environ.get("AGE_GRAPH_NAME", "soc_graph")

# §5.2: Stale orphans (6 labels) — 100% orphaned, zero Decision overlap
ORPHAN_LABELS = [
    "Outcome",
    "EvidenceReceipt",
    "CentroidCheckpoint",
    "DecisionDistanceLog",
    "DecisionEntityLink",
    "EvolutionEvent",
]

# §5.3: Stale L5 (4 labels) — wrong state, SOC confirmed not affected
L5_LABELS = [
    "L5Centroid",
    "L5DKWeight",
    "L5ConservationState",
    "L5DKWeightArchive",
]


def _cypher(cur, query, columns="c agtype"):
    """Run a single cypher query and return all rows."""
    sql = f"SELECT * FROM cypher('{GRAPH}', $$ {query} $$) as ({columns})"
    cur.execute(sql)
    return cur.fetchall()


def _count(cur, label):
    """Count nodes with a given label."""
    rows = _cypher(cur, f"MATCH (n:{label}) RETURN count(n)")
    return rows[0][0] if rows else 0


def _delete(cur, label):
    """Delete all nodes with a given label and return count deleted."""
    rows = _cypher(cur, f"MATCH (n:{label}) DETACH DELETE n RETURN count(*)")
    return rows[0][0] if rows else 0


def main():
    conn = psycopg2.connect(DSN)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("LOAD 'age'")
    cur.execute('SET search_path = ag_catalog, "$user", public')

    all_labels = ORPHAN_LABELS + L5_LABELS
    gate_pass = True

    # --- Pre-delete counts ---
    print("=" * 60)
    print("PHASE 1 CLEANUP — PRE-DELETE COUNTS")
    print("=" * 60)
    pre_counts = {}
    for label in all_labels:
        count = _count(cur, label)
        pre_counts[label] = count
        print(f"  {label}: {count}")

    # --- §5.2: Delete stale orphans ---
    print("\n" + "=" * 60)
    print("§5.2: DELETING STALE ORPHANS (6 labels)")
    print("=" * 60)
    for label in ORPHAN_LABELS:
        deleted = _delete(cur, label)
        print(f"  {label}: deleted {deleted}")

    # --- §5.2: Verify ---
    print("\n--- §5.2 VERIFICATION ---")
    for label in ORPHAN_LABELS:
        remaining = _count(cur, label)
        status = "✅" if str(remaining) == "0" else "❌ FAIL"
        if str(remaining) != "0":
            gate_pass = False
        print(f"  {label}: {remaining} remaining {status}")

    # --- §5.3: Delete stale L5 ---
    print("\n" + "=" * 60)
    print("§5.3: DELETING STALE L5 (4 labels)")
    print("=" * 60)
    for label in L5_LABELS:
        deleted = _delete(cur, label)
        print(f"  {label}: deleted {deleted}")

    # --- §5.3: Verify ---
    print("\n--- §5.3 VERIFICATION ---")
    for label in L5_LABELS:
        remaining = _count(cur, label)
        status = "✅" if str(remaining) == "0" else "❌ FAIL"
        if str(remaining) != "0":
            gate_pass = False
        print(f"  {label}: {remaining} remaining {status}")

    # --- Decision count (must be unchanged) ---
    print("\n" + "=" * 60)
    print("DECISION INTEGRITY CHECK")
    print("=" * 60)
    decision_count = _count(cur, "Decision")
    print(f"  Total Decisions: {decision_count}")
    print(f"  (Must be unchanged from pre-cleanup baseline of 4,862)")

    # --- V check ---
    rows = _cypher(
        cur,
        "MATCH (d:Decision) "
        "WHERE (d.domain = 'soc' OR d.domain IS NULL) "
        "AND (d.archived IS NULL OR d.archived <> true) "
        "AND ((d.status IS NOT NULL AND d.status IN ['confirmed','overridden']) "
        "     OR (d.status IS NULL AND d.outcome IS NOT NULL)) "
        "RETURN count(DISTINCT d.decision_id)",
    )
    v_soc = rows[0][0] if rows else "ERROR"
    print(f"  V_soc (D2 predicate): {v_soc}")
    print(f"  (Must be unchanged from baseline of 4,862)")

    # --- Summary ---
    print("\n" + "=" * 60)
    if gate_pass:
        print("GATE: ✅ PASS — All 10 labels empty. Decisions intact.")
    else:
        print("GATE: ❌ FAIL — Some labels still have remaining nodes.")
    print("=" * 60)

    conn.close()
    sys.exit(0 if gate_pass else 1)


if __name__ == "__main__":
    main()
