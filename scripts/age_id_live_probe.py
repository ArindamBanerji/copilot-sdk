#!/usr/bin/env python3
"""
AGE id() Live Probe — Resolve pagination release gate.

Usage:
    python age_id_live_probe.py
    python age_id_live_probe.py --host localhost --port 5433 --db soc_db --graph soc_graph

Defaults: localhost:5433, postgres/postgres, soc_db, soc_graph
"""

import argparse
import socket
import subprocess
import sys

try:
    import psycopg2
except ImportError:
    print("psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)


def ensure_age_running(host: str, port: int):
    """Check if PostgreSQL+AGE is reachable. If not, try to start it via WSL2."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    result = sock.connect_ex((host, port))
    sock.close()
    if result == 0:
        print(f"  ✓ PostgreSQL+AGE reachable on {host}:{port}")
        return

    print(f"  ✗ PostgreSQL+AGE NOT reachable on {host}:{port}")
    print(f"  Attempting to start via WSL2...")
    try:
        subprocess.run(
            ["wsl", "-d", "Ubuntu", "--", "sudo", "service", "postgresql", "start"],
            timeout=15, check=False
        )
        # Wait a moment then re-check
        import time
        time.sleep(3)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            print(f"  ✓ PostgreSQL+AGE started successfully on {host}:{port}")
            return
    except FileNotFoundError:
        pass  # wsl not available (running on Linux directly, etc.)
    except Exception:
        pass

    print(f"\n  Could not auto-start PostgreSQL+AGE. Start it manually:")
    print(f"    Option 1 (PowerShell): wsl -d Ubuntu -- sudo service postgresql start")
    print(f"    Option 2 (WSL shell):  sudo service postgresql start")
    print(f"  Then re-run this script.")
    sys.exit(1)


def run_probe(cur, graph: str, label: str, query: str, columns: list[str]) -> list[dict] | str:
    """Run a single Cypher probe via AGE. Returns rows or error string."""
    col_defs = ", ".join(f"{c} agtype" for c in columns)
    sql = f"SELECT * FROM cypher('{graph}', $$ {query} $$) AS ({col_defs})"
    try:
        cur.execute(sql)
        rows = cur.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        return f"ERROR: {e}"


def print_result(label: str, result, verdict_fn=None):
    """Print probe result with pass/fail verdict."""
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    if isinstance(result, str):
        print(f"  {result}")
        print(f"  VERDICT: FAIL")
        return False
    if not result:
        print(f"  No rows returned")
        print(f"  VERDICT: FAIL (empty result)")
        return False
    for i, row in enumerate(result[:10]):
        print(f"  [{i}] {row}")
    if len(result) > 10:
        print(f"  ... ({len(result)} total rows)")
    if verdict_fn:
        passed, msg = verdict_fn(result)
        print(f"  VERDICT: {'PASS' if passed else 'FAIL'} — {msg}")
        return passed
    print(f"  VERDICT: PASS — {len(result)} rows returned")
    return True


def main():
    parser = argparse.ArgumentParser(description="AGE id() live probe")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5433)
    parser.add_argument("--db", default="soc_db")
    parser.add_argument("--user", default="postgres")
    parser.add_argument("--password", default="postgres")
    parser.add_argument("--graph", default="soc_graph")
    args = parser.parse_args()

    # Pre-flight: make sure PostgreSQL+AGE is running
    print(f"\nPre-flight check: PostgreSQL+AGE on {args.host}:{args.port}")
    ensure_age_running(args.host, args.port)

    print(f"\nConnecting to {args.host}:{args.port}/{args.db} graph={args.graph}")
    try:
        conn = psycopg2.connect(
            host=args.host, port=args.port, dbname=args.db,
            user=args.user, password=args.password
        )
        conn.autocommit = True
        cur = conn.cursor()
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

    # Load AGE
    try:
        cur.execute("LOAD 'age'")
        cur.execute("SET search_path = ag_catalog, \"$user\", public")
    except Exception as e:
        print(f"Failed to load AGE extension: {e}")
        sys.exit(1)

    results = {}
    g = args.graph

    # ── PROBE 1: Node id() availability ──
    r1 = run_probe(cur, g, "P1",
        "MATCH (n:Decision) RETURN n.decision_id, id(n) ORDER BY id(n) LIMIT 5",
        ["decision_id", "node_id"])
    results["P1"] = print_result("PROBE 1: Node id() availability", r1)

    if not results["P1"]:
        print("\n" + "!"*60)
        print("  id() NOT AVAILABLE. Release gate UNRESOLVED.")
        print("  Fallback: best-effort property ordering.")
        print("!"*60)
        conn.close()
        sys.exit(1)

    # ── PROBE 2: Relationship id() ──
    r2 = run_probe(cur, g, "P2",
        "MATCH (a)-[r]->(b) RETURN type(r), id(r), id(a), id(b) ORDER BY id(r) LIMIT 5",
        ["rel_type", "rel_id", "src_id", "dst_id"])
    results["P2"] = print_result("PROBE 2: Relationship id() availability", r2)

    # ── PROBE 3: SKIP + ORDER BY id() ──
    r3 = run_probe(cur, g, "P3",
        "MATCH (n:Decision) RETURN n.decision_id, id(n) ORDER BY id(n) SKIP 5 LIMIT 5",
        ["decision_id", "node_id"])

    def check_skip(rows):
        if isinstance(r1, str) or isinstance(rows, str):
            return False, "prior probe failed"
        ids_p1 = {str(r["node_id"]) for r in r1}
        ids_p3 = {str(r["node_id"]) for r in rows}
        overlap = ids_p1 & ids_p3
        if not overlap:
            return True, f"SKIP worked — 0 overlap between page 1 and page 2"
        return False, f"SKIP broken — {len(overlap)} overlapping IDs"

    results["P3"] = print_result("PROBE 3: SKIP + ORDER BY id()", r3, check_skip)

    # ── PROBE 4: Stability (same query twice) ──
    r4a = run_probe(cur, g, "P4A",
        "MATCH (n:Decision) RETURN n.decision_id, id(n) ORDER BY id(n) LIMIT 10",
        ["decision_id", "node_id"])
    r4b = run_probe(cur, g, "P4B",
        "MATCH (n:Decision) RETURN n.decision_id, id(n) ORDER BY id(n) LIMIT 10",
        ["decision_id", "node_id"])

    def check_stability(_):
        if isinstance(r4a, str) or isinstance(r4b, str):
            return False, "query failed"
        if len(r4a) != len(r4b):
            return False, f"different row counts: {len(r4a)} vs {len(r4b)}"
        for i, (a, b) in enumerate(zip(r4a, r4b)):
            if str(a) != str(b):
                return False, f"row {i} differs: {a} vs {b}"
        return True, f"identical ordering across 2 runs ({len(r4a)} rows)"

    results["P4"] = print_result("PROBE 4: Ordering stability (2 runs)", r4a, check_stability)

    # ── PROBE 5: decision_movement edge id(r) ──
    r5 = run_probe(cur, g, "P5",
        "MATCH (d:Decision)-[r]->(e) RETURN d.decision_id, type(r), id(r), id(d), id(e) ORDER BY id(r) LIMIT 10",
        ["decision_id", "rel_type", "rel_id", "src_id", "dst_id"])

    def check_edge_unique(rows):
        ids = [str(r["rel_id"]) for r in rows]
        if len(ids) == len(set(ids)):
            return True, f"all {len(ids)} edge IDs unique"
        return False, f"duplicate edge IDs found"

    results["P5"] = print_result("PROBE 5: Edge id(r) uniqueness for movement", r5, check_edge_unique)

    # ── PROBE 6: Path component ID extraction ──
    r6 = run_probe(cur, g, "P6",
        """MATCH p=(a)-[*1..2]-(b)
        WITH p, nodes(p) AS ns, relationships(p) AS rs
        RETURN [n IN ns | id(n)], [r IN rs | id(r)], length(p)
        ORDER BY [n IN ns | id(n)]
        LIMIT 5""",
        ["node_ids", "rel_ids", "path_length"])
    results["P6"] = print_result("PROBE 6: Path component id() extraction", r6)

    # ── PROBE 7: Node id() global uniqueness ──
    r7 = run_probe(cur, g, "P7",
        """MATCH (n:Decision)
        WITH count(n) AS total, count(DISTINCT id(n)) AS distinct_ids
        RETURN total, distinct_ids, total = distinct_ids AS all_unique""",
        ["total", "distinct_ids", "all_unique"])

    def check_unique_nodes(rows):
        row = rows[0]
        if "true" in str(row.get("all_unique", "")).lower():
            return True, f"{row['distinct_ids']} distinct out of {row['total']} — all unique"
        return False, f"{row['distinct_ids']} distinct out of {row['total']} — DUPLICATES"

    results["P7"] = print_result("PROBE 7: Node id() global uniqueness", r7, check_unique_nodes)

    # ── PROBE 8: Edge id() global uniqueness ──
    r8 = run_probe(cur, g, "P8",
        """MATCH ()-[r]->()
        WITH count(r) AS total, count(DISTINCT id(r)) AS distinct_ids
        RETURN total, distinct_ids, total = distinct_ids AS all_unique""",
        ["total", "distinct_ids", "all_unique"])

    def check_unique_edges(rows):
        row = rows[0]
        if "true" in str(row.get("all_unique", "")).lower():
            return True, f"{row['distinct_ids']} distinct out of {row['total']} — all unique"
        return False, f"{row['distinct_ids']} distinct out of {row['total']} — DUPLICATES"

    results["P8"] = print_result("PROBE 8: Edge id() global uniqueness", r8, check_unique_edges)

    # ── SUMMARY ──
    conn.close()
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    for k, v in results.items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")

    all_pass = all(results.values())
    core_pass = all(results.get(k, False) for k in ["P1", "P2", "P3", "P4", "P5", "P7", "P8"])
    p6_pass = results.get("P6", False)

    print()
    if all_pass:
        print("  ALL 8 PASS → Release gate RESOLVED.")
        print("  id() is the tiebreaker for all pagination queries.")
        print("  decision_movement: ORDER BY id(r)")
        print("  Path traversals: ORDER BY path component IDs")
    elif core_pass and not p6_pass:
        print("  CORE PASS, P6 FAIL → Release gate PARTIALLY RESOLVED.")
        print("  decision_movement: ORDER BY id(r) in Cypher ✓")
        print("  Path traversals: Python-side sort using _age_id ✓")
    else:
        failed = [k for k, v in results.items() if not v]
        print(f"  FAILED: {', '.join(failed)}")
        print("  Release gate UNRESOLVED. Fallback to best-effort ordering.")


if __name__ == "__main__":
    main()
