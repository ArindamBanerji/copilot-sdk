"""SQLite Copilot Audit — All 4 SDK Copilots

Per-copilot:
- Decision count (total, by status, verified, pending/ghost)
- Outcome count and all GraphStore table counts
- V baseline (for regression tracking through migration)
- Table schema (columns, tables)
- Rule #38 compliance (direct SQLiteGraphStore construction)
- GraphStore interaction patterns (from main.py)
- ID format samples
- Per-copilot specific concerns

Run from: copilot-sdk root
"""
import os
import sqlite3

SDK_BASE = r"C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\copilot-sdk"
S2P_BASE = r"C:\Users\baner\CopyFolder\IoT_thoughts\python-projects\kaggle_experiments\claude_projects\s2p-copilot"
CI_DATA_DIR = os.environ.get("CI_DATA_DIR", os.path.expanduser("~/.ci-platform"))

SQLITE_PATHS = {
    "trading": [
        os.path.join(CI_DATA_DIR, "trading", "trading.db"),
        os.path.join(SDK_BASE, "apps", "trading", "backend", "app", "data", "trading.db"),
    ],
    "purchasing": [
        os.path.join(CI_DATA_DIR, "purchasing", "purchasing.db"),
        os.path.join(SDK_BASE, "apps", "purchasing", "backend", "app", "data", "purchasing.db"),
    ],
    "dataops": [
        os.path.join(CI_DATA_DIR, "dataops", "dataops.db"),
        os.path.join(SDK_BASE, "apps", "dataops", "backend", "app", "data", "dataops.db"),
    ],
    "s2p": [
        os.path.join(CI_DATA_DIR, "s2p", "s2p.db"),
        os.path.join(S2P_BASE, "backend", "app", "data", "s2p.db"),
    ],
}

MAIN_PY_PATHS = {
    "trading": os.path.join(SDK_BASE, "apps", "trading", "backend", "app", "main.py"),
    "purchasing": os.path.join(SDK_BASE, "apps", "purchasing", "backend", "app", "main.py"),
    "dataops": os.path.join(SDK_BASE, "apps", "dataops", "backend", "app", "main.py"),
    "s2p": os.path.join(S2P_BASE, "backend", "app", "main.py"),
}

GRAPH_STATUS_PATHS = {
    "trading": os.path.join(SDK_BASE, "apps", "trading", "backend", "app", "graph_status.py"),
    "purchasing": os.path.join(SDK_BASE, "apps", "purchasing", "backend", "app", "graph_status.py"),
    "dataops": os.path.join(SDK_BASE, "apps", "dataops", "backend", "app", "graph_status.py"),
    "s2p": os.path.join(S2P_BASE, "backend", "app", "s2p_graph_status.py"),
}


def section(title):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def find_db(domain):
    for p in SQLITE_PATHS.get(domain, []):
        if os.path.exists(p):
            return p
    return None


def audit_sqlite(domain, db_path):
    """Full audit of one copilot's SQLite DB."""
    print(f"\n  path: {db_path}")
    print(f"  size: {os.path.getsize(db_path) / 1024:.0f} KB")

    conn = sqlite3.connect(db_path)
    try:
        tables = [t[0] for t in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()]
        print(f"  tables: {tables}")

        if "decisions" not in tables:
            print(f"  NO 'decisions' TABLE")
            return {"error": "no decisions table", "tables": tables}

        cols = [c[1] for c in conn.execute("PRAGMA table_info(decisions)").fetchall()]
        print(f"  decisions columns: {cols}")

        total = conn.execute("SELECT count(*) FROM decisions").fetchone()[0]
        print(f"  decisions total: {total}")

        result = {"total": total, "columns": cols, "tables": tables}

        # Status breakdown
        if "status" in cols:
            status_rows = conn.execute(
                "SELECT status, count(*) FROM decisions GROUP BY status ORDER BY count(*) DESC"
            ).fetchall()
            print(f"  by status:")
            for r in status_rows:
                print(f"    {r[0]}: {r[1]}")
            result["by_status"] = {str(r[0]): r[1] for r in status_rows}

            verified = conn.execute(
                "SELECT count(*) FROM decisions WHERE status IN ('confirmed', 'overridden')"
            ).fetchone()[0]
            pending = conn.execute(
                "SELECT count(*) FROM decisions WHERE status = 'pending' OR status IS NULL"
            ).fetchone()[0]
            print(f"  verified (confirmed+overridden): {verified}")
            print(f"  pending/null: {pending}")
            result["verified"] = verified
            result["pending"] = pending
        else:
            print(f"  NO status column — Fix 3a may not be applied")
            # Estimate verified from outcomes table if it exists
            if "outcomes" in tables:
                outcome_count = conn.execute("SELECT count(*) FROM outcomes").fetchone()[0]
                print(f"  (estimating verified from outcomes table: {outcome_count})")
                result["verified"] = outcome_count
                result["verified_source"] = "outcomes_table"
            else:
                result["verified"] = "unknown"

        # Outcomes table
        if "outcomes" in tables:
            outcome_count = conn.execute("SELECT count(*) FROM outcomes").fetchone()[0]
            print(f"  outcomes table: {outcome_count} rows")
            result["outcomes"] = outcome_count
        else:
            print(f"  no outcomes table")

        # Archive table (Fix 3c)
        if "decisions_archive" in tables:
            archive_count = conn.execute("SELECT count(*) FROM decisions_archive").fetchone()[0]
            print(f"  decisions_archive: {archive_count} rows")
            result["archived"] = archive_count
        else:
            print(f"  no decisions_archive table")

        # All other GraphStore tables with counts
        gs_tables = [
            "centroid_checkpoints", "evolution_events", "decision_entity_edges",
            "evidence_receipts", "observations", "fingerprints",
            "conservation_status", "rl_state", "rl_posteriors",
            "dk_weights", "dk_weight_archive",
        ]
        print(f"  GraphStore tables:")
        for t in gs_tables:
            if t in tables:
                try:
                    cnt = conn.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]
                    if cnt > 0:
                        print(f"    {t}: {cnt}")
                except Exception as e:
                    print(f"    {t}: error — {e}")

        # Domain column
        if "domain" in cols:
            dom_rows = conn.execute(
                "SELECT domain, count(*) FROM decisions GROUP BY domain ORDER BY count(*) DESC"
            ).fetchall()
            print(f"  by domain:")
            for r in dom_rows:
                print(f"    {r[0]}: {r[1]}")

        # Sample IDs and format
        samples = conn.execute("SELECT decision_id FROM decisions LIMIT 5").fetchall()
        result["sample_ids"] = [r[0] for r in samples]
        print(f"  sample IDs: {result['sample_ids'][:3]}")

        if samples:
            prefixes = set()
            for s in conn.execute(
                "SELECT DISTINCT substr(decision_id, 1, 4) FROM decisions"
            ).fetchall():
                if s[0]:
                    prefixes.add(s[0])
            if len(prefixes) <= 5:
                print(f"  ID prefixes: {sorted(prefixes)}")
            else:
                print(f"  ID prefixes: {sorted(list(prefixes))[:5]}... ({len(prefixes)} distinct)")

        return result

    finally:
        conn.close()


def check_rule38(domain):
    """Check Rule #38: does main.py construct SQLiteGraphStore directly?"""
    print(f"\n  --- Rule #38 compliance ---")

    main_path = MAIN_PY_PATHS.get(domain)
    if not main_path or not os.path.exists(main_path):
        print(f"    main.py NOT FOUND: {main_path}")
        return

    try:
        with open(main_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        direct_constructions = []
        factory_calls = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # Direct construction (Rule #38 violation)
            if "SQLiteGraphStore(" in stripped:
                direct_constructions.append((i, stripped[:100]))
            # Factory usage (compliant)
            if "create_graph_store(" in stripped:
                factory_calls.append((i, stripped[:100]))

        if direct_constructions:
            print(f"    VIOLATION: {len(direct_constructions)} direct SQLiteGraphStore() calls:")
            for ln, text in direct_constructions:
                print(f"      L{ln}: {text}")
        else:
            print(f"    COMPLIANT: no direct SQLiteGraphStore() calls")

        if factory_calls:
            print(f"    Factory: {len(factory_calls)} create_graph_store() calls:")
            for ln, text in factory_calls:
                print(f"      L{ln}: {text}")

    except Exception as e:
        print(f"    Error: {e}")


def check_graph_gates(domain):
    """Check graph_status.py for AGE hard gates."""
    print(f"\n  --- AGE gates ---")

    gs_path = GRAPH_STATUS_PATHS.get(domain)
    if not gs_path or not os.path.exists(gs_path):
        print(f"    graph_status.py NOT FOUND")
        return

    try:
        with open(gs_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            low = stripped.lower()
            # Look for gate patterns
            if any(kw in low for kw in ["test_only", "test-only", "reject", "block",
                                         "not_permitted", "forbidden", "live_age"]):
                if any(kw in low for kw in ["age", "graph", "backend", "product"]):
                    print(f"    L{i}: {stripped[:100]}")

    except Exception as e:
        print(f"    Error: {e}")


def check_special(domain):
    """Per-copilot specific concerns."""
    print(f"\n  --- Copilot-specific concerns ---")

    if domain == "s2p":
        db_path = find_db("s2p")
        if db_path:
            try:
                conn = sqlite3.connect(db_path)
                tables = [t[0] for t in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()]

                if "decisions_archive" in tables:
                    cnt = conn.execute("SELECT count(*) FROM decisions_archive").fetchone()[0]
                    print(f"    Fix 3c archive: {cnt} rows archived")
                else:
                    print(f"    Fix 3c: NO decisions_archive table")

                cols = [c[1] for c in conn.execute("PRAGMA table_info(decisions)").fetchall()]
                if "status" in cols:
                    pending = conn.execute(
                        "SELECT count(*) FROM decisions WHERE status = 'pending' OR status IS NULL"
                    ).fetchone()[0]
                    total = conn.execute("SELECT count(*) FROM decisions").fetchone()[0]
                    print(f"    total: {total}, pending/ghost: {pending}")
                    if pending > 1000:
                        print(f"    >>> WARNING: {pending} ghosts in S2P")
                        print(f"    >>> Migration would move ghosts to AGE")
                        print(f"    >>> Must archive before migration")
                        ghost_pct = pending / total * 100 if total > 0 else 0
                        print(f"    >>> Ghost percentage: {ghost_pct:.1f}%")
                conn.close()
            except Exception as e:
                print(f"    Error: {e}")

    elif domain == "dataops":
        gq_path = os.path.join(SDK_BASE, "apps", "dataops", "backend", "app", "graph_queries.py")
        if os.path.exists(gq_path):
            try:
                with open(gq_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if "AGEClient" in stripped or "age_client" in stripped:
                        print(f"    Rule #29 violation — graph_queries.py L{i}: {stripped[:100]}")
                    if "intelligence_map" in stripped or "source_profiler" in stripped:
                        print(f"    Graph interaction — L{i}: {stripped[:100]}")
            except Exception as e:
                print(f"    Error: {e}")
        else:
            print(f"    graph_queries.py: NOT FOUND")

    # For all copilots: check if main.py imports/uses RL, evolver, analytics
    main_path = MAIN_PY_PATHS.get(domain)
    if main_path and os.path.exists(main_path):
        try:
            with open(main_path, "r", encoding="utf-8") as f:
                content = f.read()
            features = {
                "RL/reward": ["rl_", "reward_", "exploration_", "RewardLedger"],
                "Evolver": ["evolver", "ScorerEvolution", "EvolutionLedger"],
                "Analytics": ["analytics", "vol_sharpe", "vrp_attribution"],
                "Regime": ["regime_scoring", "RegimeDetector"],
            }
            for feature_name, patterns in features.items():
                for pat in patterns:
                    if pat in content:
                        print(f"    {feature_name}: '{pat}' found in main.py")
                        break
        except Exception as e:
            print(f"    Feature check error: {e}")


def main():
    section("SQLite COPILOT AUDIT — ALL 4 SDK COPILOTS")

    all_stats = {}

    for domain in ["trading", "purchasing", "dataops", "s2p"]:
        section(f"COPILOT: {domain.upper()}")

        db_path = find_db(domain)
        if db_path is None:
            print(f"  SQLite DB NOT FOUND")
            for p in SQLITE_PATHS.get(domain, []):
                print(f"    tried: {p}")
            all_stats[domain] = {"error": "not found"}
            continue

        try:
            stats = audit_sqlite(domain, db_path)
            all_stats[domain] = stats
        except Exception as e:
            print(f"  Audit error: {e}")
            all_stats[domain] = {"error": str(e)}

        try:
            check_rule38(domain)
        except Exception as e:
            print(f"  Rule #38 check error: {e}")

        try:
            check_graph_gates(domain)
        except Exception as e:
            print(f"  Gate check error: {e}")

        try:
            check_special(domain)
        except Exception as e:
            print(f"  Special concern error: {e}")

    # ================================================================
    # SUMMARY TABLE
    # ================================================================
    section("SUMMARY TABLE")

    print(f"\n  {'Copilot':<12} {'Total':>7} {'Verified':>9} {'Pending':>9} {'Archived':>9} {'Outcomes':>9}  {'ID sample'}")
    print(f"  {'-'*12} {'-'*7} {'-'*9} {'-'*9} {'-'*9} {'-'*9}  {'-'*15}")

    for domain in ["trading", "purchasing", "dataops", "s2p"]:
        stats = all_stats.get(domain, {})
        if "error" in stats:
            print(f"  {domain:<12} {'ERROR':>7}  {stats.get('error', '')}")
            continue

        total = stats.get("total", "?")
        verified = stats.get("verified", "?")
        pending = stats.get("pending", "-")
        archived = stats.get("archived", "-")
        outcomes = stats.get("outcomes", "-")
        sample = str(stats.get("sample_ids", ["?"])[0])
        prefix = sample[:13] + ".." if len(sample) > 13 else sample

        print(f"  {domain:<12} {str(total):>7} {str(verified):>9} {str(pending):>9} {str(archived):>9} {str(outcomes):>9}  {prefix}")

    # ================================================================
    # MIGRATION READINESS + V BASELINES
    # ================================================================
    section("MIGRATION READINESS")

    for domain in ["trading", "purchasing", "dataops", "s2p"]:
        stats = all_stats.get(domain, {})
        print(f"\n  {domain.upper()}:")

        if "error" in stats:
            print(f"    NOT READY — {stats['error']}")
            continue

        issues = []

        pending = stats.get("pending", 0)
        if isinstance(pending, int) and pending > 100:
            issues.append(f"{pending} pending/ghost decisions — must archive before migration")

        if "status" not in stats.get("columns", []):
            issues.append("no status column — Fix 3a not applied")

        verified = stats.get("verified", 0)
        if verified == 0 or verified == "unknown":
            issues.append(f"verified={verified} — check if copilot has live data")

        if issues:
            for issue in issues:
                print(f"    ISSUE: {issue}")
        else:
            total = stats.get("total", 0)
            print(f"    READY — {total} total, {verified} verified")

        # V baseline
        if isinstance(verified, int) and verified > 0:
            print(f"    V_{domain} regression baseline: {verified}")

    # ================================================================
    # RECOMMENDED MIGRATION ORDER
    # ================================================================
    section("RECOMMENDED MIGRATION ORDER")

    ready_copilots = []
    for domain in ["trading", "purchasing", "dataops", "s2p"]:
        stats = all_stats.get(domain, {})
        total = stats.get("total", 0)
        verified = stats.get("verified", 0)
        pending = stats.get("pending", 0)
        if isinstance(total, int) and isinstance(verified, int):
            ready_copilots.append((domain, total, verified, pending))

    # Sort by total ascending (smallest first = fastest feedback)
    ready_copilots.sort(key=lambda x: x[1])

    print("\n  By dataset size (smallest first = fastest pattern proof):\n")
    for i, (domain, total, verified, pending) in enumerate(ready_copilots, 1):
        ghost_note = f" *** {pending} ghosts — ARCHIVE FIRST ***" if isinstance(pending, int) and pending > 1000 else ""
        print(f"    {i}. {domain}: {total} total, {verified} verified{ghost_note}")

    print()


if __name__ == "__main__":
    main()
