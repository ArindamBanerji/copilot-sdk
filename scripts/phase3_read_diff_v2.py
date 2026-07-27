"""Phase 3 Step 5 — ReadDiffRunner compare_all for Trading.

Constructs separate SQLite and AGE stores for independent comparison.
Does NOT use DualWriteStore — the diff needs distinct store instances.
"""
import os
import sys

from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
from copilot_sdk.graph.read_diff_runner import ReadDiffRunner

SQLITE_PATH = os.path.expanduser("~/.ci-platform/trading/trading.db")
AGE_DSN = "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres"
GRAPH_NAME = "soc_graph"
DOMAIN = "trading"

print("=" * 60)
print("PHASE 3 — TRADING READ-DIFF compare_all")
print("=" * 60)

# Primary: SQLite
primary = SQLiteGraphStore(SQLITE_PATH, domain=DOMAIN, decision_id_prefix="TRD-")

# Secondary: AGE — use the factory's AGE construction path
try:
    from copilot_sdk.graph.factory import create_graph_store
    secondary = create_graph_store(
        backend="age",
        dsn=AGE_DSN,
        graph_name=GRAPH_NAME,
        domain=DOMAIN,
    )
except Exception as e:
    # Fallback: direct adapter construction
    from ci_platform.graph.age_sdk_adapter import AGEGraphStoreAdapter
    secondary = AGEGraphStoreAdapter(
        dsn=AGE_DSN,
        graph_name=GRAPH_NAME,
        domain=DOMAIN,
    )
    print(f"(Using direct adapter — factory raised: {e})")

runner = ReadDiffRunner(primary, secondary, domain=DOMAIN)
report = runner.compare_all()

print(report.summary())
print()
print(f"PASSED: {report.passed}")
print(f"Primary verified: {report.primary_count}")
print(f"Secondary verified: {report.secondary_count}")
print(f"Primary total: {report.primary_total}")
print(f"Secondary total: {report.secondary_total}")

if report.field_mismatches:
    print(f"\nField mismatches ({len(report.field_mismatches)}):")
    for m in report.field_mismatches[:10]:
        print(f"  {m}")

if report.missing_in_secondary:
    print(f"\nMissing in AGE ({len(report.missing_in_secondary)}):")
    for did in report.missing_in_secondary[:10]:
        print(f"  {did}")

if report.missing_in_primary:
    print(f"\nMissing in SQLite ({len(report.missing_in_primary)}):")
    for did in report.missing_in_primary[:10]:
        print(f"  {did}")

primary.close()
try:
    secondary.close()
except Exception:
    pass

print()
print("=" * 60)
if report.passed:
    print("GATE: ✅ PASS — Trading SQLite and AGE are in parity.")
else:
    print("GATE: ❌ FAIL — investigate mismatches above.")
print("=" * 60)

sys.exit(0 if report.passed else 1)
