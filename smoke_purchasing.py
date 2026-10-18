import httpx
for ep in ["/api/purchasing/commodity-prices/produce", "/api/purchasing/par-recommendations", "/api/purchasing/supplier-scorecard/SUP-001"]:
    r = httpx.get(f"http://localhost:8020{ep}", timeout=5)
    print(f"{ep}: {'PASS' if r.status_code == 200 else f'FAIL ({r.status_code})'}")
