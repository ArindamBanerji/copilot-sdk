"""Phase 3 — durable 40-cycle dual-write validation gate.

Per-cycle verification (while backend is running):
- Score N decisions, learn on 2
- Verify all scored decision_ids exist in AGE (secondary write proof)
- Verify AGE active count stays within retention cap (800 +/- margin)
- Verify AGE archived count is non-decreasing (retention symmetry)
- Verify outbox has 0 pending and 0 failed entries

Full field-level parity (compare_active + compare_history) runs ONCE
after the 40 cycles complete and the backend is stopped, because
Windows SQLite WAL prevents cross-process reads while the backend
holds the connection. The stopped-backend parity check is the true
flip gate.

Reads DSN/graph from environment (no hardcoded credentials).
Persists cycle state to a JSON checkpoint. Resumable.
Resets consecutive counter on any failure.
"""
import json
import os
import sys
import time

import httpx
import psycopg2

SDK_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQLITE_PATH = os.path.join(SDK_ROOT, "apps", "trading", "backend", "data", "trading.db")

AGE_DSN = os.environ.get("GRAPH_DSN", os.environ.get("AGE_DSN", ""))
GRAPH_NAME = os.environ.get("GRAPH_NAME", os.environ.get("AGE_GRAPH_NAME", "soc_graph"))
BASE = os.environ.get("TRADING_API_BASE", "http://127.0.0.1:8010")
DOMAIN = "trading"

TARGET_CYCLES = int(os.environ.get("PHASE3_TARGET_CYCLES", "40"))
SCORES_PER_CYCLE = 3
LEARNS_PER_CYCLE = 2
RETENTION_CAP = 800
RETENTION_MARGIN = 10  # allow cap + margin for in-flight scores

CHECKPOINT_PATH = os.path.join(
    SDK_ROOT, "apps", "trading", "backend", "data", "phase3_cycle_checkpoint.json"
)

CATEGORIES = [
    "trend_following", "mean_reversion", "event_driven",
    "income_strategy", "scalp_intraday",
]
FACTORS = {
    "signal_alignment": 0.72, "market_regime": 0.65,
    "position_sizing": 0.80, "timing_quality": 0.55,
    "risk_reward_actual": 0.60, "emotional_indicator": 0.45,
    "signal_confidence": 0.70, "options_delta_exposure": 0.50,
    "options_iv_percentile": 0.40, "options_gamma_risk": 0.35,
}


def load_checkpoint() -> dict:
    if os.path.exists(CHECKPOINT_PATH):
        with open(CHECKPOINT_PATH) as f:
            return json.load(f)
    return {
        "consecutive": 0, "total_cycles": 0,
        "total_scored": 0, "total_learned": 0,
        "last_age_archived": 0, "history": [],
    }


def save_checkpoint(state: dict) -> None:
    tmp = CHECKPOINT_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, CHECKPOINT_PATH)


class AGEConnection:
    """Reusable AGE connection for one cycle's queries."""

    def __init__(self, dsn: str, graph_name: str):
        self.conn = psycopg2.connect(dsn)
        self.conn.autocommit = True
        self.cur = self.conn.cursor()
        self.cur.execute("LOAD 'age'")
        self.cur.execute('SET search_path = ag_catalog, "$user", public')
        self.graph_name = graph_name

    def query_int(self, cypher: str) -> int:
        self.cur.execute(
            f"SELECT * FROM cypher('{self.graph_name}', $$ {cypher} $$) as (c agtype)"
        )
        return int(str(self.cur.fetchone()[0]).strip('"'))

    def has_decision(self, decision_id: str) -> bool:
        return self.query_int(
            f"MATCH (d:Decision {{domain:'{DOMAIN}', decision_id:'{decision_id}'}}) "
            f"RETURN count(d)"
        ) > 0

    def active_count(self) -> int:
        return self.query_int(
            f"MATCH (d:Decision {{domain:'{DOMAIN}'}}) "
            f"WHERE (d.archived IS NULL OR d.archived <> true) "
            f"RETURN count(d)"
        )

    def archived_count(self) -> int:
        return self.query_int(
            f"MATCH (d:Decision {{domain:'{DOMAIN}'}}) "
            f"WHERE d.archived = true "
            f"RETURN count(d)"
        )

    def verified_count(self) -> int:
        return self.query_int(
            f"MATCH (d:Decision {{domain:'{DOMAIN}'}}) "
            f"WHERE (d.archived IS NULL OR d.archived <> true) "
            f"AND ((d.status IS NOT NULL AND d.status IN ['confirmed','overridden']) "
            f"OR (d.status IS NULL AND d.outcome IS NOT NULL)) "
            f"RETURN count(DISTINCT d.decision_id)"
        )

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass


def check_outbox() -> dict:
    import sqlite3
    outbox_path = os.path.join(
        SDK_ROOT, "apps", "trading", "backend", "data",
        "trading_dual_write_outbox.db",
    )
    if not os.path.exists(outbox_path):
        return {"pending": 0, "failed": 0, "clean": True, "exists": False}
    conn = sqlite3.connect(outbox_path)
    cur = conn.cursor()
    try:
        # Verify table exists
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='secondary_outbox'"
        )
        if not cur.fetchone():
            conn.close()
            return {"pending": 0, "failed": 0, "clean": True, "exists": True,
                    "note": "table not created yet"}
        pending = cur.execute(
            "SELECT COUNT(*) FROM secondary_outbox WHERE status='pending'"
        ).fetchone()[0]
        failed = cur.execute(
            "SELECT COUNT(*) FROM secondary_outbox WHERE status='failed'"
        ).fetchone()[0]
        conn.close()
        return {"pending": pending, "failed": failed,
                "clean": pending == 0 and failed == 0, "exists": True}
    except Exception as e:
        conn.close()
        return {"pending": -1, "failed": -1, "clean": False, "exists": True,
                "error": str(e)}


def run_cycle(cycle_num: int, age: AGEConnection, last_archived: int) -> dict:
    """Score, learn, verify one cycle."""
    # Score
    scored = []
    for i in range(SCORES_PER_CYCLE):
        cat = CATEGORIES[(cycle_num * SCORES_PER_CYCLE + i) % len(CATEGORIES)]
        resp = httpx.post(
            f"{BASE}/api/score",
            json={"category": cat, "factors": FACTORS},
            timeout=10,
        )
        if resp.status_code != 200:
            return {"passed": False, "reason": f"score HTTP {resp.status_code}: {resp.text[:100]}"}
        data = resp.json()
        did = data.get("decision_id", "?")
        if not did.startswith("TRD-"):
            return {"passed": False, "reason": f"no TRD- prefix: {did}"}
        scored.append({"decision_id": did, "action": data.get("action", "?")})

    # Learn
    for i, s in enumerate(scored[:LEARNS_PER_CYCLE]):
        resp = httpx.post(
            f"{BASE}/api/learn",
            json={
                "decision_id": s["decision_id"],
                "actual_action": s["action"],
                "outcome": "confirmed" if i == 0 else "overridden",
            },
            timeout=10,
        )
        if resp.status_code != 200:
            return {"passed": False, "reason": f"learn HTTP {resp.status_code}: {resp.text[:100]}"}

    time.sleep(0.5)

    # Verify all scored decisions exist in AGE
    for s in scored:
        if not age.has_decision(s["decision_id"]):
            return {"passed": False, "reason": f"{s['decision_id']} not in AGE"}

    # AGE count checks
    age_active = age.active_count()
    age_archived = age.archived_count()
    age_verified = age.verified_count()

    # Active count within retention cap + margin
    if age_active > RETENTION_CAP + RETENTION_MARGIN:
        return {"passed": False,
                "reason": f"AGE active {age_active} > {RETENTION_CAP}+{RETENTION_MARGIN}"}

    # Archived count must be non-decreasing (retention only adds, never removes)
    if age_archived < last_archived:
        return {"passed": False,
                "reason": f"AGE archived decreased: {age_archived} < {last_archived}"}

    # Outbox must be clean
    outbox = check_outbox()
    if not outbox["clean"]:
        return {"passed": False,
                "reason": f"outbox: {outbox['pending']}p/{outbox['failed']}f"}

    return {
        "passed": True,
        "scored": len(scored),
        "learned": min(LEARNS_PER_CYCLE, len(scored)),
        "age_active": age_active,
        "age_archived": age_archived,
        "age_verified": age_verified,
    }


# === MAIN ===

if not AGE_DSN:
    print("ERROR: set GRAPH_DSN or AGE_DSN environment variable.")
    sys.exit(1)

if not os.path.exists(SQLITE_PATH):
    print(f"ERROR: SQLite not found at {SQLITE_PATH}")
    sys.exit(1)

print("=" * 60)
print("PHASE 3 — DURABLE 40-CYCLE GATE")
print(f"  Target: {TARGET_CYCLES} consecutive zero-discrepancy cycles")
print(f"  Per cycle: {SCORES_PER_CYCLE} scores + {LEARNS_PER_CYCLE} learns")
print(f"  Retention cap: {RETENTION_CAP}")
print(f"  Checkpoint: {CHECKPOINT_PATH}")
print(f"  AGE: {GRAPH_NAME}")
print("=" * 60)

# Pre-flight
try:
    health = httpx.get(f"{BASE}/api/health", timeout=5).json()
    print(f"Health: OK (phase={health.get('phase')})")
except Exception as e:
    print(f"Backend not reachable: {e}")
    sys.exit(1)

state = load_checkpoint()
consecutive = state["consecutive"]
total_scored = state["total_scored"]
total_learned = state["total_learned"]
last_archived = state.get("last_age_archived", 0)

if consecutive > 0:
    print(f"Resuming: {consecutive}/{TARGET_CYCLES} consecutive cycles recorded.")

remaining = TARGET_CYCLES - consecutive
if remaining <= 0:
    print(f"Already reached {TARGET_CYCLES} cycles. Gate PASSED.")
    sys.exit(0)

print(f"Running {remaining} remaining cycles...\n")

age = AGEConnection(AGE_DSN, GRAPH_NAME)

try:
    for i in range(remaining):
        cycle_num = state["total_cycles"] + 1
        result = run_cycle(cycle_num, age, last_archived)

        if result["passed"]:
            consecutive += 1
            total_scored += result["scored"]
            total_learned += result["learned"]
            last_archived = result["age_archived"]
            state.update({
                "consecutive": consecutive,
                "total_cycles": cycle_num,
                "total_scored": total_scored,
                "total_learned": total_learned,
                "last_age_archived": last_archived,
            })
            state["history"].append({
                "cycle": cycle_num,
                "passed": True,
                "age_active": result["age_active"],
                "age_archived": result["age_archived"],
                "age_verified": result["age_verified"],
                "timestamp": time.time(),
            })
            save_checkpoint(state)
            print(f"  Cycle {cycle_num:3d}: PASS "
                  f"(consecutive={consecutive}/{TARGET_CYCLES}, "
                  f"active={result['age_active']}, "
                  f"archived={result['age_archived']}, "
                  f"verified={result['age_verified']})")
        else:
            state.update({
                "consecutive": 0,
                "total_cycles": cycle_num,
                "total_scored": total_scored,
                "total_learned": total_learned,
                "last_age_archived": last_archived,
            })
            state["history"].append({
                "cycle": cycle_num,
                "passed": False,
                "reason": result["reason"],
                "timestamp": time.time(),
            })
            save_checkpoint(state)
            print(f"  Cycle {cycle_num:3d}: FAIL -- {result['reason']}")
            print(f"\nConsecutive counter RESET to 0. Fix and re-run.")
            age.close()
            sys.exit(1)
finally:
    age.close()

print()
print("=" * 60)
print(f"GATE: PASS -- {TARGET_CYCLES} consecutive cycles achieved.")
print(f"  Total scored:  {total_scored}")
print(f"  Total learned: {total_learned}")
print(f"  AGE archived:  {last_archived}")
print()
print("NEXT (mandatory before flip):")
print("  1. Stop Trading backend (Ctrl+C)")
print("  2. python scripts/phase3_dual_parity_v2.py  (full field parity)")
print("  3. Both active + history must PASS")
print("  4. Then flip: set TRADING_ACTIVE_GRAPH_BACKEND=age")
print("=" * 60)
sys.exit(0)
