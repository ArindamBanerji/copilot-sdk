"""AGE Complete Inventory — All 5 Copilots

Checks EVERY node and edge label in the live AGE graph:
- Count, domain distribution, sample IDs/properties
- Canonical (§4) match or not
- Stale SDK artifact or live SOC data
- Forward-write domain check on age_client.py and age_sdk_adapter.py
- PosteriorStore table check
- SOC test grep for domain IS NULL assumptions

Run from: copilot-sdk root
"""
import os
import psycopg

DSN = "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres"
GRAPH = "soc_graph"

CI_PLATFORM = r"C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\ci-platform"
SOC_FRONTEND = r"C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\frontend"
SOC_BACKEND = r"C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\gen-ai-roi-demo-v4-v50\backend"

CANONICAL_LABELS = {
    "Decision", "Outcome", "FactorVector", "Observation", "Domain",
    "DomainContext", "EvolutionEvent", "Rule", "TransferPattern",
    "EvidenceReceipt", "CentroidCheckpoint", "Fingerprint", "ConservationStatus",
}

CANONICAL_EDGES = {
    "HAS_OUTCOME", "HAS_FACTOR_VECTOR", "ABOUT", "DECIDED_ON",
    "TRIGGERED_EVOLUTION", "SNAPSHOT_AFTER", "HAS_CENTROID_CHECKPOINT",
    "EMITTED_RECEIPT", "FROM_DOMAIN", "TO_DOMAIN", "MEMBER_OF",
    "CONTINUES", "REPLACED_BY", "INVOLVES", "DETECTED_ON",
    "CLASSIFIED_AS", "HAS_INDICATOR", "ORIGINATES_FROM",
}


def q(conn, cypher_body, columns):
    sql = f"SELECT * FROM cypher('{GRAPH}', $$ {cypher_body} $$) as ({columns})"
    return conn.execute(sql).fetchall()


def try_q(conn, cypher_body, columns):
    try:
        return q(conn, cypher_body, columns), None
    except Exception as e:
        return None, str(e)


def section(title):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def run_section(name, fn):
    section(name)
    try:
        return fn()
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def parse_agtype_props(raw_str):
    """Best-effort parse of agtype properties to dict."""
    s = str(raw_str)
    try:
        import json
        return json.loads(s)
    except Exception:
        return None


def main():
    conn = psycopg.connect(DSN)
    conn.autocommit = True
    conn.execute("LOAD 'age'")
    conn.execute('SET search_path = ag_catalog, "$user", public')

    label_report = {}

    def get_labels():
        """Return this graph's labels without binding Python int to oid."""
        graphid = conn.execute(
            "SELECT graphid FROM ag_graph WHERE name = %s", (GRAPH,)
        ).fetchone()
        if graphid is None:
            raise RuntimeError(f"AGE graph not found: {GRAPH}")
        expected_graphid = int(graphid[0])
        rows = conn.execute(
            "SELECT name, kind FROM ag_label "
            f"WHERE graph = {expected_graphid}::oid ORDER BY kind, name"
        ).fetchall()
        rows = [row for row in rows if not str(row[0]).startswith("_")]
        vertex_labels = [r[0] for r in rows if r[1] == 'v']
        edge_labels = [r[0] for r in rows if r[1] == 'e']
        print(f"  Vertex labels: {len(vertex_labels)}")
        print(f"  Edge labels: {len(edge_labels)}")
        return vertex_labels, edge_labels

    # ================================================================
    # 1. GET ALL LABELS FROM CATALOG
    # ================================================================
    labels = run_section("1. LABEL CATALOG", get_labels)
    if labels is None:
        print("  FATAL: Cannot read ag_label")
        conn.close()
        return
    vertex_labels, edge_labels = labels

    # ================================================================
    # 2. PER-VERTEX-LABEL AUDIT
    # ================================================================
    def audit_vertices():
        for label in sorted(vertex_labels):
            print(f"\n  --- {label} ---")

            # Count
            rows, err = try_q(conn, f"MATCH (n:{label}) RETURN count(n) AS c", "c agtype")
            if err:
                print(f"    count error: {err}")
                label_report[label] = {"count": 0, "canonical": label in CANONICAL_LABELS}
                continue
            count = rows[0][0]
            count_int = int(str(count))
            print(f"    count: {count_int}")

            if count_int == 0:
                label_report[label] = {"count": 0, "canonical": label in CANONICAL_LABELS}
                continue

            # Domain distribution
            domains = {}
            dom_rows, err = try_q(conn,
                f"MATCH (n:{label}) RETURN n.domain AS dom, count(*) AS c ORDER BY c DESC",
                "dom agtype, c agtype")
            if dom_rows:
                for r in dom_rows:
                    dom_str = str(r[0]).strip('"')
                    if dom_str in ("null", "None"):
                        dom_str = "NULL"
                    domains[dom_str] = int(str(r[1]))
            print(f"    domains: {domains}")

            # Sample properties (2 nodes)
            sample_ids = []
            prop_rows, err = try_q(conn,
                f"MATCH (n:{label}) RETURN properties(n) LIMIT 2",
                "props agtype")
            if prop_rows:
                for r in prop_rows:
                    raw = str(r[0])
                    props = parse_agtype_props(raw)
                    if props:
                        for id_field in ["decision_id", "alert_id", "campaign_id",
                                         "entity_id", "event_id", "asset_id",
                                         "user_id", "name", "pattern_id", "seed_key"]:
                            if id_field in props:
                                sample_ids.append(f"{id_field}={props[id_field]}")
                                break
                    truncated = raw[:200] + "..." if len(raw) > 200 else raw
                    print(f"    sample: {truncated}")

            # Classification
            canonical = label in CANONICAL_LABELS
            is_soc = any(d in ("soc", "NULL") for d in domains)
            is_sdk = any(d in ("trading", "purchasing", "dataops", "s2p") for d in domains)

            cls = []
            cls.append("CANONICAL" if canonical else "NON-CANONICAL")
            if is_soc and not is_sdk:
                cls.append("SOC-only")
            elif is_sdk and not is_soc:
                cls.append("SDK-only")
            elif is_soc and is_sdk:
                cls.append("MIXED")
            elif not is_soc and not is_sdk:
                cls.append("NO-DOMAIN")

            print(f"    classification: {', '.join(cls)}")

            label_report[label] = {
                "count": count_int, "canonical": canonical,
                "domains": domains, "classification": cls,
                "sample_ids": sample_ids[:3],
            }

    run_section("2. PER-VERTEX-LABEL AUDIT", audit_vertices)

    # ================================================================
    # 3. STALE ARTIFACT CHECK
    # ================================================================
    def stale_check():
        print("\n  Loading Decision decision_ids...")
        dec_rows = q(conn,
            "MATCH (d:Decision) RETURN DISTINCT d.decision_id AS did",
            "did agtype")
        decision_ids = {str(r[0]).strip('"') for r in dec_rows}
        print(f"  {len(decision_ids)} distinct Decision IDs")

        # Labels that should have decision_id
        check_labels = [
            "Outcome", "EvidenceReceipt", "CentroidCheckpoint",
            "DecisionDistanceLog", "DecisionEntityLink",
            "L5Centroid", "ProfileSnapshot",
        ]

        for label in check_labels:
            info = label_report.get(label, {})
            if info.get("count", 0) == 0:
                continue

            print(f"\n  --- {label} ({info['count']} nodes) ---")
            id_rows, err = try_q(conn,
                f"MATCH (n:{label}) WHERE n.decision_id IS NOT NULL "
                f"RETURN DISTINCT n.decision_id AS did",
                "did agtype")
            if err:
                print(f"    error: {err}")
                # Try without the IS NOT NULL filter
                id_rows, err2 = try_q(conn,
                    f"MATCH (n:{label}) RETURN DISTINCT n.decision_id AS did",
                    "did agtype")
                if err2:
                    print(f"    fallback error: {err2}")
                    continue

            if id_rows is None:
                continue

            label_ids = {str(r[0]).strip('"') for r in id_rows
                        if str(r[0]).strip('"') not in ("null", "None", "")}
            overlap = label_ids & decision_ids
            orphans = label_ids - decision_ids

            print(f"    with decision_id: {len(label_ids)}")
            print(f"    matched:          {len(overlap)}")
            print(f"    orphaned:         {len(orphans)}")
            if orphans:
                print(f"    orphan samples:   {sorted(list(orphans))[:3]}")
                if len(orphans) == len(label_ids):
                    print(f"    >>> ALL ORPHANED")
                else:
                    print(f"    >>> PARTIAL — {len(orphans)} orphaned, {len(overlap)} live")

        # L5 labels without decision_id — classify by domain only
        for label in ["L5ConservationState", "L5DKWeight", "L5DKWeightArchive", "DeploymentState"]:
            info = label_report.get(label, {})
            if info.get("count", 0) == 0:
                continue
            print(f"\n  --- {label} ({info['count']} nodes, no decision_id) ---")
            print(f"    domains: {info.get('domains', '?')}")

    run_section("3. STALE ARTIFACT IDENTIFICATION", stale_check)

    # ================================================================
    # 4. EDGE INVENTORY (show zero-count canonical edges too)
    # ================================================================
    def edge_inventory():
        all_edges = set(edge_labels) | CANONICAL_EDGES
        for elabel in sorted(all_edges):
            rows, err = try_q(conn,
                f"MATCH ()-[r:{elabel}]->() RETURN count(r) AS c",
                "c agtype")
            if err:
                # Label might not exist in catalog
                if elabel in CANONICAL_EDGES:
                    print(f"  {elabel}: NOT IN GRAPH (canonical)")
                continue
            count = rows[0][0] if rows else 0
            canonical = "  (canonical)" if elabel in CANONICAL_EDGES else ""
            if str(count) == "0":
                if elabel in CANONICAL_EDGES:
                    print(f"  {elabel}: 0{canonical} *** MISSING ***")
            else:
                print(f"  {elabel}: {count}{canonical}")

    run_section("4. EDGE INVENTORY (including zero-count canonical)", edge_inventory)

    # ================================================================
    # 5. FORWARD-WRITE CHECK
    # ================================================================
    def forward_write_check():
        age_client_path = os.path.join(CI_PLATFORM, "ci_platform", "graph", "age_client.py")
        if not os.path.exists(age_client_path):
            print(f"  NOT FOUND: {age_client_path}")
            return

        with open(age_client_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Find CREATE blocks that mention Decision
        print("\n  --- CREATE blocks mentioning :Decision ---")
        printed_ranges = []
        for i, line in enumerate(lines):
            if ":Decision" not in line:
                continue
            # Check if this is in a CREATE context (within 10 lines)
            window_start = max(0, i - 5)
            window_end = min(len(lines), i + 10)
            window_text = "".join(lines[window_start:window_end])

            if "CREATE" not in window_text and "SET" not in window_text:
                continue

            # Avoid reprinting overlapping ranges
            if any(abs(i - prev) < 15 for prev in printed_ranges):
                continue
            printed_ranges.append(i)

            print(f"\n  --- Context around L{i+1} ---")
            for j in range(window_start, window_end):
                marker = " >>>" if j == i else "    "
                print(f"  {marker} L{j+1}: {lines[j].rstrip()[:130]}")

            # Check for domain in this window
            if "domain" in window_text.lower():
                print(f"  ^^^ 'domain' found in this block")

        # Verdict
        all_windows_text = ""
        for i, line in enumerate(lines):
            if ":Decision" in line:
                ws = max(0, i - 5)
                we = min(len(lines), i + 15)
                block = "".join(lines[ws:we])
                if "CREATE" in block:
                    all_windows_text += block

        print(f"\n  --- VERDICT ---")
        if "domain" in all_windows_text.lower():
            print("  YES — 'domain' appears in at least one Decision CREATE block")
        else:
            print("  NO — 'domain' NOT found in any Decision CREATE block")
            print("  >>> SOC forward-writes will leak domain=NULL")
            print("  >>> D8 MUST add forward-tag clause to age_client.py")

        # SDK adapter check
        print(f"\n  --- AGE SDK Adapter ---")
        adapter_path = os.path.join(CI_PLATFORM, "ci_platform", "graph", "age_sdk_adapter.py")
        if os.path.exists(adapter_path):
            with open(adapter_path, "r", encoding="utf-8") as f:
                adapter_content = f.read()
            found = False
            for i, line in enumerate(adapter_content.splitlines(), 1):
                if "domain" in line and any(kw in line for kw in ["CREATE", "write", "Decision", "SET"]):
                    print(f"  L{i}: {line.strip()[:120]}")
                    found = True
            if not found:
                print("  'domain' not found in write context")
        else:
            print(f"  NOT FOUND: {adapter_path}")

    run_section("5. FORWARD-WRITE CHECK (age_client.py)", forward_write_check)

    # ================================================================
    # 6. PosteriorStore / rl tables
    # ================================================================
    def posterior_check():
        rows = conn.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND (table_name LIKE '%posterior%' OR table_name LIKE '%rl_%')
        """).fetchall()
        if rows:
            for r in rows:
                print(f"  Table: {r[0]}")
                try:
                    cnt = conn.execute(f'SELECT count(*) FROM "{r[0]}"').fetchone()[0]
                    print(f"    rows: {cnt}")
                except Exception as e2:
                    print(f"    count error: {e2}")
        else:
            print("  No posterior/rl tables found")

    run_section("6. PosteriorStore / rl tables", posterior_check)

    # ================================================================
    # 7. SOC TEST GREP: does any test assume domain IS NULL?
    # ================================================================
    def soc_test_grep():
        test_dirs = [
            os.path.join(SOC_FRONTEND, "tests", "e2e"),
            os.path.join(SOC_BACKEND, "tests"),
        ]
        found_any = False
        for test_dir in test_dirs:
            if not os.path.isdir(test_dir):
                print(f"  NOT FOUND: {test_dir}")
                continue
            for root, dirs, files in os.walk(test_dir):
                for fname in files:
                    if not (fname.endswith(".py") or fname.endswith(".ts") or fname.endswith(".spec.ts")):
                        continue
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            for i, line in enumerate(f, 1):
                                if "domain" in line.lower() and any(
                                    kw in line.lower() for kw in ["null", "none", "undefined", "is null"]
                                ):
                                    rel = os.path.relpath(fpath, test_dir)
                                    print(f"  {rel}:{i}: {line.strip()[:100]}")
                                    found_any = True
                    except Exception:
                        pass
        if not found_any:
            print("  No tests reference 'domain' with null/none checks")
            print("  Domain backfill is unlikely to break SOC tests")

    run_section("7. SOC tests referencing domain IS NULL", soc_test_grep)

    # ================================================================
    # SUMMARY TABLE
    # ================================================================
    section("SUMMARY — ALL LABELS WITH DATA")

    print(f"\n  {'Label':<25} {'Count':>6}  {'Canon':>5}  {'Domains':<45}  {'Class'}")
    print(f"  {'-'*25} {'-'*6}  {'-'*5}  {'-'*45}  {'-'*20}")

    for label in sorted(label_report.keys()):
        info = label_report[label]
        count = info.get("count", 0)
        if count == 0:
            continue
        canon = "YES" if info.get("canonical") else "no"
        domains = info.get("domains", {})
        dom_str = ", ".join(f"{k}:{v}" for k, v in domains.items())
        if len(dom_str) > 43:
            dom_str = dom_str[:43] + ".."
        cls = ", ".join(info.get("classification", ["?"]))
        print(f"  {label:<25} {count:>6}  {canon:>5}  {dom_str:<45}  {cls}")

    conn.close()
    print("\n  DONE")


if __name__ == "__main__":
    main()
