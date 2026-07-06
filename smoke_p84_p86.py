"""P84/P86 evolution endpoint smoke tests."""
import urllib.request
import json
import sys

BASE = "http://127.0.0.1:8010/api/trading/evolution"
HEALTH = "http://127.0.0.1:8010/api/health"

passed = 0
failed = 0


def smoke(name, url):
    global passed, failed
    try:
        r = urllib.request.urlopen(url, timeout=10)
        data = json.loads(r.read())
        return data
    except Exception as e:
        print(f"FAIL {name}: {e}")
        failed += 1
        return None


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"PASS {name}")
        passed += 1
    else:
        print(f"FAIL {name} -- {detail}")
        failed += 1


# 1. Health baseline
data = smoke("health", HEALTH)
check("health", data is not None and "phase" in data)

# 2. Evolution log
data = smoke("log", f"{BASE}/log")
check("log is list", isinstance(data, list))

# 3. Active variant
data = smoke("active", f"{BASE}/active")
check("active is dict", isinstance(data, dict))
check("active has conservation_state", data is not None and "conservation_state" in data)
check("active has bounds", data is not None and "bounds" in data)

# 4. Proposals (P86)
data = smoke("proposals", f"{BASE}/proposals")
check("proposals is dict", isinstance(data, dict))
check("proposals has provenance", data is not None and data.get("provenance") == "demo",
      f"got: {data.get('provenance') if data else 'None'}")

# 5. Kind filter - variant
data = smoke("log?kind=variant", f"{BASE}/log?kind=variant")
check("variant log is list", isinstance(data, list))

# 6. Kind filter - parameter
data = smoke("log?kind=parameter", f"{BASE}/log?kind=parameter")
check("parameter log is list", isinstance(data, list))

# 7. Generate variant (POST)
try:
    req = urllib.request.Request(f"{BASE}/generate", method="POST",
                                 data=b"{}", headers={"Content-Type": "application/json"})
    r = urllib.request.urlopen(req, timeout=10)
    data = json.loads(r.read())
    check("generate returns variant", "variant_id" in data or "variant" in str(data).lower(),
          f"got: {str(data)[:100]}")
except Exception as e:
    check("generate", False, str(e))

# 8. Log after generate (should have 1+ entry)
data = smoke("log after generate", f"{BASE}/log")
check("log has entries after generate", isinstance(data, list) and len(data) >= 1,
      f"got: {len(data) if data else 'None'} entries")

print(f"\n--- RESULTS: {passed} passed, {failed} failed ---")
sys.exit(1 if failed > 0 else 0)
