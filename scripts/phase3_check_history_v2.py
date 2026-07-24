"""Check Trading backend's own decision count via API."""
import httpx
import sys

BASE = "http://127.0.0.1:8010"

try:
    resp = httpx.get(f"{BASE}/api/history", timeout=10)
    data = resp.json()
except Exception as e:
    print(f"API request failed: {e}")
    sys.exit(1)

print("=" * 60)
print("TRADING BACKEND — LIVE STORE STATE")
print("=" * 60)

# Handle both list and dict response formats
if isinstance(data, dict):
    decisions = data.get("decisions", data.get("items", []))
    total_reported = data.get("total", data.get("count", len(decisions)))
    print(f"Response type: dict (total field: {total_reported})")
elif isinstance(data, list):
    decisions = data
    total_reported = len(data)
    print(f"Response type: list ({total_reported} items)")
else:
    print(f"Unexpected response type: {type(data)}")
    sys.exit(1)

trd = [x for x in decisions if x.get("decision_id", "").startswith("TRD-")]
verified = [x for x in decisions if x.get("status") in ("confirmed", "overridden")]
pending = [x for x in decisions if x.get("status") in ("pending", None)]

print(f"Total returned: {len(decisions)}")
print(f"TRD- prefixed:  {len(trd)}")
print(f"Verified:       {len(verified)}")
print(f"Pending/null:   {len(pending)}")

if len(decisions) == 400:
    print("\nWARNING: exactly 400 returned — may be truncated by default limit")

# Show newest 5 by decision_id (likely most recent)
if decisions:
    newest = sorted(decisions, key=lambda x: x.get("created_at", 0), reverse=True)[:5]
    print(f"\nNewest 5 decisions:")
    for d in newest:
        print(f"  {d.get('decision_id', '?'):20s} status={str(d.get('status', '?')):12s} cat={d.get('category', '?')}")

# Also check measurement-state for total count
try:
    ms = httpx.get(f"{BASE}/api/measurement-state", timeout=5).json()
    if isinstance(ms, dict):
        for key in ("total_decisions", "verified_count", "correct_count", "decision_count"):
            if key in ms:
                print(f"\nmeasurement-state.{key}: {ms[key]}")
except Exception:
    pass

print("=" * 60)
