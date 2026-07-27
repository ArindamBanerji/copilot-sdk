"""Phase 1 domain backfill — §5.5 SOC Decisions + §5.6 DataOps nodes.

Run: python scripts/phase1_backfill.py

Pre-condition: §5.4 forward-write fix deployed (new decisions get domain='soc').
Tags backfilled nodes with domain_source='backfill' for rollback.

Rollback §5.5:
  MATCH (d:Decision {domain_source:'backfill'}) REMOVE d.domain, d.domain_source

Rollback §5.6:
  MATCH (n) WHERE n.domain_source = 'backfill'
  AND (n:DataQualityAlert OR n:PipelineSystem)
  REMOVE n.domain, n.domain_source
"""
import os
import sys
import psycopg2

DSN = os.environ.get(
    "GRAPH_DSN",
    "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres",
)
GRAPH = os.environ.get("AGE_GRAPH_NAME", "soc_graph")


def _cypher(cur, query, columns="c agtype"):
    sql = f"SELECT * FROM cypher('{GRAPH}', $$ {query} $$) as ({columns})"
    cur.execute(sql)
    return cur.fetchall()


def main():
    conn = psycopg2.connect(DSN)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("LOAD 'age'")
    cur.execute('SET search_path = ag_catalog, "$user", public')

    # ============================================================
    # §5.5: SOC Decision domain backfill
    # ============================================================
    print("=" * 60)
    print("§5.5: SOC DECISION DOMAIN BACKFILL")
    print("=" * 60)

    # Pre-backfill counts
    rows = _cypher(cur, "MATCH (d:Decision) WHERE d.domain IS NULL RETURN count(*)")
    null_before = rows[0][0]
    print(f"  Decisions with domain IS NULL (before): {null_before}")

    rows = _cypher(cur, "MATCH (d:Decision {domain:'soc'}) RETURN count(*)")
    soc_before = rows[0][0]
    print(f"  Decisions with domain='soc' (before): {soc_before}")

    # Backfill
    rows = _cypher(
        cur,
        "MATCH (d:Decision) WHERE d.domain IS NULL "
        "SET d.domain = 'soc', d.domain_source = 'backfill' "
        "RETURN count(*) AS updated",
    )
    updated = rows[0][0]
    print(f"\n  Backfilled: {updated}")

    # Verify
    rows = _cypher(cur, "MATCH (d:Decision) WHERE d.domain IS NULL RETURN count(*)")
    null_after = rows[0][0]

    rows = _cypher(cur, "MATCH (d:Decision {domain:'soc'}) RETURN count(*)")
    soc_after = rows[0][0]

    rows = _cypher(
        cur,
        "MATCH (d:Decision {domain:'soc'}) "
        "WHERE d.outcome IS NOT NULL RETURN count(*)",
    )
    soc_verified = rows[0][0]

    rows = _cypher(cur, "MATCH (d:Decision) RETURN count(*)")
    total = rows[0][0]

    print(f"\n--- §5.5 VERIFICATION ---")
    s1 = "✅" if str(null_after) == "0" else "❌"
    print(f"  domain IS NULL remaining: {null_after} {s1}")
    print(f"  domain='soc' total: {soc_after}")
    print(f"  domain='soc' verified (outcome IS NOT NULL): {soc_verified}")
    print(f"  Total decisions: {total}")

    gate_55 = str(null_after) == "0"

    # ============================================================
    # §5.6: DataOps domain backfill
    # ============================================================
    print("\n" + "=" * 60)
    print("§5.6: DATAOPS DOMAIN BACKFILL")
    print("=" * 60)

    gate_56 = True
    for label in ["DataQualityAlert", "PipelineSystem"]:
        # Count before
        rows = _cypher(cur, f"MATCH (n:{label}) WHERE n.domain IS NULL RETURN count(*)")
        before = rows[0][0]
        print(f"  {label} with domain IS NULL (before): {before}")

        # Backfill
        rows = _cypher(
            cur,
            f"MATCH (n:{label}) WHERE n.domain IS NULL "
            f"SET n.domain = 'dataops', n.domain_source = 'backfill' "
            f"RETURN count(*)",
        )
        filled = rows[0][0]
        print(f"  {label} backfilled: {filled}")

        # Verify
        rows = _cypher(cur, f"MATCH (n:{label}) WHERE n.domain IS NULL RETURN count(*)")
        remaining = rows[0][0]
        status = "✅" if str(remaining) == "0" else "❌"
        if str(remaining) != "0":
            gate_56 = False
        print(f"  {label} untagged remaining: {remaining} {status}")
        print()

    # ============================================================
    # V integrity check
    # ============================================================
    print("=" * 60)
    print("V INTEGRITY CHECK (post-backfill)")
    print("=" * 60)

    # Raw Cypher D2 predicate
    rows = _cypher(
        cur,
        "MATCH (d:Decision) "
        "WHERE (d.domain = 'soc' OR d.domain IS NULL) "
        "AND (d.archived IS NULL OR d.archived <> true) "
        "AND ((d.status IS NOT NULL AND d.status IN ['confirmed','overridden']) "
        "     OR (d.status IS NULL AND d.outcome IS NOT NULL)) "
        "RETURN count(DISTINCT d.decision_id)",
    )
    v_soc = rows[0][0]
    print(f"  V_soc (D2 raw Cypher): {v_soc}")

    # Same query but with domain='soc' only (post-backfill, NULL should be 0)
    rows = _cypher(
        cur,
        "MATCH (d:Decision {domain:'soc'}) "
        "WHERE (d.archived IS NULL OR d.archived <> true) "
        "AND ((d.status IS NOT NULL AND d.status IN ['confirmed','overridden']) "
        "     OR (d.status IS NULL AND d.outcome IS NOT NULL)) "
        "RETURN count(DISTINCT d.decision_id)",
    )
    v_soc_strict = rows[0][0]
    print(f"  V_soc (domain='soc' only): {v_soc_strict}")

    if str(v_soc) == str(v_soc_strict):
        print(f"  Parity: ✅ — legacy NULL scope equals strict domain scope")
    else:
        print(f"  Parity: ❌ — {v_soc} (with NULL) vs {v_soc_strict} (strict)")
        print(f"  This means some verified decisions still have NULL domain")

    # Domain distribution
    print(f"\n--- DOMAIN DISTRIBUTION ---")
    rows = _cypher(
        cur,
        "MATCH (d:Decision) RETURN d.domain, count(d) ORDER BY count(d) DESC",
        "domain agtype, c agtype",
    )
    for row in rows:
        print(f"  {row[0]}: {row[1]}")

    # Null check
    rows = _cypher(cur, "MATCH (d:Decision) WHERE d.domain IS NULL RETURN count(*)")
    null_final = rows[0][0]
    print(f"\n  Decisions with domain IS NULL: {null_final}")

    # ============================================================
    # Summary
    # ============================================================
    print("\n" + "=" * 60)
    gate_all = gate_55 and gate_56 and str(null_final) == "0"
    if gate_all:
        print("GATE: ✅ PASS — All backfills complete. V intact. No NULL domains.")
    else:
        if not gate_55:
            print("GATE: ❌ FAIL — §5.5 SOC backfill incomplete.")
        if not gate_56:
            print("GATE: ❌ FAIL — §5.6 DataOps backfill incomplete.")
        if str(null_final) != "0":
            print(f"GATE: ❌ FAIL — {null_final} decisions still have NULL domain.")
    print("=" * 60)

    conn.close()
    sys.exit(0 if gate_all else 1)


if __name__ == "__main__":
    main()
