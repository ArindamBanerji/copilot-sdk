#!/usr/bin/env python3
"""Validate AGE graph seed data for all 5 copilots.

Usage:
    python validate_graph_seed_v1.py
    python validate_graph_seed_v1.py --dsn "host=... port=5433 ..."
    python validate_graph_seed_v1.py --check-endpoints
    python validate_graph_seed_v1.py --copilot DataOps --check-endpoints

Env vars:
    GRAPH_DSN          - PostgreSQL+AGE connection string
    AGE_GRAPH_NAME     - Graph name (default: soc_graph)

Note: Node counts are GLOBAL across all domains in the graph.
      Alert nodes are shared between SOC and DataOps — the validator
      checks total count only. A copilot's endpoint may still return
      empty if it filters by domain. Use --check-endpoints to catch that.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from typing import Any

# ── Graph node requirements per copilot ──────────────────────────────
#
# "min"      = minimum node count expected after seed
# "critical" = True → FAIL (blocks E2E), False → WARN (cosmetic)
# "note"     = context for debugging
#
# Counts are checked against the GLOBAL graph census. Nodes shared
# across copilots (Decision, Alert, etc.) are counted once.

COPILOT_REQUIREMENTS: dict[str, dict[str, Any]] = {
    "SOC": {
        "port": {"backend": 8001, "frontend": 5173},
        "nodes": {
            "Decision":            {"min": 100, "critical": True},
            "Outcome":             {"min": 10,  "critical": True},
            "Alert":               {"min": 50,  "critical": True},
            "CentroidCheckpoint":  {"min": 1,   "critical": True},
            "ConservationStatus":  {"min": 1,   "critical": False},
            "Fingerprint":         {"min": 1,   "critical": True},
            "EvidenceReceipt":     {"min": 1,   "critical": False},
            "Domain":              {"min": 1,   "critical": False},
            "User":                {"min": 1,   "critical": False},
            "Asset":               {"min": 1,   "critical": False},
            "Campaign":            {"min": 1,   "critical": False},
        },
        "endpoints": {
            "/api/health":              {"field": "ready", "expect": True},
            "/api/conservation/status": {"field": "conservation_phase", "expect_exists": True},
        },
    },
    "S2P": {
        "port": {"backend": 8002, "frontend": 5177},
        "nodes": {
            "Decision":            {"min": 10,  "critical": True},
            "Outcome":             {"min": 1,   "critical": True},
            "Invoice":             {"min": 24,  "critical": True,  "note": "Queue needs >=24 for E2E"},
            "Supplier":            {"min": 5,   "critical": True},
            "PurchaseOrder":       {"min": 10,  "critical": False},
            "GoodsReceipt":        {"min": 10,  "critical": False},
            "Contract":            {"min": 1,   "critical": False},
            "Commodity":           {"min": 1,   "critical": False},
            "ProcessModel":        {"min": 1,   "critical": False, "note": "D-CEL process data"},
            "Activity":            {"min": 1,   "critical": False, "note": "Bottleneck panel"},
            "CentroidCheckpoint":  {"min": 1,   "critical": True},
            "Fingerprint":         {"min": 1,   "critical": True},
        },
        "endpoints": {
            "/api/health":               {"field": "ready", "expect": True},
            "/api/s2p/preview/queue":     {"field": "total", "expect_gt": 0, "note": "Invoice queue must be non-empty"},
            "/api/conservation/status":   {"field": "conservation_phase", "expect_exists": True},
        },
    },
    "Trading": {
        "port": {"backend": 8010, "frontend": 5174},
        "nodes": {
            "Decision":            {"min": 10,  "critical": True},
            "Outcome":             {"min": 1,   "critical": True},
            "CentroidCheckpoint":  {"min": 1,   "critical": True},
            "Fingerprint":         {"min": 1,   "critical": True},
            "ConservationStatus":  {"min": 1,   "critical": False},
        },
        "endpoints": {
            "/api/health":              {"field": "ready", "expect": True},
            "/api/conservation/status":  {"field": "conservation_phase", "expect_exists": True},
        },
    },
    "Purchasing": {
        "port": {"backend": 8020, "frontend": 5175},
        "nodes": {
            "Decision":            {"min": 10,  "critical": True},
            "Outcome":             {"min": 1,   "critical": True},
            "CentroidCheckpoint":  {"min": 1,   "critical": True},
            "Fingerprint":         {"min": 1,   "critical": True},
            "ConservationStatus":  {"min": 1,   "critical": False},
        },
        "endpoints": {
            "/api/health":              {"field": "ready", "expect": True},
            "/api/conservation/status":  {"field": "conservation_phase", "expect_exists": True},
        },
    },
    "DataOps": {
        "port": {"backend": 8030, "frontend": 5176},
        "nodes": {
            "Decision":            {"min": 10,  "critical": True},
            "Outcome":             {"min": 1,   "critical": True},
            "Alert":               {"min": 20,  "critical": True,  "note": "alert-groups needs these (global count; endpoint check catches domain filtering)"},
            "CentroidCheckpoint":  {"min": 1,   "critical": True},
            "Fingerprint":         {"min": 1,   "critical": True},
            "ConservationStatus":  {"min": 1,   "critical": False},
        },
        "endpoints": {
            "/api/health":                  {"field": "ready", "expect": True},
            "/api/context/alert-groups":     {"field_any": ["groups", "alert_groups"], "expect_nonempty": True, "note": "DataOps PW failures if empty"},
            "/api/context/pipelines":        {"expect_nonempty": True, "note": "Pipeline grid"},
            "/api/conservation/status":      {"field": "conservation_phase", "expect_exists": True},
        },
    },
}

# ── Graph query ──────────────────────────────────────────────────────

def get_graph_census(dsn: str, graph_name: str) -> dict[str, int]:
    """Query AGE for node label counts."""
    try:
        import psycopg2
    except ImportError:
        print("ERROR: psycopg2 not installed. pip install psycopg2-binary")
        sys.exit(1)

    try:
        conn = psycopg2.connect(dsn)
    except Exception as exc:
        print(f"ERROR: Cannot connect to AGE database.")
        print(f"  DSN: {dsn[:40]}...")
        print(f"  Error: {exc}")
        print(f"  Is WSL2/PostgreSQL running? Check: wsl -e pg_isready -h localhost -p 5433")
        sys.exit(1)

    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SET search_path = ag_catalog, public;")

    query = (
        f"SELECT * FROM cypher('{graph_name}', "
        "$q$ MATCH (n) RETURN labels(n)[0] AS label, count(*) AS cnt "
        "ORDER BY cnt DESC $q$) AS (label agtype, cnt agtype);"
    )
    try:
        cur.execute(query)
    except Exception as exc:
        print(f"ERROR: Cypher query failed on graph '{graph_name}'.")
        print(f"  Error: {exc}")
        print(f"  Does the graph exist? Check: SELECT * FROM ag_catalog.ag_graph;")
        cur.close()
        conn.close()
        sys.exit(1)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    census: dict[str, int] = {}
    for label_raw, cnt_raw in rows:
        label = str(label_raw).strip('"')
        cnt = int(str(cnt_raw))
        census[label] = cnt
    return census


# ── Endpoint checks ─────────────────────────────────────────────────

def check_endpoint(base_url: str, path: str, spec: dict[str, Any]) -> tuple[bool, str]:
    """Check a single endpoint. Returns (passed, message)."""
    url = f"{base_url}{path}"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return False, f"Connection refused (backend down?): {e.reason}"
    except Exception as e:
        return False, f"Error: {e}"

    # Check field == expected value
    if "field" in spec and "expect" in spec:
        val = data.get(spec["field"])
        if val != spec["expect"]:
            return False, f"{spec['field']}={val} (expected {spec['expect']})"

    # Check field exists
    if "field" in spec and "expect_exists" in spec:
        if spec["field"] not in data:
            return False, f"missing field '{spec['field']}'"

    # Check field > threshold
    if "field" in spec and "expect_gt" in spec:
        val = data.get(spec["field"], 0)
        threshold = spec["expect_gt"]
        if not isinstance(val, (int, float)) or val <= threshold:
            return False, f"{spec['field']}={val} (expected > {threshold})"

    # Check any of multiple field names for non-empty
    if "field_any" in spec and "expect_nonempty" in spec:
        found = False
        for fname in spec["field_any"]:
            val = data.get(fname)
            if isinstance(val, (list, dict)) and len(val) > 0:
                found = True
                break
        if not found:
            return False, f"none of {spec['field_any']} has data"

    # Check response itself is non-empty list/dict
    if "expect_nonempty" in spec and "field_any" not in spec and "field" not in spec:
        if isinstance(data, list) and len(data) == 0:
            return False, "empty list"
        if isinstance(data, dict) and len(data) == 0:
            return False, "empty dict"

    return True, "OK"


# ── Main ─────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate AGE graph seed data for all 5 copilots",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python validate_graph_seed_v1.py                        # graph-only check
  python validate_graph_seed_v1.py --check-endpoints      # graph + API smoke
  python validate_graph_seed_v1.py --copilot DataOps      # single copilot
  python validate_graph_seed_v1.py --json                  # machine-readable""",
    )
    parser.add_argument("--dsn", default=os.environ.get("GRAPH_DSN", ""),
                        help="PostgreSQL+AGE DSN (default: $GRAPH_DSN)")
    parser.add_argument("--graph", default=os.environ.get("AGE_GRAPH_NAME", "soc_graph"),
                        help="AGE graph name (default: soc_graph)")
    parser.add_argument("--check-endpoints", action="store_true",
                        help="Also check backend HTTP endpoints (backends must be running)")
    parser.add_argument("--copilot", choices=["SOC", "S2P", "Trading", "Purchasing", "DataOps"],
                        help="Check only one copilot")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not args.dsn:
        print("ERROR: No DSN. Set GRAPH_DSN env var or pass --dsn \"host=... port=5433 ...\"")
        sys.exit(1)

    # ── Census ───────────────────────────────────────────────────────
    print(f"Connecting to graph '{args.graph}'...")
    census = get_graph_census(args.dsn, args.graph)
    total_nodes = sum(census.values())
    print(f"  {total_nodes} total nodes across {len(census)} labels")

    # Print full census
    print(f"\n  {'Label':<30} {'Count':>8}")
    print(f"  {'-'*30} {'-'*8}")
    for label, cnt in sorted(census.items(), key=lambda x: -x[1]):
        print(f"  {label:<30} {cnt:>8}")
    print()

    copilots = (
        {args.copilot: COPILOT_REQUIREMENTS[args.copilot]}
        if args.copilot
        else COPILOT_REQUIREMENTS
    )
    results: dict[str, dict[str, Any]] = {}
    all_pass = True

    for name, spec in copilots.items():
        print(f"{'='*60}")
        print(f"  {name} (backend :{spec['port']['backend']}, frontend :{spec['port']['frontend']})")
        print(f"{'='*60}")

        node_results: list[dict[str, Any]] = []
        copilot_pass = True

        # ── Node checks ─────────────────────────────────────────────
        print(f"\n  {'Node Label':<25} {'Actual':>8} {'/ Min':<8} {'Status'}")
        print(f"  {'-'*25} {'-'*8} {'-'*8} {'-'*6}")
        for label, req in spec["nodes"].items():
            actual = census.get(label, 0)
            needed = req["min"]
            ok = actual >= needed
            critical = req.get("critical", False)
            note = req.get("note", "")

            status = "PASS" if ok else ("FAIL" if critical else "WARN")

            if not ok and critical:
                copilot_pass = False
                all_pass = False

            entry = {"label": label, "actual": actual, "min": needed, "status": status}
            if note:
                entry["note"] = note
            node_results.append(entry)

            marker = "  " if ok else ("!!" if critical else "? ")
            note_str = f"  # {note}" if note and not ok else ""
            print(f"  {marker} {label:<25} {actual:>6} / {needed:<6} {status}{note_str}")

        # ── Endpoint checks ──────────────────────────────────────────
        endpoint_results: list[dict[str, Any]] = []
        if args.check_endpoints:
            base = f"http://127.0.0.1:{spec['port']['backend']}"
            print(f"\n  {'Endpoint':<40} {'Result'}")
            print(f"  {'-'*40} {'-'*20}")
            for path, espec in spec["endpoints"].items():
                ok, msg = check_endpoint(base, path, espec)
                note = espec.get("note", "")
                if not ok:
                    copilot_pass = False
                    all_pass = False

                entry = {"path": path, "status": "PASS" if ok else "FAIL", "message": msg}
                if note:
                    entry["note"] = note
                endpoint_results.append(entry)

                marker = "  " if ok else "!!"
                note_str = f"  # {note}" if note and not ok else ""
                print(f"  {marker} {path:<40} {msg}{note_str}")

        verdict = "PASS" if copilot_pass else "FAIL"
        print(f"\n  >>> {name}: {verdict}\n")

        results[name] = {
            "verdict": verdict,
            "nodes": node_results,
            "endpoints": endpoint_results,
        }

    # ── Summary ──────────────────────────────────────────────────────
    print(f"{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    for name, res in results.items():
        marker = "  " if res["verdict"] == "PASS" else "!!"
        fails = [n for n in res["nodes"] if n["status"] == "FAIL"]
        warns = [n for n in res["nodes"] if n["status"] == "WARN"]
        efails = [e for e in res.get("endpoints", []) if e["status"] == "FAIL"]
        suffix = ""
        if fails:
            suffix = f"  MISSING: {', '.join(n['label'] for n in fails)}"
        if efails:
            suffix += f"  ENDPOINT: {', '.join(e['path'] for e in efails)}"
        if warns and not fails:
            suffix = f"  LOW: {', '.join(n['label'] for n in warns)}"
        print(f"  {marker} {name:<15} {res['verdict']}{suffix}")

    print(f"\n  Graph: {total_nodes} nodes, {len(census)} labels")
    overall = "ALL PASS" if all_pass else "FAILURES DETECTED"
    print(f"  Overall: {overall}")
    print()

    if args.json:
        out = {"census": census, "results": results, "overall": overall}
        print(json.dumps(out, indent=2))

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
