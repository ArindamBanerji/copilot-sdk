"""Profile real AGE I/O and compare identical ASGI routes with/without middleware."""
from __future__ import annotations

import argparse
import importlib
import json
import os
import statistics
import sys
import threading
import time
from pathlib import Path
from types import FrameType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT.parent / "ci-platform")]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("domain", choices=("purchasing", "trading", "dataops", "soc", "s2p"))
    parser.add_argument("output", type=Path)
    parser.add_argument("--writes", action="store_true")
    parser.add_argument("--middleware-only", action="store_true")
    args = parser.parse_args()
    import demo
    config = next(item for item in demo.COPILOTS if item["name"].lower() == args.domain)
    os.environ.update(config["env"])
    os.environ["DEMO_NO_RESEED"] = "1"
    if args.domain == "soc":
        os.environ["SOC_DEMO_MODE"] = "true"  # Match demo.py's explicit local launch.
    sys.path.insert(0, str(config["be_path"]))
    imported_at = time.perf_counter()
    app = importlib.import_module("app.main").app
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from copilot_sdk.scoring import CompoundingScorer
    from scripts.mutable_flow_probe import BODY
    result: dict[str, Any] = {"domain": args.domain, "import_ms": (time.perf_counter() - imported_at) * 1000}
    result["middleware"] = [{"class": item.cls.__name__, "dispatch": getattr(item.kwargs.get("dispatch"), "__qualname__", None)} for item in app.user_middleware]

    @app.get("/api/context/__drift_ping")
    async def ping() -> dict[str, bool]:
        return {"ok": True}

    bare = FastAPI()
    bare.router.routes = app.router.routes
    bare.state = app.state
    # The middleware-only mode avoids running external app startup workflows.
    # It still executes each real registered middleware on an identical route.
    if args.middleware_only:
        full_app = FastAPI()
        full_app.router.routes = app.router.routes
        full_app.state = app.state
        full_app.user_middleware = app.user_middleware
    else:
        full_app = app
    with TestClient(full_app) as full, TestClient(bare) as stripped:
        if not args.middleware_only:
            full.get("/api/fingerprint")
        pairs = []
        for _ in range(20):
            row = []
            for client in (full, stripped):
                started = time.perf_counter()
                response = client.get("/api/context/__drift_ping", headers={"Origin": "http://127.0.0.1:5175"})
                assert response.status_code == 200, response.text
                row.append((time.perf_counter() - started) * 1000)
            pairs.append(row)
        result["middleware_ms"] = {"full_median": statistics.median(row[0] for row in pairs),
                                   "bare_median": statistics.median(row[1] for row in pairs),
                                   "paired_delta_median": statistics.median(row[0] - row[1] for row in pairs), "samples": pairs}
        if args.middleware_only:
            args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
            print(json.dumps(result))
            return
        graph = getattr(app.state, f"{args.domain}_selected_graph_store")
        started = time.perf_counter()
        recreated = CompoundingScorer.from_preset(args.domain, graph_store=graph, evolve=True, consolidation_enabled=True, profile="production")
        result["scorer_creation_ms"] = (time.perf_counter() - started) * 1000
        result["scorer_type"] = type(recreated).__name__
        rows: list[dict[str, Any]] = []
        active: dict[int, tuple[float, str, list[str]]] = {}
        enabled = False

        def trace(frame: FrameType, event: str, arg: Any) -> None:
            if not enabled or frame.f_code.co_name not in {"_sync_execute", "_execute_cypher_on_connection"}:
                return
            key = id(frame)
            if event == "call":
                stack = []
                caller = frame.f_back
                while caller is not None:
                    if "claude_projects" in caller.f_code.co_filename:
                        stack.append(f"{Path(caller.f_code.co_filename).name}:{caller.f_code.co_name}")
                    caller = caller.f_back
                query = str(frame.f_locals.get("query") or frame.f_locals.get("cypher") or "")
                active[key] = (time.perf_counter(), query, stack)
            elif event == "return" and key in active:
                began, query, stack = active.pop(key)
                rows.append({"ms": (time.perf_counter() - began) * 1000, "query": query, "stack": stack})

        threading.setprofile(trace)
        # Existing worker threads inherit no new profile; a fresh TestClient
        # creates the ASGI and worker threads while this profiler is installed.
        with TestClient(app) as profiled:
            requests: list[dict[str, Any]] = []
            sequence: list[tuple[str, dict[str, Any] | None]] = [("/api/evolution/variants", None)]
            if args.writes:
                sequence.extend([("/api/score", BODY), ("/api/score", BODY)])
            index = 0
            while index < len(sequence):
                path, body = sequence[index]
                rows.clear()
                enabled = True
                started = time.perf_counter()
                response = profiled.get(path) if body is None else profiled.post(path, json=body)
                enabled = False
                payload = response.json()
                requests.append({"path": path, "ms": (time.perf_counter() - started) * 1000, "status": response.status_code,
                                 "bytes": len(response.content), "payload": payload, "queries": list(rows)})
                if path == "/api/score" and response.status_code == 200:
                    endpoint = "/api/purchasing/verify" if index == 1 else "/api/learn"
                    sequence.append((endpoint, {"decision_id": payload["decision_id"], "actual_action": payload["action"], "reason_code": "supplier_preference"}))
                index += 1
            result["requests"] = requests
        threading.setprofile(None)
    args.output.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps({**result, "requests": [{"path": row["path"], "ms": row["ms"], "status": row["status"], "queries": len(row["queries"])} for row in result["requests"]]}, default=str))


if __name__ == "__main__":
    main()
