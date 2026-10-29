#!/usr/bin/env python3
"""Validate AGE graph seed data for all 5 copilots.

v3 changes (from v2):
  - Added ShadowDecision (min 1000, critical) to SOC nodes
  - Added AttackPattern (min 7, critical) to SOC nodes
  - Added edge-type checking: get_edge_census() + per-copilot edges dict
  - SOC edges: CLASSIFIED_AS (min 100, critical) — Alert->AttackPattern
  - Edge census printed alongside node census
  - Edge failures included in summary + JSON output

v2 changes (from v1):
  - Fixed conservation endpoint field: 'status' (not 'conservation_phase')
  - Added domain property validation for DataQualityAlert and PipelineSystem
  - Added --check-domains flag for deep domain property audit

Usage:
    python validate_graph_seed_v3.py
    python validate_graph_seed_v3.py --dsn "host=... port=5433 ..."
    python validate_graph_seed_v3.py --check-endpoints
    python validate_graph_seed_v3.py --check-domains
    python validate_graph_seed_v3.py --copilot SOC --check-endpoints
    python validate_graph_seed_v3.py --json

Env vars:
    GRAPH_DSN          - PostgreSQL+AGE connection string
    AGE_GRAPH_NAME     - Graph name (default: soc_graph)

Note: Node counts are GLOBAL across all domains in the graph.
      Alert nodes are shared between SOC and DataOps — the validator
      checks total count only. Use --check-domains to catch nodes
      missing the domain property (which makes them invisible to
      copilots that filter by domain). Use --check-endpoints for
      live API smoke tests.
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
            "ShadowDecision":      {"min": 1000, "critical": True, "note": "f9 analyst-benchmarking needs >=1500 with source=v_shadow_synthetic_v3"},
            "AttackPattern":       {"min": 7,    "critical": True, "note": "attack-tactic-breakdown needs tactic property"},
        },
        "edges": {
            "CLASSIFIED_AS":       {"min": 100,  "critical": True, "note": "Alert->AttackPattern for attack-tactic-breakdown"},
        },
        "endpoints": {
            "/api/health":              {"field": "ready", "expect": True},
            "/api/conservation/status": {"field": "status", "expect_exists": True},
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
            "/api/conservation/status":   {"field": "status", "expect_exists": True},
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
            "/api/conservation/status":  {"field": "status", "expect_exists": True},
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
            "/api/conservation/status":  {"field": "status", "expect_exists": True},
        },
    },
    "DataOps": {
        "port": {"backend": 8030, "frontend": 5176},
        "nodes": {
            "Decision":            {"min": 10,  "critical": True},
            "Outcome":             {"min": 1,   "critical": True},
            "Alert":               {"min": 20,  "critical": True,  "note": "alert-groups needs these (global count; --check-domains catches domain filtering)"},
            "DataQualityAlert":    {"min": 20,  "critical": True,  "note": "Seeded by seed_dataops_graph.py; must have domain='dataops'"},
            "PipelineSystem":      {"min": 9,   "critical": True,  "note": "Pipeline grid; must have domain='dataops'"},
            "CentroidCheckpoint":  {"min": 1,   "critical": True},
            "Fingerprint":         {"min": 1,   "critical": True},
            "ConservationStatus":  {"min": 1,   "critical": False},
        },
        "endpoints": {
            "/api/health":                  {"field": "ready", "expect": True},
            "/api/context/alert-groups":     {"field_any": ["groups", "alert_groups"], "expect_nonempty": True, "note": "DataOps PW failures if empty"},
            "/api/context/pipelines":        {"expect_nonempty": True, "note": "Pipeline grid"},
            "/api/conservation/status":      {"field": "status", "expect_exists": True},
        },
    },
}

# ── Domain property requirements ─────────────────────────────────────
# Nodes that MUST have a domain property for their copilot's graph
# queries to find them. Without this property, the node exists but
# is invisible to the copilot (the root cause of DataOps PW mass fail).

DOMAIN_REQUIREMENTS: dict[str, list[dict[str, Any]]] = {
    "DataOps": [
        {
            "label": "DataQualityAlert",
            "domain": "dataops",
            "critical": True,
            "note": "DataOpsGraphClient.get_alerts() filters WHERE alert.domain = 'dataops'",
        },
        {
            "label": "PipelineSystem",
            "domain": "dataops",
            "critical": True,
            "note": "DataOpsGraphClient.get_pipelines() filters WHERE system.domain = 'dataops'",
        },
    ],
    # SOC Alert nodes *may* also need domain='soc' — checking for awareness
    "SOC": [
        {
            "label": "Alert",
            "domain": "soc",
            "critical": False,  # SOC tests pass without it today
            "note": "540+ Alert nodes lack domain; SOC may not filter by it yet",
        },
    ],
}

# ── Graph queries ────────────────────────────────────────────────────

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


def get_edge_census(dsn: str, graph_name: str) -> dict[str, int]:
    """Query AGE for edge label counts."""
    try:
        import psycopg2
    except ImportError:
        print("ERROR: psycopg2 not installed. pip install psycopg2-binary")
        sys.exit(1)

    try:
        conn = psycopg2.connect(dsn)
    except Exception as exc:
        print(f"ERROR: Cannot connect to AGE database: {exc}")
        sys.exit(1)

    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SET search_path = ag_catalog, public;")

    query = (
        f"SELECT * FROM cypher('{graph_name}', "
        "$q$ MATCH ()-[r]->() RETURN type(r) AS label, count(*) AS cnt "
        "ORDER BY cnt DESC $q$) AS (label agtype, cnt agtype);"
    )
    try:
        cur.execute(query)
    except Exception as exc:
        print(f"ERROR: Edge census query failed: {exc}")
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


def check_domain_properties(dsn: str, graph_name: str) -> dict[str, dict[str, Any]]:
    """Check which nodes have/lack the domain property.

    Returns a dict keyed by "Label:domain_value" with counts.
    """
    try:
        import psycopg2
    except ImportError:
        print("ERROR: psycopg2 not installed. pip install psycopg2-binary")
        sys.exit(1)

    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SET search_path = ag_catalog, public;")

    results: dict[str, dict[str, Any]] = {}

    # Check each label that requires domain property
    all_labels: set[str] = set()
    for reqs in DOMAIN_REQUIREMENTS.values():
        for req in reqs:
            all_labels.add(req["label"])

    for label in sorted(all_labels):
        # Count nodes WITH correct domain
        for domain_val in ["dataops", "soc", None]:
            if domain_val is None:
                # Count nodes with NO domain property
                q = (
                    f"SELECT * FROM cypher('{graph_name}', "
                    f"$q$ MATCH (n:{label}) WHERE n.domain IS NULL "
                    f"RETURN count(n) $q$) AS (cnt agtype);"
                )
                key = f"{label}:NULL"
            else:
                q = (
                    f"SELECT * FROM cypher('{graph_name}', "
                    f"$q$ MATCH (n:{label}) WHERE n.domain = '{domain_val}' "
                    f"RETURN count(n) $q$) AS (cnt agtype);"
                )
                key = f"{label}:{domain_val}"

            try:
                cur.execute(q)
                row = cur.fetchone()
                cnt = int(str(row[0])) if row else 0
                results[key] = {"count": cnt, "label": label, "domain": domain_val}
            except Exception:
                results[key] = {"count": -1, "label": label, "domain": domain_val, "error": True}

    cur.close()
    conn.close()
    return results


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
            # Try common alternatives for conservation
            alt_fields = {"status": ["conservation_phase", "phase"],
                          "conservation_phase": ["status", "phase"]}
            alts = alt_fields.get(spec["field"], [])
            found_alt = None
            for alt in alts:
                if alt in data:
                    found_alt = alt
                    break
            if found_alt:
                return False, f"missing field '{spec['field']}' (found '{found_alt}' instead — wrong field name?)"
            return False, f"missing field '{spec['field']}' (keys: {list(data.keys())[:5]})"

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
        description="Validate AGE graph seed data for all 5 copilots (v3)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python validate_graph_seed_v3.py                                    # graph-only
  python validate_graph_seed_v3.py --check-endpoints                  # graph + API
  python validate_graph_seed_v3.py --check-domains                    # graph + domain audit
  python validate_graph_seed_v3.py --check-endpoints --check-domains  # full check
  python validate_graph_seed_v3.py --copilot SOC                      # single copilot
  python validate_graph_seed_v3.py --json                             # machine-readable""",
    )
    parser.add_argument("--dsn", default=os.environ.get("GRAPH_DSN", ""),
                        help="PostgreSQL+AGE DSN (default: $GRAPH_DSN)")
    parser.add_argument("--graph", default=os.environ.get("AGE_GRAPH_NAME", "soc_graph"),
                        help="AGE graph name (default: soc_graph)")
    parser.add_argument("--check-endpoints", action="store_true",
                        help="Also check backend HTTP endpoints (backends must be running)")
    parser.add_argument("--check-domains", action="store_true",
                        help="Check domain property on nodes that require it (DataQualityAlert, PipelineSystem, Alert)")
    parser.add_argument("--copilot", choices=["SOC", "S2P", "Trading", "Purchasing", "DataOps"],
                        help="Check only one copilot")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not args.dsn:
        print("ERROR: No DSN. Set GRAPH_DSN env var or pass --dsn \"host=... port=5433 ...\"")
        sys.exit(1)

    # ── Node census ─────────────────────────────────────────────────
    print(f"Connecting to graph '{args.graph}'...")
    census = get_graph_census(args.dsn, args.graph)
    total_nodes = sum(census.values())
    print(f"  {total_nodes} total nodes across {len(census)} labels")

    # Print full node census
    print(f"\n  {'Label':<30} {'Count':>8}")
    print(f"  {'-'*30} {'-'*8}")
    for label, cnt in sorted(census.items(), key=lambda x: -x[1]):
        print(f"  {label:<30} {cnt:>8}")
    print()

    # ── Edge census (v3 addition) ───────────────────────────────────
    edge_census = get_edge_census(args.dsn, args.graph)
    total_edges = sum(edge_census.values())
    print(f"  {total_edges} total edges across {len(edge_census)} labels")

    print(f"\n  {'Edge Label':<30} {'Count':>8}")
    print(f"  {'-'*30} {'-'*8}")
    for label, cnt in sorted(edge_census.items(), key=lambda x: -x[1]):
        print(f"  {label:<30} {cnt:>8}")
    print()

    # ── Domain audit (v2 addition) ───────────────────────────────────
    domain_results: dict[str, dict[str, Any]] = {}
    domain_pass = True
    if args.check_domains:
        print(f"{'='*60}")
        print(f"  DOMAIN PROPERTY AUDIT")
        print(f"{'='*60}")

        domain_data = check_domain_properties(args.dsn, args.graph)

        print(f"\n  {'Label:Domain':<35} {'Count':>8}  {'Status'}")
        print(f"  {'-'*35} {'-'*8}  {'-'*6}")

        for key, info in sorted(domain_data.items()):
            cnt = info["count"]
            label = info["label"]
            domain = info["domain"]

            # Check if this is a problem
            status = "OK"
            marker = "  "
            for copilot_name, reqs in DOMAIN_REQUIREMENTS.items():
                if args.copilot and args.copilot != copilot_name:
                    continue
                for req in reqs:
                    if req["label"] == label:
                        if domain is None and cnt > 0:
                            # Nodes without domain = invisible to copilot
                            if req["critical"]:
                                status = "FAIL"
                                marker = "!!"
                                domain_pass = False
                            else:
                                status = "WARN"
                                marker = "? "
                        elif domain == req["domain"] and cnt == 0:
                            if req["critical"]:
                                status = "FAIL"
                                marker = "!!"
                                domain_pass = False
                            else:
                                status = "WARN"
                                marker = "? "

            print(f"  {marker} {key:<35} {cnt:>6}  {status}")

            domain_results[key] = {"count": cnt, "status": status}

        # Actionable advice
        if not domain_pass:
            print(f"\n  !!  Domain property issues detected!")
            print(f"  Fix: Run fix_domain.py to SET domain property on affected nodes.")
            print(f"  Permanent fix: Update seed_dataops_graph.py to include domain in CREATE.")
        print()

    # ── Per-copilot checks ──────────────────────────────────────────
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
        edge_results: list[dict[str, Any]] = []
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

        # ── Edge checks (v3 addition) ────────────────────────────────
        if "edges" in spec:
            print(f"\n  {'Edge Label':<25} {'Actual':>8} {'/ Min':<8} {'Status'}")
            print(f"  {'-'*25} {'-'*8} {'-'*8} {'-'*6}")
            for label, req in spec["edges"].items():
                actual = edge_census.get(label, 0)
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
                edge_results.append(entry)

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
            "edges": edge_results,
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
        efails_edges = [e for e in res.get("edges", []) if e["status"] == "FAIL"]
        suffix = ""
        if fails:
            suffix = f"  MISSING: {', '.join(n['label'] for n in fails)}"
        if efails_edges:
            suffix += f"  EDGES: {', '.join(e['label'] for e in efails_edges)}"
        if efails:
            suffix += f"  ENDPOINT: {', '.join(e['path'] for e in efails)}"
        if warns and not fails and not efails_edges:
            suffix = f"  LOW: {', '.join(n['label'] for n in warns)}"
        print(f"  {marker} {name:<15} {res['verdict']}{suffix}")

    if args.check_domains and not domain_pass:
        print(f"\n  !! DOMAIN AUDIT:  Nodes missing domain property (see audit above)")

    print(f"\n  Graph: {total_nodes} nodes, {total_edges} edges, {len(census)} node labels, {len(edge_census)} edge labels")
    overall_pass = all_pass and (domain_pass if args.check_domains else True)
    overall = "ALL PASS" if overall_pass else "FAILURES DETECTED"
    print(f"  Overall: {overall}")
    print()

    if args.json:
        out = {
            "census": census,
            "edge_census": edge_census,
            "results": results,
            "domain_audit": domain_results if args.check_domains else {},
            "overall": overall,
        }
        print(json.dumps(out, indent=2))

    sys.exit(0 if overall_pass else 1)


if __name__ == "__main__":
    main()
