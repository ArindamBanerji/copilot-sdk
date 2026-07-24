"""Phase 3 — compare_active + compare_history for Trading.

Uses the v3.22 read-diff modes. Both must pass for flip gate.
Run with Trading backend STOPPED to avoid SQLite WAL visibility issues.
"""
import os
import sys

from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
from copilot_sdk.graph.read_diff_runner import ReadDiffRunner
from ci_platform.graph.age_sdk_adapter import AGEGraphStoreAdapter

SDK_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQLITE_PATH = os.path.join(SDK_ROOT, "apps", "trading", "backend", "data", "trading.db")
AGE_DSN = "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres"
DOMAIN = "trading"

if not os.path.exists(SQLITE_PATH):
    print(f"ERROR: SQLite not found at {SQLITE_PATH}")
    sys.exit(1)

print("=" * 60)
print("PHASE 3 — TRADING DUAL PARITY (active + history)")
print("=" * 60)
print(f"Source: {SQLITE_PATH}")

primary = SQLiteGraphStore(SQLITE_PATH, domain=DOMAIN, decision_id_prefix="TRD-")
secondary = AGEGraphStoreAdapter(dsn=AGE_DSN, graph_name="soc_graph")

# Raw counts for diagnostics
p_active = primary.count_decisions(DOMAIN)
p_verified = primary.count_verified(DOMAIN)
s_active = secondary.count_decisions(DOMAIN)
s_verified = secondary.count_verified(DOMAIN)

p_archived = primary.get_archived_decisions(DOMAIN)
s_archived = secondary.get_archived_decisions(DOMAIN)

print(f"\nPrimary (SQLite):")
print(f"  Active: {p_active} total, {p_verified} verified")
print(f"  Archived: {len(p_archived)}")
print(f"  Grand total: {p_active + len(p_archived)}")

print(f"Secondary (AGE):")
print(f"  Active: {s_active} total, {s_verified} verified")
print(f"  Archived: {len(s_archived)}")
print(f"  Grand total: {s_active + len(s_archived)}")

runner = ReadDiffRunner(primary, secondary, domain=DOMAIN)

# Active parity
print("\n--- ACTIVE PARITY ---")
try:
    active_report = runner.compare_active()
    print(active_report.summary())
    active_passed = active_report.passed
    print(f"Active PASSED: {active_passed}")
except Exception as e:
    print(f"compare_active failed: {e}")
    active_passed = False

# History parity
print("\n--- HISTORY PARITY ---")
try:
    history_report = runner.compare_history(compare_archived_at=False)
    print(history_report.summary())
    history_passed = history_report.passed
    print(f"History PASSED: {history_passed}")
except Exception as e:
    print(f"compare_history failed: {e}")
    history_passed = False

primary.close()
try:
    secondary.close()
except Exception:
    pass

# Gate
print()
print("=" * 60)
if active_passed and history_passed:
    print("GATE: PASS — both active and history parity confirmed.")
else:
    if not active_passed:
        print("GATE: FAIL — active parity broken.")
    if not history_passed:
        print("GATE: FAIL — history parity broken.")
print("=" * 60)

sys.exit(0 if (active_passed and history_passed) else 1)
