"""Phase 3 Step 7 — score Trading alerts and verify dual-write.

Discovers the /api/score and /api/learn payload schema from openapi.json,
scores N alerts, learns on 2, verifies TRD- prefix and AGE presence.
"""
import json
import sys
import time

try:
    import httpx
except ImportError:
    print("httpx not available — install or switch to requests")
    sys.exit(1)

BASE = "http://127.0.0.1:8010"
N = 5

print("=" * 60)
print(f"PHASE 3 — DUAL-WRITE E2E ({N} alerts)")
print("=" * 60)

# Pre-flight: health check
try:
    health = httpx.get(f"{BASE}/api/health", timeout=5).json()
    print(f"Health: OK (phase={health.get('phase')})")
except Exception as e:
    print(f"Health check failed: {e}")
    sys.exit(1)

# Discover payload schema
print("\nDiscovering /api/score schema...")
spec = httpx.get(f"{BASE}/openapi.json", timeout=5).json()
score_schema = spec.get("paths", {}).get("/api/score", {})
score_method = score_schema.get("post", {})
score_body = score_method.get("requestBody", {})
print(f"  Score endpoint found: {'post' in score_schema}")
if score_body:
    content = score_body.get("content", {}).get("application/json", {})
    schema_ref = content.get("schema", {})
    print(f"  Body schema: {json.dumps(schema_ref, indent=4)[:300]}")

# Capture baseline counts
print("\nCapturing baseline...")
import os
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore

sqlite_path = os.path.expanduser("~/.ci-platform/trading/trading.db")
sqlite = SQLiteGraphStore(sqlite_path, domain="trading", decision_id_prefix="TRD-")
baseline_total = sqlite.count_decisions("trading")
baseline_verified = sqlite.count_verified("trading")
print(f"  SQLite: {baseline_total} total, {baseline_verified} verified")
sqlite.close()

# Score N alerts
print(f"\nScoring {N} alerts...")
scored_ids = []
for i in range(1, N + 1):
    payload = {
        "alert_id": f"DUAL-TEST-{i:03d}",
        "category": "market_manipulation",
    }
    resp = httpx.post(f"{BASE}/api/score", json=payload, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        did = data.get("decision_id", "UNKNOWN")
        scored_ids.append(did)
        has_prefix = did.startswith("TRD-")
        print(f"  {payload['alert_id']} → {did} (TRD-: {has_prefix}, conf: {data.get('confidence', '?'):.3f})")
        if not has_prefix:
            print(f"    ❌ WARNING: missing TRD- prefix — governed write may not be active")
    else:
        print(f"  FAILED {payload['alert_id']}: HTTP {resp.status_code}")
        print(f"    {resp.text[:300]}")

if not scored_ids:
    print("\nNo decisions scored. Check API payload format above.")
    sys.exit(1)

print(f"\nScored {len(scored_ids)} decisions")

# Learn on first 2
print("\nLearning on first 2...")
for i, did in enumerate(scored_ids[:2]):
    is_correct = i == 0
    payload = {
        "decision_id": did,
        "actual_action": "escalate" if is_correct else "monitor",
        "is_correct": is_correct,
    }
    resp = httpx.post(f"{BASE}/api/learn", json=payload, timeout=10)
    if resp.status_code == 200:
        print(f"  {did}: correct={is_correct} → OK")
    else:
        print(f"  {did}: correct={is_correct} → HTTP {resp.status_code}")
        print(f"    {resp.text[:300]}")

time.sleep(1)

# Verify counts changed
print("\nPost-scoring counts...")
sqlite = SQLiteGraphStore(sqlite_path, domain="trading", decision_id_prefix="TRD-")
after_total = sqlite.count_decisions("trading")
after_verified = sqlite.count_verified("trading")
print(f"  SQLite: {after_total} total (+{after_total - baseline_total}), {after_verified} verified (+{after_verified - baseline_verified})")
sqlite.close()

# Verify AGE has the new decisions
print("\nChecking AGE for new decisions...")
import psycopg2

conn = psycopg2.connect("host=localhost port=5433 dbname=soc_copilot user=postgres password=postgres")
conn.autocommit = True
cur = conn.cursor()
cur.execute("LOAD 'age'")
cur.execute('SET search_path = ag_catalog, "$user", public')

cur.execute("SELECT * FROM cypher('soc_graph', $$ MATCH (d:Decision {domain:'trading'}) RETURN count(d) $$) as (c agtype)")
age_total = int(str(cur.fetchone()[0]).strip('"'))

cur.execute("SELECT * FROM cypher('soc_graph', $$ MATCH (d:Decision {domain:'trading'}) WHERE d.status IN ['confirmed','overridden'] RETURN count(d) $$) as (c agtype)")
age_verified = int(str(cur.fetchone()[0]).strip('"'))

print(f"  AGE: {age_total} total, {age_verified} verified")

# Check if new scored IDs exist in AGE
found_in_age = 0
for did in scored_ids[:3]:
    cur.execute(f"SELECT * FROM cypher('soc_graph', $$ MATCH (d:Decision {{domain:'trading', decision_id:'{did}'}}) RETURN count(d) $$) as (c agtype)")
    count = int(str(cur.fetchone()[0]).strip('"'))
    if count > 0:
        found_in_age += 1
        print(f"  {did}: ✅ in AGE")
    else:
        print(f"  {did}: ❌ NOT in AGE")

conn.close()

# Summary
print()
print("=" * 60)
all_prefixed = all(d.startswith("TRD-") for d in scored_ids)
new_in_sqlite = after_total > baseline_total
new_in_age = found_in_age > 0

print(f"TRD- prefix on all IDs: {all_prefixed} {'✅' if all_prefixed else '❌'}")
print(f"New decisions in SQLite: {new_in_sqlite} {'✅' if new_in_sqlite else '❌'}")
print(f"New decisions in AGE:    {found_in_age}/{min(3, len(scored_ids))} checked {'✅' if new_in_age else '❌'}")

if all_prefixed and new_in_sqlite and new_in_age:
    print("\nDUAL-WRITE: ✅ PROVEN — governed writes landing in both stores.")
    print("Run phase3_read_diff_v4.py for full parity check.")
else:
    print("\nDUAL-WRITE: ❌ ISSUE — investigate above.")
print("=" * 60)

sys.exit(0 if (all_prefixed and new_in_sqlite and new_in_age) else 1)
