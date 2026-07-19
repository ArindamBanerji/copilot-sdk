from __future__ import annotations

import asyncio
import logging
import threading
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from pydantic import RootModel
import pytest

from copilot_sdk.state import TabStateCache, scan_mutation_routes


class DemoPayload(RootModel[Any]):
    pass


def run(coro):
    return asyncio.run(coro)


def register(cache: TabStateCache, key: str, compute, **kwargs):
    url = kwargs.pop("url", f"/api/{key}")
    cache.register(key, compute, schema=DemoPayload, service_fn=compute, url=url, **kwargs)


def test_register_warm_up_and_get_cached_values():
    calls = {"a": 0}
    cache = TabStateCache("demo")

    def compute():
        calls["a"] += 1
        return {"value": calls["a"]}

    register(cache, "a", compute)

    payload = run(cache.get(["a"]))
    second = run(cache.get(["a"]))

    assert payload["a"]["data"] == {"value": 1}
    assert second["a"]["data"] == {"value": 1}
    assert calls["a"] == 1


def test_keyspec_has_url_field():
    cache = TabStateCache("demo")
    register(cache, "test", lambda: {"value": 1}, url="/api/test")

    assert cache.registrations["test"].url == "/api/test"


def test_unknown_dynamic_and_duplicate_keys():
    cache = TabStateCache("demo")
    register(cache, "a", lambda: {"value": 1})
    cache.register_dynamic("ticker/{ticker}")

    payload = run(cache.get(["a", "a", "ticker/{ticker}", "missing"]))

    assert list(payload) == ["a", "ticker/{ticker}", "missing"]
    assert payload["ticker/{ticker}"]["status"] == "dynamic"
    assert payload["missing"]["status"] == "unknown_key"


def test_get_keys_for_event():
    cache = TabStateCache("demo")
    register(cache, "score-a", lambda: {"value": 1}, invalidated_by=["score"])
    register(cache, "score-b", lambda: {"value": 2}, invalidated_by=["score", "learn"])
    register(cache, "learn-only", lambda: {"value": 3}, invalidated_by=["learn"], tier="COLD")

    assert cache.get_keys_for_event("score") == ["score-a", "score-b"]


def test_tiered_invalidation_critical_standard_and_cold():
    cache = TabStateCache("demo")
    register(cache, "critical-a", lambda: {"value": 1}, tier="CRITICAL")
    register(cache, "standard-a", lambda: {"value": 2}, invalidated_by=["score"], tier="STANDARD")
    register(cache, "standard-b", lambda: {"value": 3}, invalidated_by=["learn"], tier="STANDARD")
    register(cache, "cold-a", lambda: {"value": 3}, tier="COLD")

    assert cache.get_keys_for_event("score") == ["critical-a", "standard-a"]
    assert cache.get_keys_for_event("learn") == ["critical-a", "standard-b"]
    assert cache.get_keys_for_event("reset") == ["critical-a", "standard-a", "standard-b", "cold-a"]


def test_register_rejects_missing_schema_duplicate_and_dynamic_category():
    cache = TabStateCache("demo")
    compute = lambda: {"value": 1}

    with pytest.raises(TypeError, match="requires a BaseModel schema"):
        cache.register("missing-schema", compute, service_fn=compute)

    register(cache, "a", compute)

    with pytest.raises(ValueError, match="Duplicate key registration"):
        register(cache, "a", compute)

    with pytest.raises(ValueError, match="register_dynamic"):
        cache.register("ticker/{ticker}", compute, category="DYNAMIC", schema=DemoPayload, service_fn=compute)


def test_invalidate_recomputes_only_registered_event_keys():
    values = {"a": 0, "b": 0}
    cache = TabStateCache("demo")
    register(cache, "a", lambda: {"value": values.__setitem__("a", values["a"] + 1) or values["a"]}, invalidated_by=["score"], critical=True)
    register(cache, "b", lambda: {"value": values.__setitem__("b", values["b"] + 1) or values["b"]}, invalidated_by=["learn"], tier="COLD")
    run(cache.warm_up())

    result = run(cache.invalidate("score"))

    assert result["wave1"] == ["a"]
    assert run(cache.get(["a", "b"]))["a"]["data"] == {"value": 2}
    assert values == {"a": 2, "b": 1}


def test_standard_key_deleted_on_mutation():
    value = {"n": 0}
    cache = TabStateCache("demo")

    def compute():
        value["n"] += 1
        return {"value": value["n"]}

    register(cache, "standard", compute, invalidated_by=["score"], tier="STANDARD")

    async def scenario():
        await cache.warm_up()
        result = await cache.invalidate("score")
        payload = await cache.get(["standard"])
        return result, payload

    result, payload = run(scenario())

    assert result["deleted"] == ["standard"]
    assert result["wave2"] == []
    assert cache.get_entry("standard") is None
    assert payload["standard"]["status"] == "missing"
    assert payload["standard"]["error"] == "not materialized"
    assert value["n"] == 1


def test_error_isolation_and_invalidated_error():
    cache = TabStateCache("demo")
    register(cache, "ok", lambda: {"ok": True}, invalidated_by=["score"], critical=True)
    register(cache, "bad", lambda: (_ for _ in ()).throw(RuntimeError("boom")), invalidated_by=["score"], critical=True)

    run(cache.warm_up())
    run(cache.invalidate("score"))
    payload = run(cache.get(["ok", "bad"]))

    assert payload["ok"]["status"] == "ready"
    assert payload["bad"]["status"] == "invalidated_error"
    assert payload["bad"]["data"] is None


def test_version_race_discards_older_result():
    cache = TabStateCache("demo")
    release = asyncio.Event()
    counter = {"n": 0}

    async def compute():
        counter["n"] += 1
        current = counter["n"]
        if current == 2:
            await release.wait()
        return {"value": current}

    register(cache, "a", compute, invalidated_by=["score", "verify"], critical=True)

    async def scenario():
        await cache.warm_up()
        first = asyncio.create_task(cache.invalidate("score"))
        await asyncio.sleep(0)
        second = asyncio.create_task(cache.invalidate("verify"))
        release.set()
        await asyncio.gather(first, second)
        return await cache.get(["a"])

    payload = run(scenario())

    assert payload["a"]["data"] == {"value": 3}


def test_memory_guards_reject_large_payload():
    cache = TabStateCache("demo", warn_bytes=10, reject_bytes=20)
    register(cache, "large", lambda: {"value": "x" * 100}, invalidated_by=["score"], critical=True)

    payload = run(cache.get(["large"]))

    assert payload["large"]["status"] == "missing"
    assert "exceeds" in payload["large"]["error"]


def test_warmup_computes_static_only():
    cache = TabStateCache("demo")
    calls = {"static": 0}
    register(cache, "static", lambda: calls.__setitem__("static", calls["static"] + 1) or {"ok": True})
    cache.register_dynamic("ticker/{ticker}")

    run(cache.warm_up())
    payload = run(cache.get(["static", "ticker/{ticker}"]))

    assert calls["static"] == 1
    assert payload["static"]["data"] == {"ok": True}
    assert payload["ticker/{ticker}"]["data"] is None
    assert payload["ticker/{ticker}"]["status"] == "dynamic"


def test_cold_warmup_does_not_overwrite_preseed():
    cache = TabStateCache("demo")
    calls = {"a": 0, "b": 0}
    register(cache, "a", lambda: calls.__setitem__("a", calls["a"] + 1) or {"value": "computed-a"})
    register(cache, "b", lambda: calls.__setitem__("b", calls["b"] + 1) or {"value": "computed-b"})
    cache._entries["a"].data = {"value": "preseeded-a"}
    cache._entries["a"].status = "ready"
    cache._entries["a"].computed_at = time.time()

    payload = run(cache.get(["a", "b"]))

    assert payload["a"]["data"] == {"value": "preseeded-a"}
    assert payload["b"]["data"] == {"value": "computed-b"}
    assert calls == {"a": 0, "b": 1}


def test_quasi_static_warm_uses_default_params():
    cache = TabStateCache("demo")
    register(
        cache,
        "correlation",
        lambda: {"value": "window-20"},
        category="QUASI_STATIC",
        default_params={"window": "20"},
    )

    run(cache.warm_up())

    assert cache.get_entry("correlation", "window=20").data == {"value": "window-20"}
    assert cache.get_entry("correlation", "window=50") is None


def test_sync_compute_runs_directly_for_small_wave_budget():
    cache = TabStateCache("demo")
    thread_ids: list[int] = []

    def compute():
        thread_ids.append(threading.get_ident())
        return {"value": "done"}

    register(cache, "slow", compute)

    async def scenario():
        event_loop_thread = threading.get_ident()
        await cache.warm_up()
        return event_loop_thread

    event_loop_thread = run(scenario())

    assert thread_ids == [event_loop_thread]
    assert cache.get_entry("slow").data == {"value": "done"}


def test_warmup_chunks_batches_of_5(monkeypatch):
    cache = TabStateCache("demo")
    for index in range(6):
        register(cache, f"key-{index}", lambda index=index: {"index": index})

    sleep_calls: list[float] = []
    original_sleep = asyncio.sleep

    async def fake_sleep(delay: float):
        sleep_calls.append(delay)
        await original_sleep(0)

    monkeypatch.setattr("copilot_sdk.state.tab_state_cache.asyncio.sleep", fake_sleep)

    run(cache.warm_up())
    payload = run(cache.get([f"key-{index}" for index in range(6)]))

    assert len(payload) == 6
    assert len(sleep_calls) == 2


def test_standard_invalidation_deletes_without_background_batches(monkeypatch):
    cache = TabStateCache("demo")
    values = {f"key-{index}": 0 for index in range(5)}
    for key in values:
        register(
            cache,
            key,
            lambda key=key: values.__setitem__(key, values[key] + 1) or {"value": values[key]},
            invalidated_by=["score"],
            critical=False,
        )
    run(cache.warm_up())

    sleep_calls: list[float] = []

    async def fake_sleep(delay: float):
        sleep_calls.append(delay)
        return None

    async def scenario():
        with monkeypatch.context() as patch:
            patch.setattr("copilot_sdk.state.tab_state_cache.asyncio.sleep", fake_sleep)
            result = await cache.invalidate("score")
        return result

    result = run(scenario())

    assert sorted(result["deleted"]) == sorted(values)
    assert result["wave2"] == []
    assert sleep_calls == []
    assert all(cache.get_entry(key) is None for key in values)
    assert values == {f"key-{index}": 1 for index in range(5)}


def test_critical_keys_still_wave1_recomputed():
    cache = TabStateCache("demo")
    calls = {"count": 0}

    def compute():
        calls["count"] += 1
        return {"value": calls["count"]}

    register(cache, "critical", compute, invalidated_by=["score"], critical=True, tier="CRITICAL")

    async def scenario():
        await cache.warm_up()
        result = await cache.invalidate("score")
        payload = await cache.get(["critical"])
        return result, payload

    result, payload = run(scenario())

    assert result["wave1"] == ["critical"]
    assert result["deleted"] == []
    assert payload["critical"]["status"] == "ready"
    assert payload["critical"]["data"] == {"value": 2}


def test_cold_keys_not_deleted_on_non_reset():
    cache = TabStateCache("demo")
    register(cache, "cold", lambda: {"value": "cold"}, tier="COLD")

    async def scenario():
        await cache.warm_up()
        result = await cache.invalidate("score")
        payload = await cache.get(["cold"])
        return result, payload

    result, payload = run(scenario())

    assert result["deleted"] == []
    assert payload["cold"]["status"] == "ready"
    assert payload["cold"]["data"] == {"value": "cold"}


def test_no_global_lock_reads_during_invalidation():
    cache = TabStateCache("demo")
    release = asyncio.Event()
    calls = {"a": 0}

    async def slow_compute():
        calls["a"] += 1
        if calls["a"] > 1:
            await release.wait()
        return {"value": "a"}

    register(cache, "a", slow_compute, invalidated_by=["score"], critical=False)
    register(cache, "b", lambda: {"value": "b"}, tier="COLD")

    async def scenario():
        await cache.warm_up()
        await cache.invalidate("score")
        started = time.perf_counter()
        payload = await cache.get(["b"])
        elapsed = time.perf_counter() - started
        return elapsed, payload

    elapsed, payload = run(scenario())

    assert elapsed < 0.05
    assert payload["b"]["data"] == {"value": "b"}


def test_cache_size_warning_over_1mb(caplog):
    cache = TabStateCache("demo", warn_bytes=10, reject_bytes=2_000_000)
    register(cache, "large", lambda: {"value": "x" * 1_100_000})

    with caplog.at_level(logging.WARNING):
        payload = run(cache.get(["large"]))

    assert payload["large"]["status"] == "ready"
    assert any("tab-state key demo.large" in message for message in caplog.messages)


def test_scanner_detects_missing_mutation_path():
    app = FastAPI()

    @app.post("/api/demo/mutate")
    def mutate():
        scorer.score({"x": 1}, "demo")  # noqa: F821
        return {"ok": True}

    missing = scan_mutation_routes(app, mutation_paths={})

    assert missing == [{"method": "POST", "path": "/api/demo/mutate", "endpoint": "mutate"}]


def test_scanner_checks_serialize_mutation_event():
    app = FastAPI()

    @app.post("/api/demo/mutate")
    def mutate():
        scorer.score({"x": 1}, "demo")  # noqa: F821
        return {"ok": True}

    missing = scan_mutation_routes(app, mutation_paths={("POST", "/api/demo/mutate"): "score"})

    assert missing == [{"method": "POST", "path": "/api/demo/mutate", "endpoint": "mutate"}]


def test_no_invalidates_middleware_remains():
    root = Path(__file__).resolve().parents[1]
    forbidden = ("create_" + "invalidation_middleware", "@" + "invalidates")
    offenders: list[str] = []
    for base in (root / "copilot_sdk", root / "apps" / "trading" / "backend" / "app"):
        for path in base.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            for pattern in forbidden:
                if pattern in source:
                    offenders.append(str(path.relative_to(root)))
                    break

    assert offenders == []


def test_warmup_under_5s_with_preseed():
    cache = TabStateCache("demo")
    for index in range(43):
        register(cache, f"key-{index}", lambda index=index: {"index": index})

    started = time.perf_counter()
    run(cache.warm_up())
    elapsed = time.perf_counter() - started

    assert elapsed < 5.0
