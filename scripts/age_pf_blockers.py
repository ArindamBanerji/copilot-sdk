"""AGE Phase 1 — Blocker Investigation (v3.3 review)

Blocker 1: Do trading/dataops SQLite decision_ids overlap with the orphan AGE decision_ids?
Blocker 2: What domain do CentroidCheckpoint nodes actually have?
Plus: Check for shared cross-domain entities (§6.6).
Plus: V_soc regression baseline.
"""
import psycopg
import sqlite3
import os

DSN = "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres"
GRAPH = "soc_graph"

BASE = r"C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
S2P_BASE = r"C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\s2p-copilot"

CI_DATA_DIR = os.environ.get("CI_DATA_DIR", os.path.expanduser("~/.ci-platform"))

SQLITE_CANDIDATES = {
    "trading": [
        os.path.join(CI_DATA_DIR, "trading", "trading.db"),
        os.path.join(BASE, "apps", "trading", "backend", "app", "data", "trading.db"),
    ],
    "purchasing": [
        os.path.join(CI_DATA_DIR, "purchasing", "purchasing.db"),
        os.path.join(BASE, "apps", "purchasing", "backend", "app", "data", "purchasing.db"),
    ],
    "dataops": [
        os.path.join(CI_DATA_DIR, "dataops", "dataops.db"),
        os.path.join(BASE, "apps", "dataops", "backend", "app", "data", "dataops.db"),
    ],
    "s2p": [
        os.path.join(CI_DATA_DIR, "s2p", "s2p.db"),
        os.path.join(S2P_BASE, "backend", "app", "data", "s2p.db"),
    ],
}


def q(conn, cypher_body, columns):
    """Run a single Cypher query through AGE's cypher() function."""
    sql = f"SELECT * FROM cypher('{GRAPH}', $$ {cypher_body} $$) as ({columns})"
    return conn.execute(sql).fetchall()


def section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def find_sqlite(domain):
    """Find the SQLite DB for a domain. Returns (path, None) or (None, tried_paths)."""
    for path in SQLITE_CANDIDATES.get(domain, []):
        if os.path.exists(path):
            return path
    return None


def get_sqlite_decision_ids(db_path):
    """Extract decision_ids from a SQLite GraphStore DB."""
    try:
        with sqlite3.connect(db_path) as sconn:
            # Check what tables exist
            tables = [t[0] for t in sconn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()]

            if "decisions" not in tables:
                print(f"    No 'decisions' table. Tables: {tables}")
                return set()

            # Check columns
            cols = [c[1] for c in sconn.execute("PRAGMA table_info(decisions)").fetchall()]
            if "decision_id" not in cols:
                print(f"    No 'decision_id' column. Columns: {cols}")
                return set()

            rows = sconn.execute("SELECT DISTINCT decision_id FROM decisions").fetchall()
            return {r[0] for r in rows if r[0] is not None}
    except Exception as e:
        print(f"    Error reading {db_path}: {e}")
        return set()


def run_section(name, fn):
    """Run a section with error isolation."""
    section(name)
    try:
        fn()
    except Exception as e:
        print(f"  ERROR in {name}: {e}")
        import traceback
        traceback.print_exc()


def main():
    conn = psycopg.connect(DSN)
    conn.autocommit = True
    conn.execute("LOAD 'age'")
    conn.execute('SET search_path = ag_catalog, "$user", public')

    # ================================================================
    # BLOCKER 1: Do SDK SQLite decision_ids overlap with AGE orphan IDs?
    # ================================================================
    def blocker1():
        # Get orphan decision_ids from AGE (all three node types)
        print("\n--- 1a. Orphan decision_ids from AGE ---")
        age_outcome_ids = q(conn,
            "MATCH (o:Outcome) RETURN DISTINCT o.decision_id AS did",
            "did agtype")
        orphan_outcome = {str(r[0]).strip('"') for r in age_outcome_ids}
        print(f"  Outcome orphans: {len(orphan_outcome)}")

        age_er_ids = q(conn,
            "MATCH (r:EvidenceReceipt) RETURN DISTINCT r.decision_id AS did",
            "did agtype")
        orphan_er = {str(r[0]).strip('"') for r in age_er_ids}
        print(f"  EvidenceReceipt orphans: {len(orphan_er)}")

        age_cc_ids = q(conn,
            "MATCH (c:CentroidCheckpoint) RETURN DISTINCT c.decision_id AS did",
            "did agtype")
        orphan_cc = {str(r[0]).strip('"') for r in age_cc_ids}
        print(f"  CentroidCheckpoint orphans: {len(orphan_cc)}")

        # Union of all orphan IDs
        all_orphans = orphan_outcome | orphan_er | orphan_cc
        print(f"  Union (all orphan decision_ids): {len(all_orphans)}")
        for oid in sorted(list(all_orphans))[:5]:
            print(f"    {oid}")

        # Check each SDK copilot's SQLite
        print("\n--- 1b. SQLite decision_id overlap per copilot ---")
        any_overlap = False
        for domain in ["trading", "dataops", "purchasing", "s2p"]:
            db_path = find_sqlite(domain)
            if db_path is None:
                print(f"\n  {domain}: NOT FOUND")
                for p in SQLITE_CANDIDATES.get(domain, []):
                    print(f"    tried: {p}")
                continue

            print(f"\n  {domain}: {db_path}")
            sqlite_ids = get_sqlite_decision_ids(db_path)
            print(f"    SQLite decisions: {len(sqlite_ids)}")
            if not sqlite_ids:
                print(f"    (empty or unreadable)")
                continue

            # Show sample SQLite IDs for format comparison
            for sid in sorted(list(sqlite_ids))[:3]:
                print(f"    sample: {sid}")

            # Check overlap with each orphan type
            o_overlap = orphan_outcome & sqlite_ids
            er_overlap = orphan_er & sqlite_ids
            cc_overlap = orphan_cc & sqlite_ids
            total_overlap = len(o_overlap) + len(er_overlap) + len(cc_overlap)

            print(f"    Outcome overlap:          {len(o_overlap)}")
            print(f"    EvidenceReceipt overlap:  {len(er_overlap)}")
            print(f"    CentroidCheckpoint overlap: {len(cc_overlap)}")

            if total_overlap > 0:
                any_overlap = True
                print(f"    >>> OVERLAP EXISTS ({total_overlap} total)")
                for oid in sorted(list(o_overlap | er_overlap | cc_overlap))[:5]:
                    print(f"      MATCH: {oid}")
            else:
                print(f"    >>> Zero overlap — orphans are NOT from this copilot's current data")

        print(f"\n--- 1c. Blocker 1 verdict ---")
        if any_overlap:
            print("  OVERLAP FOUND — must resolve before Phase 3")
            print("  Options: delete orphans (if stale) or modify adapter (if current)")
        else:
            print("  ZERO OVERLAP across all copilots")
            print("  Orphans are stale dev artifacts — safe to delete in week 1")

    run_section("BLOCKER 1: Orphan disposition", blocker1)

    # ================================================================
    # BLOCKER 2: CentroidCheckpoint actual domain values
    # ================================================================
    def blocker2():
        print("\n--- 2a. CentroidCheckpoint domain distribution ---")
        rows = q(conn,
            "MATCH (c:CentroidCheckpoint) "
            "RETURN c.domain AS dom, count(*) AS n ORDER BY n DESC",
            "dom agtype, n agtype")
        for r in rows:
            print(f"  domain={r[0]}: {r[1]}")

        # Sample nodes per domain value
        print("\n--- 2b. Samples per domain ---")
        for r in rows:
            dom_str = str(r[0]).strip('"')
            try:
                if dom_str in ("null", "None", ""):
                    samples = q(conn,
                        "MATCH (c:CentroidCheckpoint) WHERE c.domain IS NULL "
                        "RETURN c.decision_id, c.category LIMIT 3",
                        "did agtype, cat agtype")
                else:
                    samples = q(conn,
                        f"MATCH (c:CentroidCheckpoint {{domain: '{dom_str}'}}) "
                        f"RETURN c.decision_id, c.category LIMIT 3",
                        "did agtype, cat agtype")
                for s in samples:
                    print(f"  domain={r[0]}: decision_id={s[0]}, category={s[1]}")
            except Exception as e:
                print(f"  domain={r[0]}: query error: {e}")

        print("\n--- 2c. Blocker 2 verdict ---")
        domains_found = {str(r[0]).strip('"') for r in rows}
        if "soc" in domains_found:
            print("  Some CentroidCheckpoints have domain='soc'")
            print("  v3.3 F1 claim ('all are SDK data') is WRONG for this label")
            print("  Must re-check zero-overlap conclusion for CentroidCheckpoints with domain='soc'")
        else:
            print("  No CentroidCheckpoints have domain='soc'")
            print("  v3.3 F1 claim confirmed for CentroidCheckpoints")

    run_section("BLOCKER 2: CentroidCheckpoint domain ownership", blocker2)

    # ================================================================
    # §6.6: Do any shared cross-domain entities exist?
    # ================================================================
    def cross_domain():
        print("\n--- 3a. DomainContext node count ---")
        try:
            rows = q(conn, "MATCH (ctx:DomainContext) RETURN count(*) AS c", "c agtype")
            print(f"  DomainContext nodes: {rows[0][0]}")
        except Exception as e:
            print(f"  DomainContext query failed: {e}")

        # Simple approach: count alerts linked to decisions that have domain set,
        # and check if any alert is linked to decisions from >1 domain.
        # Avoid collect(DISTINCT ...) and size() which AGE may not support.
        print("\n--- 3b. Alert nodes linked to domain-bearing Decisions ---")
        try:
            # Count distinct (alert_id, domain) pairs
            rows = q(conn,
                "MATCH (d:Decision)-[:DECIDED_ON]->(a:Alert) "
                "WHERE d.domain IS NOT NULL "
                "RETURN d.domain AS dom, count(DISTINCT a) AS alerts",
                "dom agtype, alerts agtype")
            for r in rows:
                print(f"  domain={r[0]}: {r[1]} linked alerts")
        except Exception as e:
            print(f"  Error: {e}")

        print("\n  NOTE: Full cross-domain entity check requires the domain")
        print("  backfill to complete first (only 1,139 of 6,253 have domain).")
        print("  Re-run after domain backfill to get accurate results.")

    run_section("§6.6: Shared cross-domain entities", cross_domain)

    # ================================================================
    # V_soc regression baseline
    # ================================================================
    def v_baseline():
        # Current V: counts ALL Decisions with outcome IS NOT NULL.
        # This is correct NOW because no SDK Decision nodes exist in AGE.
        # After SDK migrations, must filter by domain='soc'.
        rows = q(conn,
            "MATCH (d:Decision) WHERE d.outcome IS NOT NULL "
            "RETURN count(*) AS v_soc",
            "v_soc agtype")
        v_all = rows[0][0]

        # Also compute domain-filtered for comparison
        rows2 = q(conn,
            "MATCH (d:Decision) WHERE d.outcome IS NOT NULL AND d.domain = 'soc' "
            "RETURN count(*) AS v_soc_filtered",
            "v_soc_filtered agtype")
        v_filtered = rows2[0][0]

        rows3 = q(conn,
            "MATCH (d:Decision) WHERE d.outcome IS NOT NULL AND d.domain IS NULL "
            "RETURN count(*) AS v_soc_null",
            "v_soc_null agtype")
        v_null = rows3[0][0]

        print(f"  V (all, outcome IS NOT NULL):           {v_all}")
        print(f"  V (domain='soc', outcome IS NOT NULL):  {v_filtered}")
        print(f"  V (domain IS NULL, outcome IS NOT NULL): {v_null}")
        print(f"  Sum (filtered + null):                  {int(str(v_filtered)) + int(str(v_null))}")
        print()
        print(f"  Expected: {v_all} = 'correct' (3,749) + 'incorrect' (1,150)")
        print(f"  'incorrect' = overridden, which counts toward V per JM §4.2")
        print(f"  >>> REGRESSION BASELINE: V_soc = {v_all}")
        print(f"  >>> After domain backfill: V(domain='soc') must = {v_all}")
        print(f"  >>> After Rule #38: V_soc must not change")
        print(f"  >>> After SDK migrations: V(domain='soc') must still = {v_all}")

    run_section("V_soc regression baseline", v_baseline)

    conn.close()

    # ================================================================
    # SUMMARY
    # ================================================================
    section("DISPOSITION SUMMARY")
    print()
    print("  Blocker 1: check overlap results above")
    print("    Zero overlap → delete orphans in week 1")
    print("    Any overlap  → decide delete-or-link before Phase 3")
    print()
    print("  Blocker 2: check CentroidCheckpoint domain results above")
    print("    No domain='soc' → v3.3 F1 confirmed")
    print("    Some domain='soc' → re-examine zero-overlap for that subset")
    print()
    print("  V_soc: record the baseline number above")
    print("  Cross-domain entities: re-run after domain backfill")
    print()


if __name__ == "__main__":
    main()
