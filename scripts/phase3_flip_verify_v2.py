"""Phase 3 flip verification — score + learn through AGE active read.

Proves the full loop: score -> write to AGE -> learn -> outcome in AGE.
Verifies SOC V unchanged, trajectory/fingerprint work, status transitions.
Reads DSN from environment.
"""
import os
import sys
import time

import httpx
import psycopg2

BASE = os.environ.get("TRADING_API_BASE", "http://127.0.0.1:8010")
AGE_DSN = os.environ.get("GRAPH_DSN", os.environ.get("AGE_DSN", ""))
GRAPH_NAME = os.environ.get("GRAPH_NAME", os.environ.get("AGE_GRAPH_NAME", "soc_graph"))
EXPECTED_SOC_V = 4862

if not AGE_DSN:
    print("ERROR: set GRAPH_DSN or AGE_DSN environment variable.")
    sys.exit(1)

print("=" * 60)
print("PHASE 3 FLIP VERIFICATION")
print(f"  Backend: {BASE}")
print(f"  AGE: {GRAPH_NAME}")
print("=" * 60)

checks_passed = 0
checks_total = 0


def check(name: str, passed: bool, detail: str = "") -> bool:
    global checks_passed, checks_total
    checks_total += 1
    if passed:
        checks_passed += 1
        print(f"  {name}: PASS{' — ' + detail if detail else ''}")
    else:
        print(f"  {name}: FAIL{' — ' + detail if detail else ''}")
    return passed


# 1. Health
try:
    health = httpx.get(f"{BASE}/api/health", timeout=5).json()
    check("Health", True, f"phase={health.get('phase')}, alpha={health.get('alpha')}")
except Exception as e:
    check("Health", False, str(e))
    sys.exit(1)

# 2. Score
resp = httpx.post(f"{BASE}/api/score", json={
    "category": "trend_following",
    "factors": {
        "signal_alignment": 0.85, "market_regime": 0.70,
        "position_sizing": 0.60, "timing_quality": 0.45,
        "risk_reward_actual": 0.75, "emotional_indicator": 0.55,
        "signal_confidence": 0.65, "options_delta_exposure": 0.50,
        "options_iv_percentile": 0.40, "options_gamma_risk": 0.35,
    },
}, timeout=10)

if resp.status_code != 200:
    check("Score", False, f"HTTP {resp.status_code}: {resp.text[:200]}")
    sys.exit(1)

score_data = resp.json()
did = score_data.get("decision_id", "?")
action = score_data.get("action", "?")
conf = float(score_data.get("confidence", 0))

check("Score", True, f"{did} -> {action} (conf={conf:.3f})")
check("TRD- prefix", did.startswith("TRD-"), did)

# 3. Learn
resp = httpx.post(f"{BASE}/api/learn", json={
    "decision_id": did,
    "actual_action": action,
    "outcome": "confirmed",
}, timeout=10)
learn_ok = resp.status_code == 200
check("Learn", learn_ok, f"confirmed -> {'OK' if learn_ok else 'HTTP ' + str(resp.status_code)}")

time.sleep(0.5)

# 4. Verify in AGE directly
conn = psycopg2.connect(AGE_DSN)
conn.autocommit = True
cur = conn.cursor()
cur.execute("LOAD 'age'")
cur.execute('SET search_path = ag_catalog, "$user", public')


def cypher_one(query: str, cols: str):
    cur.execute(
        f"SELECT * FROM cypher('{GRAPH_NAME}', $$ {query} $$) as ({cols})"
    )
    return cur.fetchone()


def cypher_int(query: str) -> int:
    row = cypher_one(query, "c agtype")
    return int(str(row[0]).strip('"'))


# Decision exists with correct status
row = cypher_one(
    f"MATCH (d:Decision {{domain:'trading', decision_id:'{did}'}}) "
    f"RETURN d.status, d.confidence",
    "s agtype, c agtype"
)
if row:
    status = str(row[0]).strip('"')
    check("AGE Decision", True, f"status={status}")
    check("Status confirmed", status == "confirmed", f"got {status}")
else:
    check("AGE Decision", False, "NOT FOUND")

# Outcome exists
orow = cypher_one(
    f"MATCH (d:Decision {{domain:'trading', decision_id:'{did}'}})"
    f"-[:HAS_OUTCOME]->(o:Outcome) "
    f"RETURN o.actual_action, o.is_correct",
    "a agtype, c agtype"
)
if orow:
    check("AGE Outcome", True,
          f"action={str(orow[0]).strip(chr(34))}, correct={orow[1]}")
else:
    check("AGE Outcome", False, "NOT FOUND")

# 5. SOC V unchanged
soc_v = cypher_int(
    "MATCH (d:Decision {domain:'soc'}) "
    "WHERE (d.archived IS NULL OR d.archived <> true) "
    "AND ((d.status IS NOT NULL AND d.status IN ['confirmed','overridden']) "
    "OR (d.status IS NULL AND d.outcome IS NOT NULL)) "
    "RETURN count(DISTINCT d.decision_id)"
)
check("SOC V_soc unchanged", soc_v == EXPECTED_SOC_V,
      f"{soc_v} (expected {EXPECTED_SOC_V})")

# 6. Trading active count
trading_active = cypher_int(
    "MATCH (d:Decision {domain:'trading'}) "
    "WHERE (d.archived IS NULL OR d.archived <> true) "
    "RETURN count(d)"
)
check("Trading active <= 810", trading_active <= 810, str(trading_active))

conn.close()

# 7. Trajectory
tresp = httpx.get(f"{BASE}/api/trajectory", timeout=5)
if tresp.status_code == 200:
    tdata = tresp.json()
    points = len(tdata) if isinstance(tdata, list) else "dict"
    check("Trajectory", True, f"{points} points")
else:
    check("Trajectory", False, f"HTTP {tresp.status_code}")

# 8. Fingerprint
fresp = httpx.get(f"{BASE}/api/fingerprint", timeout=5)
if fresp.status_code == 200:
    fdata = fresp.json()
    n_factors = len(fdata.get("factors", []))
    check("Fingerprint", n_factors == 10, f"{n_factors} factors")
else:
    check("Fingerprint", False, f"HTTP {fresp.status_code}")

# Gate
print()
print("=" * 60)
print(f"Checks: {checks_passed}/{checks_total}")
if checks_passed == checks_total:
    print("FLIP: VERIFIED — Trading fully operational on AGE.")
else:
    print("FLIP: ISSUE — investigate failures above.")
print("=" * 60)

sys.exit(0 if checks_passed == checks_total else 1)
