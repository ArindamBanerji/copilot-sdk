"""Phase 3 — score Trading alerts and verify dual-write."""
import os
import sqlite3 as sqlite3_mod
import sys
import time

import httpx
import psycopg2

from copilot_sdk.graph.sqlite_store import SQLiteGraphStore

BASE = "http://127.0.0.1:8010"
N = 5
SDK_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQLITE_PATH = os.path.join(SDK_ROOT, "apps", "trading", "backend", "data", "trading.db")
AGE_DSN = "host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres"
OUTBOX_DIR = os.path.join(SDK_ROOT, "apps", "trading", "backend", "data")

CATEGORIES = [
    "trend_following", "mean_reversion", "event_driven",
    "income_strategy", "scalp_intraday",
]

FACTORS = {
    "signal_alignment": 0.82, "market_regime": 0.88,
    "position_sizing": 0.76, "timing_quality": 0.34,
    "risk_reward_actual": 0.67, "emotional_indicator": 0.71,
    "signal_confidence": 0.50, "options_delta_exposure": 0.50,
    "options_iv_percentile": 0.50, "options_gamma_risk": 0.50,
}

print("=" * 60)
print(f"PHASE 3 — DUAL-WRITE E2E ({N} alerts)")
print("=" * 60)
print(f"SQLite: {SQLITE_PATH}")

if not os.path.exists(SQLITE_PATH):
    print(f"ERROR: SQLite not found")
    sys.exit(1)

try:
    health = httpx.get(f"{BASE}/api/health", timeout=5).json()
    print(f"Health: OK (phase={health.get('phase')})")
except Exception as e:
    print(f"Health check failed: {e}")
    sys.exit(1)

# Baseline
sqlite = SQLiteGraphStore(SQLITE_PATH, domain="trading", decision_id_prefix="TRD-")
base_total = sqlite.count_decisions("trading")
base_verified = sqlite.count_verified("trading")
sqlite.close()
print(f"Baseline: {base_total} total, {base_verified} verified")

# Score
print(f"\nScoring {N} decisions...")
scored = []
for i in range(N):
    payload = {"category": CATEGORIES[i % len(CATEGORIES)], "factors": FACTORS}
    resp = httpx.post(f"{BASE}/api/score", json=payload, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        did = data.get("decision_id", "?")
        action = data.get("action", "?")
        conf = data.get("confidence", 0)
        prefix_ok = did.startswith("TRD-")
        scored.append({"decision_id": did, "action": action})
        print(f"  {i+1}. {did} -> {action} (conf={conf:.3f}, TRD-={'Y' if prefix_ok else 'N'})")
    else:
        print(f"  {i+1}. FAILED: HTTP {resp.status_code} -- {resp.text[:200]}")

if not scored:
    print("No decisions scored.")
    sys.exit(1)

# Learn on first 2
print(f"\nLearning on first 2...")
for i, s in enumerate(scored[:2]):
    payload = {
        "decision_id": s["decision_id"],
        "actual_action": s["action"],
        "outcome": "confirmed" if i == 0 else "overridden",
    }
    resp = httpx.post(f"{BASE}/api/learn", json=payload, timeout=10)
    label = payload["outcome"]
    if resp.status_code == 200:
        print(f"  {s['decision_id']}: {label} -> OK")
    else:
        print(f"  {s['decision_id']}: {label} -> HTTP {resp.status_code}")
        print(f"    {resp.text[:300]}")

print("\nWaiting 2s for writes to settle...")
time.sleep(2)

# Post-scoring SQLite
sqlite = SQLiteGraphStore(SQLITE_PATH, domain="trading", decision_id_prefix="TRD-")
after_total = sqlite.count_decisions("trading")
after_verified = sqlite.count_verified("trading")
sqlite.close()
delta_total = after_total - base_total
delta_verified = after_verified - base_verified
print(f"\nSQLite after: {after_total} total (+{delta_total}), {after_verified} verified (+{delta_verified})")

# Check AGE
print("\nChecking AGE for scored decisions...")
conn = psycopg2.connect(AGE_DSN)
conn.autocommit = True
cur = conn.cursor()
cur.execute("LOAD 'age'")
cur.execute('SET search_path = ag_catalog, "$user", public')

found_in_age = 0
for s in scored:
    did = s["decision_id"]
    cur.execute(
        f"SELECT * FROM cypher('soc_graph', $$ "
        f"MATCH (d:Decision {{domain:'trading', decision_id:'{did}'}}) "
        f"RETURN count(d) $$) as (c agtype)"
    )
    count = int(str(cur.fetchone()[0]).strip('"'))
    if count > 0:
        found_in_age += 1
        print(f"  {did}: found in AGE")
    else:
        print(f"  {did}: NOT in AGE")

conn.close()

# Outbox check
print("\nOutbox check...")
outbox_found = False
for candidate in [
    os.path.join(OUTBOX_DIR, "trading_dual_write_outbox.db"),
    os.path.expanduser("~/.ci-platform/trading/trading_dual_write_outbox.db"),
]:
    if os.path.exists(candidate):
        outbox_found = True
        oconn = sqlite3_mod.connect(candidate)
        ocur = oconn.cursor()
        try:
            pending = ocur.execute(
                "SELECT COUNT(*) FROM secondary_outbox WHERE status='pending'"
            ).fetchone()[0]
            failed = ocur.execute(
                "SELECT COUNT(*) FROM secondary_outbox WHERE status='failed'"
            ).fetchone()[0]
            print(f"  Outbox ({candidate}): {pending} pending, {failed} failed")
            outbox_ok = pending == 0 and failed == 0
        except sqlite3_mod.OperationalError:
            print(f"  Outbox ({candidate}): no entries")
            outbox_ok = True
        oconn.close()
        break

if not outbox_found:
    print("  No outbox DB found (OK if no failures)")
    outbox_ok = True

# Gate
print()
print("=" * 60)
all_prefixed = all(s["decision_id"].startswith("TRD-") for s in scored)
new_in_sqlite = delta_total >= N
all_in_age = found_in_age == len(scored)

print(f"TRD- prefix:    {'PASS' if all_prefixed else 'FAIL'}")
print(f"SQLite new:     +{delta_total} (expected +{N}) {'PASS' if new_in_sqlite else 'FAIL'}")
print(f"AGE found:      {found_in_age}/{len(scored)} {'PASS' if all_in_age else 'FAIL'}")
print(f"Verified delta: +{delta_verified}")
print(f"Outbox clean:   {'PASS' if outbox_ok else 'FAIL'}")

gate = all_prefixed and new_in_sqlite and all_in_age and outbox_ok

if gate:
    print("\nDUAL-WRITE: PROVEN")
else:
    print("\nDUAL-WRITE: ISSUE -- investigate above")
print("=" * 60)
sys.exit(0 if gate else 1)
