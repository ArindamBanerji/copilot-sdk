"""Measure real Purchasing writes, competing reads, and direct/proxy latency."""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

BODY = {
    "category": "protein",
    "factors": {"expected_demand": 0.5, "day_of_week": 0.86,
                "weather_forecast": 0.5, "event_flag": 0.0,
                "historical_waste": 0.08, "supplier_lead_time": 0.5,
                "price_memory_index": 0.5},
    "context": {"item": "chicken_breast", "quantity": 10},
    "metadata": {"diagnostic": "mutable_flow_probe"},
}
GETS = ("/api/health", "/api/fingerprint", "/api/conservation/status",
        "/api/self/accuracy-by-category", "/api/self/centroid-timeline", "/api/trajectory")


def measure(base: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    result: dict[str, Any] = {"url": base + path, "method": "GET" if body is None else "POST"}
    request = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(),
                                     headers={} if body is None else {"Content-Type": "application/json"})
    try:
        try:
            response = urllib.request.urlopen(request, timeout=45)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            raw = response.read()
            result.update(status=response.status, bytes=len(raw))
        try:
            result["payload"] = json.loads(raw)
        except ValueError:
            result["payload"] = raw.decode(errors="replace")[:200]
    except Exception as error:
        result["error"] = str(error)
    result["ms"] = round((time.perf_counter() - started) * 1000, 3)
    print(json.dumps({key: value for key, value in result.items() if key != "payload"}), flush=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--base", default="http://127.0.0.1:8020")
    args = parser.parse_args()
    results = [measure(args.base, "/api/score", BODY) for _ in range(3)]
    for result, path in zip(results[:2], ("/api/purchasing/verify", "/api/learn")):
        payload = result.get("payload", {})
        if result.get("status") == 200 and payload.get("decision_id"):
            results.append(measure(args.base, path, {"decision_id": payload["decision_id"],
                "actual_action": payload["action"], "reason_code": "supplier_preference"}))
    with ThreadPoolExecutor(max_workers=7) as pool:
        futures = [pool.submit(measure, args.base, path) for path in GETS]
        futures.append(pool.submit(measure, args.base, "/api/score", BODY))
        results.extend(future.result() for future in futures)
    for base in (args.base, "http://127.0.0.1:5175"):
        results.append(measure(base, "/api/health"))
        results.append(measure(base, "/api/score", BODY))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
