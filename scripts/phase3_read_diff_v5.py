"""Phase 3 — ReadDiffRunner verified parity for Trading."""
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
print("PHASE 3 — TRADING READ-DIFF (verified parity)")
print("=" * 60)
print(f"Source: {SQLITE_PATH}")

primary = SQLiteGraphStore(SQLITE_PATH, domain=DOMAIN, decision_id_prefix="TRD-")
secondary = AGEGraphStoreAdapter(dsn=AGE_DSN, graph_name="soc_graph")

p_verified = primary.count_verified(DOMAIN)
s_verified = secondary.count_verified(DOMAIN)
p_correct = primary.count_correct(DOMAIN)
s_correct = secondary.count_correct(DOMAIN)
p_total = primary.count_decisions(DOMAIN)
s_total = secondary.count_decisions(DOMAIN)

print(f"Primary (SQLite)  — verified: {p_verified}, correct: {p_correct}, total: {p_total}")
print(f"Secondary (AGE)   — verified: {s_verified}, correct: {s_correct}, total: {s_total}")
print(f"Pending not migrated: {p_total - s_total} (expected: {p_total - p_verified})")

verified_match = p_verified == s_verified
correct_match = p_correct == s_correct
print(f"\nVerified count match: {verified_match} {'PASS' if verified_match else 'FAIL'}")
print(f"Correct count match:  {correct_match} {'PASS' if correct_match else 'FAIL'}")

if not verified_match or not correct_match:
    print("\nGATE: FAIL — count parity broken.")
    primary.close()
    try:
        secondary.close()
    except Exception:
        pass
    sys.exit(1)

p_decisions = primary.get_verified_decisions(DOMAIN)
s_decisions = secondary.get_verified_decisions(DOMAIN)

p_map = {d["decision_id"]: d for d in p_decisions}
s_map = {d["decision_id"]: d for d in s_decisions}

missing_in_age = [k for k in p_map if k not in s_map]
missing_in_sqlite = [k for k in s_map if k not in p_map]

COMPARE_FIELDS = [
    "decision_id", "domain", "category", "recommended_action",
    "confidence", "status", "is_correct", "actual_action",
]

field_mismatches = []
for did in p_map:
    if did in s_map:
        for field in COMPARE_FIELDS:
            pv = p_map[did].get(field)
            sv = s_map[did].get(field)
            if isinstance(pv, float) and isinstance(sv, float):
                if abs(pv - sv) < 1e-6:
                    continue
            if pv is None and sv is None:
                continue
            if pv != sv:
                field_mismatches.append({
                    "decision_id": did, "field": field,
                    "primary": pv, "secondary": sv,
                })

print(f"\nL2 comparison: {len(p_map)} verified decisions")
print(f"Missing in AGE:    {len(missing_in_age)}")
print(f"Missing in SQLite: {len(missing_in_sqlite)}")
print(f"Field mismatches:  {len(field_mismatches)}")

if missing_in_age:
    for did in missing_in_age[:10]:
        print(f"  Missing in AGE: {did}")

if missing_in_sqlite:
    for did in missing_in_sqlite[:10]:
        print(f"  Missing in SQLite: {did}")

if field_mismatches:
    for m in field_mismatches[:10]:
        print(f"  Mismatch: {m}")

primary.close()
try:
    secondary.close()
except Exception:
    pass

passed = (verified_match and correct_match
          and not missing_in_age and not missing_in_sqlite
          and not field_mismatches)

print()
print("=" * 60)
if passed:
    print("GATE: PASS — Trading verified decisions in parity.")
else:
    print("GATE: FAIL — investigate mismatches above.")
print("=" * 60)
sys.exit(0 if passed else 1)
