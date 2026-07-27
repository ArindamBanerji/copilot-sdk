"""AGE Phase 1 — PF Finding Investigation

Two critical findings from the pre-flight:
1. ALL 1,015 Outcomes are orphans (zero decision_id matches with Decision)
2. Only 5,114 of 6,253 Decisions lack domain (1,139 already have it)

This script investigates root causes before any backfill proceeds.
"""
import psycopg

DSN = "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres"
GRAPH = "soc_graph"


def q(conn, cypher_body, columns):
    """Run a single Cypher query through AGE's cypher() function."""
    sql = f"SELECT * FROM cypher('{GRAPH}', $$ {cypher_body} $$) as ({columns})"
    return conn.execute(sql).fetchall()


def section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def main():
    conn = psycopg.connect(DSN)
    conn.autocommit = True
    conn.execute("LOAD 'age'")
    conn.execute('SET search_path = ag_catalog, "$user", public')

    # Build Decision ID set once (reused across investigations)
    dec_id_rows = q(conn,
        "MATCH (d:Decision) RETURN DISTINCT d.decision_id AS did",
        "did agtype")
    dec_set_raw = {str(r[0]) for r in dec_id_rows}
    # Also build a normalized set (stripped of surrounding quotes)
    dec_set_norm = {str(r[0]).strip('"') for r in dec_id_rows}

    # ================================================================
    # INVESTIGATION 1: Why are all 1,015 Outcomes orphans?
    # ================================================================
    section("INVESTIGATION 1: Outcome orphan root cause")

    # 1a. THE DEFINITIVE TEST — Cypher JOIN inside AGE
    # This bypasses all Python string comparison artifacts
    print("\n--- 1a. Direct Cypher JOIN (the definitive test) ---")
    try:
        rows = q(conn,
            "MATCH (d:Decision), (o:Outcome) "
            "WHERE d.decision_id = o.decision_id "
            "RETURN count(*) AS matched",
            "matched agtype")
        matched = rows[0][0]
        print(f"  AGE-internal match count: {matched}")
        if str(matched) == "0":
            print("  >>> CONFIRMED: Zero matches inside AGE itself")
            print("  >>> This is NOT a Python comparison artifact")
            print("  >>> The decision_id values genuinely differ")
        else:
            print(f"  >>> {matched} matches found — the PF-4d Python set comparison was wrong")
            print("  >>> Backfill WILL create edges. Re-examine PF-4d logic.")
    except Exception as e:
        print(f"  Error running JOIN: {e}")

    # 1b. Sample Decision.decision_id (with repr for exact Python representation)
    print("\n--- 1b. Decision.decision_id samples ---")
    rows = q(conn,
        "MATCH (d:Decision) RETURN d.decision_id AS did LIMIT 5",
        "did agtype")
    for r in rows:
        print(f"  str:  {r[0]}")
        print(f"  repr: {repr(r[0])}")
        print()

    # 1c. Sample Outcome.decision_id (with repr)
    print("--- 1c. Outcome.decision_id samples ---")
    out_rows = q(conn,
        "MATCH (o:Outcome) RETURN o.decision_id AS did LIMIT 5",
        "did agtype")
    for r in out_rows:
        print(f"  str:  {r[0]}")
        print(f"  repr: {repr(r[0])}")
        print()

    # 1d. Full properties of sample nodes (for finding alternative join keys)
    print("--- 1d. Outcome full properties (sample 3) ---")
    rows = q(conn,
        "MATCH (o:Outcome) RETURN properties(o) LIMIT 3",
        "props agtype")
    for r in rows:
        print(f"  {r[0]}")

    print("\n--- 1e. Decision full properties (sample 2, truncated) ---")
    rows = q(conn,
        "MATCH (d:Decision) RETURN properties(d) LIMIT 2",
        "props agtype")
    for r in rows:
        raw = str(r[0])
        if len(raw) > 600:
            raw = raw[:600] + "..."
        print(f"  {raw}")

    # 1f. Normalized comparison (strip quotes, compare)
    print("\n--- 1f. Normalized set comparison ---")
    out_set_raw = {str(r[0]) for r in out_rows}
    out_set_norm = {str(r[0]).strip('"') for r in out_rows}
    # Check if stripping quotes changes the overlap
    raw_overlap = out_set_raw & dec_set_raw
    norm_overlap = out_set_norm & dec_set_norm
    print(f"  Raw string overlap (first 5 out_ids): {len(raw_overlap)}")
    print(f"  Normalized overlap (strip quotes):    {len(norm_overlap)}")
    if len(norm_overlap) > len(raw_overlap):
        print("  >>> Quote stripping reveals matches — this IS a comparison artifact!")

    # 1g. Manual lookup of one specific Outcome's decision_id
    if out_rows:
        sample_raw = str(out_rows[0][0])
        sample_stripped = sample_raw.strip('"')
        print(f"\n--- 1g. Manual lookup for Outcome decision_id ---")
        print(f"  Looking for: {sample_stripped}")
        try:
            # Try exact match with the stripped value
            rows = q(conn,
                f"MATCH (d:Decision) WHERE d.decision_id = '{sample_stripped}' "
                f"RETURN d.decision_id, d.category LIMIT 1",
                "did agtype, cat agtype")
            if rows:
                print(f"  FOUND (stripped): {rows[0]}")
            else:
                print(f"  NOT FOUND with stripped value")
                # Try with the raw value including quotes
                print(f"  Trying raw value: {sample_raw}")
        except Exception as e:
            print(f"  Error: {e}")

    # ================================================================
    # INVESTIGATION 2: Which Decisions already have domain?
    # ================================================================
    section("INVESTIGATION 2: Existing domain values")

    # 2a. Domain value distribution
    print("\n--- 2a. Domain values ---")
    rows = q(conn,
        "MATCH (d:Decision) WHERE d.domain IS NOT NULL "
        "RETURN d.domain AS dom, count(*) AS n ORDER BY n DESC",
        "dom agtype, n agtype")
    if rows:
        for r in rows:
            print(f"  domain={r[0]}: {r[1]}")
    else:
        print("  No Decisions have domain set")

    # 2b. Total with vs without domain
    print("\n--- 2b. Domain coverage ---")
    rows_null = q(conn,
        "MATCH (d:Decision) WHERE d.domain IS NULL RETURN count(*) AS c",
        "c agtype")
    rows_set = q(conn,
        "MATCH (d:Decision) WHERE d.domain IS NOT NULL RETURN count(*) AS c",
        "c agtype")
    null_count = rows_null[0][0]
    set_count = rows_set[0][0]
    print(f"  domain IS NULL:     {null_count}")
    print(f"  domain IS NOT NULL: {set_count}")

    # 2c. Sample Decisions WITH domain (to understand what already has it)
    print("\n--- 2c. Sample Decisions that already have domain ---")
    rows = q(conn,
        "MATCH (d:Decision) WHERE d.domain IS NOT NULL "
        "RETURN d.decision_id, d.domain, d.category LIMIT 10",
        "did agtype, dom agtype, cat agtype")
    for r in rows:
        print(f"  {r[0]} domain={r[1]} category={r[2]}")

    # 2d. Are the domain-bearing Decisions SDK copilot decisions?
    # (If so, they're NOT SOC and the backfill must skip them)
    print("\n--- 2d. Domain values that are NOT 'soc' ---")
    rows = q(conn,
        "MATCH (d:Decision) WHERE d.domain IS NOT NULL AND d.domain <> 'soc' "
        "RETURN d.domain AS dom, count(*) AS n",
        "dom agtype, n agtype")
    if rows:
        for r in rows:
            print(f"  domain={r[0]}: {r[1]}")
        print("  >>> These are SDK copilot decisions already in AGE")
        print("  >>> Domain backfill must use WHERE d.domain IS NULL, not blanket SET")
    else:
        print("  All domain-bearing Decisions have domain='soc'")

    # ================================================================
    # INVESTIGATION 3: EvidenceReceipt join key
    # ================================================================
    section("INVESTIGATION 3: EvidenceReceipt join key")

    # 3a. Direct Cypher JOIN
    print("\n--- 3a. Direct Cypher JOIN ---")
    try:
        rows = q(conn,
            "MATCH (d:Decision), (r:EvidenceReceipt) "
            "WHERE d.decision_id = r.decision_id "
            "RETURN count(*) AS matched",
            "matched agtype")
        print(f"  AGE-internal match count: {rows[0][0]}")
    except Exception as e:
        print(f"  Error: {e}")

    # 3b. Sample IDs with repr
    print("\n--- 3b. EvidenceReceipt.decision_id samples ---")
    rows = q(conn,
        "MATCH (r:EvidenceReceipt) RETURN r.decision_id AS did LIMIT 5",
        "did agtype")
    for r in rows:
        print(f"  str: {r[0]}  repr: {repr(r[0])}")

    # 3c. Python set comparison (for comparison with Cypher JOIN)
    print("\n--- 3c. Python set orphan check ---")
    er_ids = q(conn,
        "MATCH (r:EvidenceReceipt) RETURN DISTINCT r.decision_id AS did",
        "did agtype")
    er_set = {str(r[0]) for r in er_ids}
    er_orphans = er_set - dec_set_raw
    er_orphans_norm = {str(r[0]).strip('"') for r in er_ids} - dec_set_norm
    print(f"  Raw orphans:        {len(er_orphans)} / {len(er_set)}")
    print(f"  Normalized orphans: {len(er_orphans_norm)} / {len(er_set)}")

    # ================================================================
    # INVESTIGATION 4: CentroidCheckpoint join key
    # ================================================================
    section("INVESTIGATION 4: CentroidCheckpoint join key")

    # 4a. Direct Cypher JOIN
    print("\n--- 4a. Direct Cypher JOIN ---")
    try:
        rows = q(conn,
            "MATCH (d:Decision), (c:CentroidCheckpoint) "
            "WHERE d.decision_id = c.decision_id "
            "RETURN count(*) AS matched",
            "matched agtype")
        print(f"  AGE-internal match count: {rows[0][0]}")
    except Exception as e:
        print(f"  Error: {e}")

    # 4b. Sample IDs with repr
    print("\n--- 4b. CentroidCheckpoint.decision_id samples ---")
    rows = q(conn,
        "MATCH (c:CentroidCheckpoint) RETURN c.decision_id AS did LIMIT 5",
        "did agtype")
    for r in rows:
        print(f"  str: {r[0]}  repr: {repr(r[0])}")

    # 4c. Python set orphan check
    print("\n--- 4c. Python set orphan check ---")
    cc_ids = q(conn,
        "MATCH (c:CentroidCheckpoint) RETURN DISTINCT c.decision_id AS did",
        "did agtype")
    cc_set = {str(r[0]) for r in cc_ids}
    cc_orphans = cc_set - dec_set_raw
    cc_orphans_norm = {str(r[0]).strip('"') for r in cc_ids} - dec_set_norm
    print(f"  Raw orphans:        {len(cc_orphans)} / {len(cc_set)}")
    print(f"  Normalized orphans: {len(cc_orphans_norm)} / {len(cc_set)}")

    conn.close()

    # ================================================================
    # SUMMARY
    # ================================================================
    section("SUMMARY — IMPACT ON BACKFILL PLAN")
    print()
    print("  If Cypher JOIN returned 0 for Outcome: the IDs genuinely differ.")
    print("  If Cypher JOIN returned >0: PF-4d Python comparison was an artifact.")
    print()
    print("  If Cypher JOIN returned 0 but IDs LOOK the same:")
    print("    Check repr() output — AGE agtype quoting may differ.")
    print("    One side may store with quotes, the other without.")
    print()
    print(f"  Decision domain backfill:")
    print(f"    {null_count} need domain='soc'")
    print(f"    {set_count} already have domain — check 2d for non-SOC values")
    print(f"    IMPORTANT: backfill must use WHERE d.domain IS NULL")
    print()


if __name__ == "__main__":
    main()
