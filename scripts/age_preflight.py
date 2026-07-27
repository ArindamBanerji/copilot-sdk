"""AGE Phase 1 Pre-Flight Checks (PF-1 through PF-7)

Run from: copilot-sdk root
  python scripts/age_preflight.py

Requires: AGE running on localhost:5433, psycopg installed
Reference: docs/design/age_shared_graph_migration_v3_2.md §1.1
"""
import sys
import psycopg

DSN = "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres"
GRAPH = "soc_graph"

PASS = "PASS"
FAIL = "FAIL"
INFO = "INFO"

gates: list[tuple[str, str, str]] = []


def q(conn, cypher_body, columns):
    """Run a single Cypher query through AGE's cypher() function."""
    sql = f"SELECT * FROM cypher('{GRAPH}', $$ {cypher_body} $$) as ({columns})"
    return conn.execute(sql).fetchall()


def run_check(name, fn):
    """Run a single pre-flight check with error isolation."""
    print(f"\n{'=' * 60}")
    print(f"  {name}")
    print(f"{'=' * 60}")
    try:
        fn()
    except Exception as e:
        print(f"  ERROR: {e}")
        gates.append((name, FAIL, f"Exception: {e}"))


def main():
    # --- Connection ---
    print("Connecting to AGE...")
    try:
        conn = psycopg.connect(DSN)
        conn.autocommit = True
        conn.execute("LOAD 'age'")
        conn.execute('SET search_path = ag_catalog, "$user", public')
        print(f"  Connected: {DSN}")
        print(f"  Graph: {GRAPH}")
    except Exception as e:
        print(f"  FATAL: Cannot connect to AGE: {e}")
        sys.exit(1)

    # --- Context counts (not a gate, but needed for dry-run math) ---
    def ctx_counts():
        labels = ["Decision", "Outcome", "EvidenceReceipt", "CentroidCheckpoint"]
        for label in labels:
            rows = q(conn, f"MATCH (n:{label}) RETURN count(n) AS c", "c agtype")
            count = rows[0][0] if rows else "?"
            print(f"  {label}: {count}")
            gates.append((f"COUNT_{label}", INFO, str(count)))

    run_check("CONTEXT: Node counts (for dry-run math)", ctx_counts)

    # --- PF-1: Outcome values ---
    def pf1():
        rows = q(conn,
            "MATCH (d:Decision) RETURN d.outcome AS v, count(*) AS n ORDER BY n DESC",
            "v agtype, n agtype")
        sentinels_found = False
        for r in rows:
            val, count = r[0], r[1]
            marker = ""
            # Flag potential sentinels
            val_str = str(val).strip('"').strip("'")
            if val_str in ("", "pending", "unknown", "null"):
                marker = " *** SENTINEL — V predicate must exclude this ***"
                sentinels_found = True
            print(f"  {val}: {count}{marker}")
        if sentinels_found:
            gates.append(("PF-1", FAIL, "Non-terminal outcome values found — narrow V predicate"))
        else:
            gates.append(("PF-1", PASS, "All outcome values are terminal or null"))

    run_check("PF-1: What does embedded outcome contain?", pf1)

    # --- PF-2: Is correct a second verification signal? ---
    def pf2():
        rows = q(conn,
            "MATCH (d:Decision) WHERE d.outcome IS NULL AND d.correct IS NOT NULL RETURN count(*) AS c",
            "c agtype")
        count = rows[0][0]
        print(f"  orphaned_correct: {count}")
        if str(count) != "0":
            print("  >>> V predicate MUST include: OR d.correct IS NOT NULL")
            print("  >>> Without this, these decisions are silently dropped from V")
            gates.append(("PF-2", FAIL, f"{count} decisions have correct but no outcome — add to predicate"))
        else:
            print("  outcome IS NOT NULL covers all verified decisions")
            gates.append(("PF-2", PASS, "correct is not an independent signal"))

    run_check("PF-2: Is 'correct' a second verification signal?", pf2)

    # --- PF-3: Status values ---
    def pf3():
        rows = q(conn,
            "MATCH (d:Decision) RETURN d.status AS v, count(*) AS n",
            "v agtype, n agtype")
        has_status = False
        for r in rows:
            val, count = r[0], r[1]
            if str(val).strip('"') not in ("null", "None", ""):
                has_status = True
            print(f"  {val}: {count}")
        if has_status:
            print("  >>> Mixed domain ALREADY EXISTS — D2 priority rises above backfill")
            gates.append(("PF-3", FAIL, "Some Decisions already have status — mixed domain"))
        else:
            gates.append(("PF-3", PASS, "All Decisions lack status (expected)"))

    run_check("PF-3: Do any Decisions carry 'status'?", pf3)

    # --- PF-4a: Duplicate Outcomes ---
    def pf4a():
        rows = q(conn,
            "MATCH (o:Outcome) WITH o.decision_id AS did, count(*) AS c WHERE c > 1 RETURN did, c",
            "did agtype, c agtype")
        print(f"  duplicates: {len(rows)} rows")
        for r in rows[:5]:
            print(f"    {r[0]}: {r[1]}")
        if len(rows) > 0:
            gates.append(("PF-4a", FAIL, f"{len(rows)} decision_ids have multiple Outcomes"))
        else:
            gates.append(("PF-4a", PASS, "No duplicate Outcomes"))

    run_check("PF-4a: Duplicate Outcomes per decision", pf4a)

    # --- PF-4b: Duplicate EvidenceReceipts ---
    def pf4b():
        rows = q(conn,
            "MATCH (r:EvidenceReceipt) WITH r.decision_id AS did, count(*) AS c WHERE c > 1 RETURN did, c",
            "did agtype, c agtype")
        print(f"  duplicates: {len(rows)} rows")
        for r in rows[:5]:
            print(f"    {r[0]}: {r[1]}")
        if len(rows) > 0:
            gates.append(("PF-4b", FAIL, f"{len(rows)} decision_ids have multiple EvidenceReceipts"))
        else:
            gates.append(("PF-4b", PASS, "No duplicate EvidenceReceipts"))

    run_check("PF-4b: Duplicate EvidenceReceipts per decision", pf4b)

    # --- PF-4c: Duplicate CentroidCheckpoints ---
    def pf4c():
        rows = q(conn,
            "MATCH (c:CentroidCheckpoint) WITH c.decision_id AS did, count(*) AS cnt WHERE cnt > 1 RETURN did, cnt",
            "did agtype, cnt agtype")
        print(f"  duplicates: {len(rows)} rows")
        for r in rows[:5]:
            print(f"    {r[0]}: {r[1]}")
        if len(rows) > 0:
            gates.append(("PF-4c", FAIL, f"{len(rows)} decision_ids have multiple CentroidCheckpoints"))
        else:
            gates.append(("PF-4c", PASS, "No duplicate CentroidCheckpoints"))

    run_check("PF-4c: Duplicate CentroidCheckpoints per decision", pf4c)

    # --- PF-4d: Orphan Outcomes ---
    def pf4d():
        # Safer approach: count Outcomes whose decision_id does NOT appear in Decision
        # Uses two separate counts to avoid slow cross-product OPTIONAL MATCH
        outcome_ids = q(conn,
            "MATCH (o:Outcome) RETURN DISTINCT o.decision_id AS did",
            "did agtype")
        decision_ids = q(conn,
            "MATCH (d:Decision) RETURN DISTINCT d.decision_id AS did",
            "did agtype")
        outcome_set = {str(r[0]) for r in outcome_ids}
        decision_set = {str(r[0]) for r in decision_ids}
        orphans = outcome_set - decision_set
        print(f"  total Outcome decision_ids: {len(outcome_set)}")
        print(f"  total Decision decision_ids: {len(decision_set)}")
        print(f"  orphans (Outcome with no Decision): {len(orphans)}")
        if orphans:
            for oid in list(orphans)[:5]:
                print(f"    orphan: {oid}")
        gates.append(("PF-4d", INFO, f"{len(orphans)} orphan Outcomes — excluded from backfill"))

    run_check("PF-4d: Orphan Outcomes (no matching Decision)", pf4d)

    # --- PF-4e: CentroidCheckpoints with null decision_id ---
    def pf4e():
        rows = q(conn,
            "MATCH (c:CentroidCheckpoint) WHERE c.decision_id IS NULL RETURN count(*) AS no_did",
            "no_did agtype")
        count = rows[0][0]
        print(f"  no_decision_id: {count}")
        gates.append(("PF-4e", INFO, f"{count} CentroidCheckpoints lack decision_id — excluded from backfill"))

    run_check("PF-4e: CentroidCheckpoints with null decision_id", pf4e)

    # --- PF-6: Decisions without domain ---
    def pf6():
        rows = q(conn,
            "MATCH (d:Decision) WHERE d.domain IS NULL RETURN count(*) AS no_domain",
            "no_domain agtype")
        count = rows[0][0]
        print(f"  no_domain: {count}")
        print(f"  >>> These must be backfilled to domain='soc' in week 1")
        print(f"  >>> Every Phase 3+ proof query filters on domain")
        gates.append(("PF-6", INFO, f"{count} Decisions lack domain — backfill required"))

    run_check("PF-6: Decisions without domain", pf6)

    # --- PF-7: is_correct stored type ---
    def pf7():
        rows = q(conn,
            "MATCH (o:Outcome) RETURN o.is_correct AS val, count(*) AS n ORDER BY n DESC",
            "val agtype, n agtype")
        for r in rows:
            val = r[0]
            print(f"  {val} (python type: {type(val).__name__}): {r[1]}")
        # Determine if integer or boolean for Phase 6 query syntax
        sample_vals = [str(r[0]).strip('"') for r in rows if str(r[0]).strip('"') not in ("null", "None")]
        if any(v in ("true", "false") for v in sample_vals):
            print("  >>> is_correct is BOOLEAN — Phase 6 queries must use true/false, not 1/0")
            gates.append(("PF-7", INFO, "is_correct is boolean — use true/false in queries"))
        elif any(v in ("0", "1") for v in sample_vals):
            print("  >>> is_correct is INTEGER — Phase 6 queries can use 1/0")
            gates.append(("PF-7", INFO, "is_correct is integer — use 1/0 in queries"))
        else:
            print(f"  >>> Unexpected values: {sample_vals[:5]}")
            gates.append(("PF-7", FAIL, f"Unexpected is_correct values: {sample_vals[:5]}"))

    run_check("PF-7: is_correct stored type", pf7)

    # --- Summary ---
    conn.close()

    print("\n")
    print("=" * 60)
    print("  GATE SUMMARY")
    print("=" * 60)

    failures = []
    for name, status, detail in gates:
        if status == FAIL:
            print(f"  {FAIL}  {name}: {detail}")
            failures.append(name)
        elif status == PASS:
            print(f"  {PASS}  {name}: {detail}")
        else:
            print(f"  {INFO}  {name}: {detail}")

    print()
    if failures:
        print(f"  VERDICT: {len(failures)} GATE FAILURE(S) — {', '.join(failures)}")
        print(f"  Resolve before proceeding. See v3.2 §1.1 decision rules.")
    else:
        print(f"  VERDICT: ALL GATES PASSED")
        print(f"  Proceed to edge backfill (v3.2 §1.2)")

    print()
    print("  Dry-run expected counts (from context + PF-4d/4e):")
    print("    HAS_OUTCOME:              Outcome count - orphan count")
    print("    EMITTED_RECEIPT:           EvidenceReceipt count")
    print("    HAS_CENTROID_CHECKPOINT:   CentroidCheckpoint count - null-decision_id count")
    print()


if __name__ == "__main__":
    main()
