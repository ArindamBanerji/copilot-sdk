from __future__ import annotations

import asyncio
import concurrent.futures
import importlib
import inspect
import re
import threading
import time
from pathlib import Path
from typing import Any

from pydantic import RootModel
from starlette.requests import Request

from copilot_sdk.state.cached_quasi_static import cached_quasi_static
from copilot_sdk.state.cached_static import cached_static
from copilot_sdk.state.invalidation import register_tab_state_cache
from copilot_sdk.state.tab_state_cache import TabStateCache


class DemoPayload(RootModel[Any]):
    pass


def run(coro):
    return asyncio.run(coro)


def register(cache: TabStateCache, key: str, compute, **kwargs):
    cache.register(key, compute, schema=DemoPayload, service_fn=compute, url=f"/api/{key}", **kwargs)


def request_for(path: str, query: str = "") -> Request:
    return Request({
        "type": "http",
        "method": "GET",
        "path": path,
        "query_string": query.encode("ascii"),
        "headers": [],
    })


def test_cached_static_returns_cached_on_hit():
    cache = TabStateCache("cached-hit")
    register(cache, "demo", lambda: {"value": "cached"})
    register_tab_state_cache(cache)
    run(cache.warm_up())
    calls = {"count": 0}

    @cached_static("demo", copilot="cached-hit")
    def handler(request: Request) -> dict[str, str]:
        calls["count"] += 1
        return {"value": "handler"}

    assert handler(request_for("/api/demo")) == {"value": "cached"}
    assert calls["count"] == 0


def test_cached_static_calls_handler_on_miss():
    cache = TabStateCache("cached-miss")
    register(cache, "demo", lambda: {"value": "warm"})
    register_tab_state_cache(cache)
    calls = {"count": 0}

    @cached_static("demo", copilot="cached-miss")
    def handler(request: Request) -> dict[str, str]:
        calls["count"] += 1
        return {"value": "handler"}

    assert handler(request_for("/api/demo")) == {"value": "handler"}
    assert calls["count"] == 1


def test_cached_static_populates_cache_on_miss():
    cache = TabStateCache("cached-populate")
    register(cache, "demo", lambda: {"value": "warm"}, tier="STANDARD")
    register_tab_state_cache(cache)

    @cached_static("demo", copilot="cached-populate")
    def handler(request: Request) -> dict[str, str]:
        return {"value": "handler"}

    assert handler(request_for("/api/demo")) == {"value": "handler"}
    entry = cache.get_entry("demo")
    assert entry is not None
    assert entry.status == "ready"
    assert entry.data == {"value": "handler"}


def test_hot_miss_does_not_populate_cache():
    cache = TabStateCache("hot-miss")
    source = {"value": "warm"}
    register(cache, "demo", lambda: {"value": source["value"]}, tier="CRITICAL", critical=True)
    register_tab_state_cache(cache)

    @cached_static("demo", copilot="hot-miss")
    def handler(request: Request) -> dict[str, str]:
        return {"value": "handler"}

    assert handler(request_for("/api/demo")) == {"value": "handler"}
    entry = cache.get_entry("demo")
    assert entry is not None
    assert entry.status == "missing"
    assert entry.data is None

    run(cache.warm_up())
    assert cache.get_entry("demo").data == {"value": "warm"}
    source["value"] = "invalidated"
    run(cache.invalidate("score"))
    assert handler(request_for("/api/demo")) == {"value": "invalidated"}


def test_cold_miss_populates_once():
    cache = TabStateCache("cold-miss")
    register(cache, "demo", lambda: {"value": "warm"}, tier="COLD")
    register_tab_state_cache(cache)
    source = {"value": "first"}

    @cached_static("demo", copilot="cold-miss")
    def handler(request: Request) -> dict[str, str]:
        return {"value": source["value"]}

    assert handler(request_for("/api/demo")) == {"value": "first"}
    assert cache.get_entry("demo").data == {"value": "first"}
    source["value"] = "second"
    assert handler(request_for("/api/demo")) == {"value": "first"}
    assert cache.get_entry("demo").data == {"value": "first"}


def test_standard_key_lazy_recompute_on_read():
    cache = TabStateCache("standard-lazy")
    source = {"value": "warm"}
    register(
        cache,
        "demo",
        lambda: {"value": source["value"]},
        invalidated_by=["score"],
        tier="STANDARD",
    )
    register_tab_state_cache(cache)
    run(cache.warm_up())
    source["value"] = "lazy"
    run(cache.invalidate("score"))

    assert cache.get_entry("demo") is None

    @cached_static("demo", copilot="standard-lazy")
    def handler(request: Request) -> dict[str, str]:
        return {"value": source["value"]}

    assert handler(request_for("/api/demo")) == {"value": "lazy"}
    assert cache.get_entry("demo").data == {"value": "lazy"}


def test_single_flight_deduplicates_concurrent_misses():
    cache = TabStateCache("single-flight")
    register(cache, "demo", lambda: {"value": "warm"}, tier="STANDARD")
    register_tab_state_cache(cache)
    calls = {"count": 0}
    call_lock = threading.Lock()

    @cached_static("demo", copilot="single-flight")
    def handler(request: Request) -> dict[str, int]:
        with call_lock:
            calls["count"] += 1
            current = calls["count"]
        time.sleep(0.05)
        return {"value": current}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: handler(request_for("/api/demo")), range(4)))

    assert calls["count"] == 1
    assert results == [{"value": 1}] * 4
    assert cache.get_entry("demo").data == {"value": 1}


def test_single_flight_timeout_falls_through(monkeypatch):
    cached_static_module = importlib.import_module("copilot_sdk.state.cached_static")
    monkeypatch.setattr(cached_static_module, "_INFLIGHT_TIMEOUT_SECONDS", 0.05)
    cache = TabStateCache("single-flight-timeout")
    register(cache, "demo", lambda: {"value": "warm"}, tier="STANDARD")
    register_tab_state_cache(cache)
    calls = {"count": 0}
    call_lock = threading.Lock()

    @cached_static("demo", copilot="single-flight-timeout")
    def handler(request: Request) -> dict[str, int]:
        with call_lock:
            calls["count"] += 1
            current = calls["count"]
        if current == 1:
            time.sleep(0.2)
        return {"value": current}

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(handler, request_for("/api/demo"))
        time.sleep(0.01)
        second = pool.submit(handler, request_for("/api/demo"))
        results = [first.result(), second.result()]

    assert calls["count"] == 2
    assert {"value": 2} in results


def test_cached_static_miss_is_current_behavior_without_cache():
    calls = {"count": 0}

    @cached_static("demo", copilot="missing-cache")
    def handler() -> dict[str, str]:
        calls["count"] += 1
        return {"value": "handler"}

    assert handler() == {"value": "handler"}
    assert calls["count"] == 1


def test_category_a_miss_acquires_lock() -> None:
    cache = TabStateCache("category-a-lock")
    register(cache, "demo", lambda: {"value": "warm"}, reads_scorer=True, tier="STANDARD")
    register_tab_state_cache(cache)
    lock = __import__("copilot_sdk.scoring.mutation_lock", fromlist=["get_mutation_lock"]).get_mutation_lock("category-a-lock")
    lock.acquire()
    result: list[dict[str, str]] = []

    @cached_static("demo", copilot="category-a-lock")
    def handler(request: Request) -> dict[str, str]:
        result.append({"value": "handler"})
        return {"value": "handler"}

    thread = threading.Thread(target=lambda: handler(request_for("/api/demo")))
    thread.start()
    try:
        time.sleep(0.05)
        assert result == []
    finally:
        lock.release()
    thread.join(timeout=1.0)
    assert result == [{"value": "handler"}]


def test_category_b_miss_does_not_acquire_lock() -> None:
    cache = TabStateCache("category-b-lock")
    register(cache, "demo", lambda: {"value": "warm"}, reads_scorer=False, tier="STANDARD")
    register_tab_state_cache(cache)
    lock = __import__("copilot_sdk.scoring.mutation_lock", fromlist=["get_mutation_lock"]).get_mutation_lock("category-b-lock")
    lock.acquire()
    try:
        calls = {"count": 0}

        @cached_static("demo", copilot="category-b-lock")
        def handler(request: Request) -> dict[str, str]:
            calls["count"] += 1
            return {"value": "handler"}

        assert handler(request_for("/api/demo")) == {"value": "handler"}
        assert calls["count"] == 1
    finally:
        lock.release()


def test_decorator_order_preserves_signature():
    def handler(category: str, limit: int = 50) -> dict[str, Any]:
        return {"category": category, "limit": limit}

    wrapped = cached_static("demo", copilot="signature")(handler)

    assert inspect.signature(wrapped) == inspect.signature(handler)
    assert wrapped.__name__ == handler.__name__


def test_no_cached_static_on_parameterized_handlers():
    root = Path(__file__).resolve().parents[1]
    paths = [
        root / "apps" / "trading" / "backend" / "app",
        root / "copilot_sdk" / "backend",
    ]
    offenders: list[str] = []
    for base in paths:
        for path in base.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            pattern = re.compile(
                r"(?P<decorators>(?:\s*@(?:router|app)\.get[^\n]*\n|\s*@cached_static[^\n]*\n)+)"
                r"\s*def\s+(?P<name>\w+)\((?P<params>[^)]*)\)",
                re.M,
            )
            for match in pattern.finditer(source):
                decorators = match.group("decorators")
                if "@cached_static" not in decorators:
                    continue
                params = [
                    item.strip()
                    for item in match.group("params").split(",")
                    if item.strip()
                ]
                non_request_params = [
                    item
                    for item in params
                    if not item.startswith("request:")
                    and not item.startswith("request ")
                    and item != "request"
                ]
                if non_request_params:
                    offenders.append(f"{path.relative_to(root)}:{match.group('name')}({', '.join(non_request_params)})")

    assert offenders == []


def test_quasi_static_hit_returns_cached():
    cache = TabStateCache("quasi-hit")
    register(
        cache,
        "correlation",
        lambda: {"value": "window-20"},
        category="QUASI_STATIC",
        default_params={"window": "20"},
    )
    register_tab_state_cache(cache)
    run(cache.warm_up())
    calls = {"count": 0}

    @cached_quasi_static("correlation", lambda request: f"window={request.query_params.get('window', '20')}", copilot="quasi-hit")
    def handler(request: Request) -> dict[str, str]:
        calls["count"] += 1
        return {"value": "handler"}

    assert handler(request_for("/api/trading/correlation", "window=20")) == {"value": "window-20"}
    assert calls["count"] == 0


def test_quasi_static_non_default_computes_once():
    cache = TabStateCache("quasi-non-default")
    register(
        cache,
        "correlation",
        lambda: {"value": "window-20"},
        category="QUASI_STATIC",
        default_params={"window": "20"},
    )
    register_tab_state_cache(cache)
    run(cache.warm_up())
    calls = {"count": 0}

    @cached_quasi_static("correlation", lambda request: f"window={request.query_params.get('window', '20')}", copilot="quasi-non-default")
    def handler(request: Request) -> dict[str, str]:
        calls["count"] += 1
        return {"value": "window-50"}

    request = request_for("/api/trading/correlation", "window=50")
    assert handler(request) == {"value": "window-50"}
    assert handler(request) == {"value": "window-50"}
    assert calls["count"] == 1


def test_quasi_static_invalidation_clears_all_variants():
    cache = TabStateCache("quasi-invalidate")
    source = {"value": "default-1"}
    register(
        cache,
        "correlation",
        lambda: {"value": source["value"]},
        category="QUASI_STATIC",
        default_params={"window": "20"},
        critical=True,
        tier="CRITICAL",
    )
    register_tab_state_cache(cache)
    run(cache.warm_up())

    @cached_quasi_static("correlation", lambda request: f"window={request.query_params.get('window', '20')}", copilot="quasi-invalidate")
    def handler(request: Request) -> dict[str, str]:
        return {"value": "window-50"}

    assert handler(request_for("/api/trading/correlation", "window=50")) == {"value": "window-50"}
    assert cache.get_entry("correlation", "window=50") is not None
    source["value"] = "default-2"

    run(cache.invalidate("score"))

    assert cache.get_entry("correlation", "window=20").data == {"value": "default-2"}
    assert cache.get_entry("correlation", "window=50") is None


def test_fast_endpoint_not_quasi_cached():
    cache = TabStateCache("quasi-fast")
    register(cache, "fast", lambda: {"value": "static"})
    register_tab_state_cache(cache)
    calls = {"count": 0}

    @cached_quasi_static("fast", lambda request: "default", copilot="quasi-fast")
    def handler(request: Request) -> dict[str, int]:
        calls["count"] += 1
        return {"value": calls["count"]}

    request = request_for("/api/fast")
    assert handler(request) == {"value": 1}
    assert handler(request) == {"value": 2}
    assert calls["count"] == 2
