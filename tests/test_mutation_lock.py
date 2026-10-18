from __future__ import annotations

import threading
import time
import inspect

import pytest

from copilot_sdk.backend.counterfactual_router import create_counterfactual_router
from copilot_sdk.backend.response_materializer import ResponseMaterializer
from copilot_sdk.scoring.mutation_lock import get_mutation_lock, serialize_mutation
from copilot_sdk.state.invalidation import invalidate_cache_event, register_tab_state_cache
from copilot_sdk.state.tab_state_cache import TabStateCache


def register(cache: TabStateCache, key: str, compute, **kwargs):
    from pydantic import RootModel
    from typing import Any

    class DemoPayload(RootModel[Any]):
        pass

    url = kwargs.pop("url", f"/api/{key}")
    cache.register(key, compute, schema=DemoPayload, service_fn=compute, url=url, **kwargs)


def test_concurrent_score_calls_serialized() -> None:
    order: list[str] = []
    active = 0
    max_active = 0
    guard = threading.Lock()

    @serialize_mutation("lock-test-score")
    def score_decision(label: str) -> None:
        nonlocal active, max_active
        with guard:
            active += 1
            max_active = max(max_active, active)
            order.append(f"start-{label}")
        time.sleep(0.05)
        with guard:
            order.append(f"end-{label}")
            active -= 1

    threads = [
        threading.Thread(target=score_decision, args=("a",)),
        threading.Thread(target=score_decision, args=("b",)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=1.0)

    assert max_active == 1
    assert order in (
        ["start-a", "end-a", "start-b", "end-b"],
        ["start-b", "end-b", "start-a", "end-a"],
    )


def _increment(values: dict[str, int], key: str) -> dict[str, int]:
    values[key] += 1
    return {"value": values[key]}


def test_concurrent_score_and_get_not_blocked() -> None:
    lock = get_mutation_lock("lock-test-read")
    lock.acquire()
    try:
        start = time.perf_counter()

        def fingerprint() -> dict[str, bool]:
            return {"ok": True}

        assert fingerprint() == {"ok": True}
        assert (time.perf_counter() - start) < 0.05
    finally:
        lock.release()


def test_lock_is_per_domain() -> None:
    trading_lock = get_mutation_lock("lock-test-trading")
    purchasing_lock = get_mutation_lock("lock-test-purchasing")

    trading_lock.acquire()
    try:
        assert purchasing_lock.acquire(blocking=False)
        purchasing_lock.release()
    finally:
        trading_lock.release()


def test_lock_released_on_exception() -> None:
    calls = 0

    @serialize_mutation("lock-test-exception")
    def mutate(raise_error: bool) -> int:
        nonlocal calls
        calls += 1
        if raise_error:
            raise RuntimeError("boom")
        return calls

    with pytest.raises(RuntimeError):
        mutate(True)

    assert mutate(False) == 2


def test_decorator_preserves_handler_signature() -> None:
    def handler(item_id: str, quantity: int = 1) -> dict[str, object]:
        return {"item_id": item_id, "quantity": quantity}

    wrapped = serialize_mutation("lock-test-signature")(handler)

    signature = inspect.signature(wrapped)
    assert list(signature.parameters) == ["item_id", "quantity"]
    assert signature.parameters["item_id"].annotation is str
    assert signature.parameters["quantity"].annotation is int
    assert signature.parameters["quantity"].default == 1


def test_invalidation_inside_decorator_lock() -> None:
    values = {"critical": 0, "standard": 0}
    cache = TabStateCache("lock-test-invalidate")
    register(
        cache,
        "critical",
        lambda: _increment(values, "critical"),
        invalidated_by=["score"],
        critical=True,
        tier="CRITICAL",
    )
    register(
        cache,
        "standard",
        lambda: _increment(values, "standard"),
        invalidated_by=["score"],
        tier="STANDARD",
    )
    register_tab_state_cache(cache)
    import asyncio

    asyncio.run(cache.warm_up())

    @serialize_mutation("lock-test-invalidate", event="score")
    def mutate() -> dict[str, bool]:
        return {"ok": True}

    assert mutate() == {"ok": True}
    assert cache.get_entry("critical").data == {"value": 2}
    assert cache.get_entry("standard") is None


def test_fail_safe_deletes_on_cache_error(monkeypatch) -> None:
    cache = TabStateCache("lock-test-failsafe")
    register(cache, "critical", lambda: {"value": 1}, invalidated_by=["score"], critical=True, tier="CRITICAL")
    register(cache, "standard", lambda: {"value": 2}, invalidated_by=["score"], tier="STANDARD")
    register_tab_state_cache(cache)
    import asyncio

    asyncio.run(cache.warm_up())

    def fail_recompute(event: str) -> list[str]:
        raise RuntimeError("boom")

    monkeypatch.setattr(cache, "recompute_critical", fail_recompute)

    @serialize_mutation("lock-test-failsafe", event="score")
    def mutate() -> dict[str, bool]:
        return {"ok": True}

    assert mutate() == {"ok": True}
    assert cache.get_entry("critical") is None
    assert cache.get_entry("standard") is None


def test_invalidate_cache_event_acquires_lock() -> None:
    values = {"critical": 0, "standard": 0}
    cache = TabStateCache("lock-test-event")
    register(
        cache,
        "critical",
        lambda: _increment(values, "critical"),
        invalidated_by=["regime_break"],
        critical=True,
        tier="CRITICAL",
    )
    register(cache, "standard", lambda: {"value": 1}, invalidated_by=["regime_break"], tier="STANDARD")
    register_tab_state_cache(cache)
    import asyncio

    asyncio.run(cache.warm_up())

    invalidate_cache_event("lock-test-event", "regime_break")

    assert cache.get_entry("critical").data == {"value": 2}
    assert cache.get_entry("standard") is None


def test_out_of_band_invalidation_also_invalidates_materializer() -> None:
    cache = TabStateCache("lock-test-materializer")
    register(
        cache,
        "critical",
        lambda: {"value": 1},
        invalidated_by=["score"],
        critical=True,
        tier="CRITICAL",
    )

    class Materializer:
        def __init__(self) -> None:
            self.invalidations = 0

        def invalidate_mutation(self) -> None:
            self.invalidations += 1

    materializer = Materializer()
    register_tab_state_cache(
        cache,
        materializer_provider=lambda: materializer,
    )

    invalidate_cache_event("lock-test-materializer", "score")

    assert materializer.invalidations == 1


def test_mutation_invalidation_prevents_tabcache_recache() -> None:
    class Store:
        value = 1

        def get_all_decisions(self, domain: str):
            return [{"value": self.value}]

        def get_verified_decisions(self, domain: str):
            return []

    store = Store()
    entered = threading.Event()
    release = threading.Event()
    block_refresh = False

    def compute_materialized(shared):
        if block_refresh:
            entered.set()
            assert release.wait(2.0)
        return shared["decisions"][0]

    materializer = ResponseMaterializer(
        "lock-test-tabcache-integration",
        lambda: store,
        {"summary": compute_materialized},
    )
    materializer.refresh()
    cache = TabStateCache("lock-test-tabcache-integration")
    register(
        cache,
        "summary",
        lambda: materializer.get_or_refresh("summary"),
        invalidated_by=["score"],
        critical=True,
        tier="CRITICAL",
    )
    register_tab_state_cache(
        cache,
        materializer_provider=lambda: materializer,
    )
    import asyncio

    asyncio.run(cache.warm_up())
    assert cache.get_entry("summary").data == {"value": 1}

    store.value = 2
    materializer.invalidate()
    block_refresh = True
    refresh_thread = threading.Thread(target=materializer.refresh)
    refresh_thread.start()
    assert entered.wait(1.0)

    store.value = 3
    invalidation_thread = threading.Thread(
        target=invalidate_cache_event,
        args=("lock-test-tabcache-integration", "score"),
    )
    invalidation_thread.start()
    assert materializer.get("summary") is None
    release.set()
    refresh_thread.join(2.0)
    invalidation_thread.join(2.0)

    assert not refresh_thread.is_alive()
    assert not invalidation_thread.is_alive()
    assert materializer.get("summary") == {"value": 3}
    assert cache.get_entry("summary").data == {"value": 3}
    cached = asyncio.run(cache.get("summary"))
    assert cached["summary"]["data"] == {"value": 3}


def test_readonly_post_not_locked() -> None:
    router = create_counterfactual_router("trading", prefix="/api/trading/score")
    endpoint = next(
        route.endpoint
        for route in router.routes
        if getattr(route, "path", "") == "/api/trading/score/counterfactual"
    )

    assert getattr(endpoint, "__mutation_lock_domain__", None) is None
