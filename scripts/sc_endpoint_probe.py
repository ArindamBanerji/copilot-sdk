"""Measure real HTTP latency and retain response bodies for parity checks."""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

ENDPOINTS = (
    "/api/self/decisions", "/api/self/audit-trail", "/api/self/accuracy-alerts",
    "/api/self/rule-lifecycle/active", "/api/self/centroid-timeline",
    "/api/self/accuracy-by-category", "/api/context/today-summary", "/api/trajectory",
)


def measure(base: str, endpoint: str) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(base + endpoint, timeout=30) as response:
            body = response.read()
        elapsed = (time.perf_counter() - started) * 1000
        payload = json.loads(body)
        return {"endpoint": endpoint, "ms": round(elapsed, 3), "bytes": len(body),
                "payload": payload}
    except Exception as error:
        return {"endpoint": endpoint, "ms": round((time.perf_counter() - started) * 1000, 3),
                "error": str(error)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--base", default="http://127.0.0.1:8020")
    parser.add_argument("--waves", type=int, default=0)
    args = parser.parse_args()
    if args.waves:
        with ThreadPoolExecutor(max_workers=len(ENDPOINTS) * args.waves) as pool:
            results = list(pool.map(lambda endpoint: measure(args.base, endpoint),
                                    ENDPOINTS * args.waves))
    else:
        results = [measure(args.base, endpoint) for endpoint in ENDPOINTS]
    for result in results:
        payload = result.get("payload", {})
        count = (sum(len(value) if isinstance(value, list) else 1 for value in payload.values())
                 if isinstance(payload, dict) else len(payload) if isinstance(payload, list) else 1)
        print(json.dumps({key: value for key, value in result.items() if key != "payload"}
                         | {"entries": count, "total": payload.get("total") if isinstance(payload, dict) else None}))
    results.append(measure(args.base, "/api/health"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
