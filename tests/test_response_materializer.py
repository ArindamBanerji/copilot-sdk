from concurrent.futures import ThreadPoolExecutor
import threading

import pytest

from copilot_sdk.backend import response_materializer as module
from copilot_sdk.backend.response_materializer import ResponseMaterializer


class Store:
    def __init__(self):
        self.value = 1
        self.reads = 0

    def get_all_decisions(self, domain):
        self.reads += 1
        return [{"value": self.value}]

    def get_verified_decisions(self, domain):
        return []


def test_invalidation_discards_inflight_build_and_clears_stale_payload():
    store = Store()
    started, release = threading.Event(), threading.Event()
    release.set()

    def compute(shared):
        started.set()
        assert release.wait(5)
        return {"total": shared["decisions"][0]["value"]}

    mat = ResponseMaterializer("test", lambda: store, {"data": compute}, ttl=60)
    mat.refresh()
    assert mat.get("data") == {"total": 1}
    started.clear()
    release.clear()
    with ThreadPoolExecutor() as pool:
        active = pool.submit(mat.refresh)
        try:
            assert started.wait(5)
            assert mat.get("data") == {"total": 1}
            store.value = 2
            mat.invalidate()  # Must not wait for the active computation.
            assert mat.get("data") is None
        finally:
            release.set()
        active.result(timeout=5)
    assert mat.get("data") is None
    assert mat.get_or_refresh("data") == {"total": 2}
    assert store.reads == 3


@pytest.mark.parametrize("invalidate_active", [False, True])
def test_concurrent_cold_read_joins_active_build(monkeypatch, invalidate_active):
    store = Store()
    started, release, waiting = threading.Event(), threading.Event(), threading.Event()

    def compute(shared):
        started.set()
        assert release.wait(5)
        return {"rows": shared["decisions"]}

    mat = ResponseMaterializer("test", lambda: store, {"data": compute})
    original_wait = mat._lock.wait_for

    def observed_wait(predicate):
        waiting.set()
        return original_wait(predicate)

    monkeypatch.setattr(mat._lock, "wait_for", observed_wait)
    with ThreadPoolExecutor(max_workers=2) as pool:
        active = pool.submit(mat.refresh)
        try:
            assert started.wait(5)
            reader = pool.submit(mat.get_or_refresh, "data")
            assert waiting.wait(5)
            assert not reader.done()
            if invalidate_active:
                store.value = 2
                mat.invalidate()
        finally:
            release.set()
        active.result(timeout=5)
        result = reader.result(timeout=5)
    expected = 2 if invalidate_active else 1
    assert result == {"rows": [{"value": expected}]}
    assert store.reads == expected
    result["rows"][0]["value"] = 999
    assert mat.get("data") == {"rows": [{"value": expected}]}


def test_failed_source_notifies_waiters_and_can_retry(monkeypatch):
    started, release, waiting = threading.Event(), threading.Event(), threading.Event()
    store = Store()
    fail = [True]

    def provider():
        if fail[0]:
            started.set()
            assert release.wait(5)
            raise ValueError("source offline")
        return store

    mat = ResponseMaterializer("test", provider, {"data": lambda s: s["decisions"]})
    original_wait = mat._lock.wait_for

    def observed_wait(predicate):
        waiting.set()
        return original_wait(predicate)

    monkeypatch.setattr(mat._lock, "wait_for", observed_wait)
    with ThreadPoolExecutor(max_workers=2) as pool:
        active = pool.submit(mat.refresh)
        try:
            assert started.wait(5)
            reader = pool.submit(mat.get_or_refresh, "data")
            assert waiting.wait(5)
        finally:
            release.set()
        with pytest.raises(ValueError, match="source offline"):
            active.result(timeout=5)
        with pytest.raises(RuntimeError, match="Response refresh failed"):
            reader.result(timeout=5)
    fail[0] = False
    assert mat.get_or_refresh("data") == [{"value": 1}]


@pytest.mark.parametrize("payload", [{}, [], 0, False])
def test_ttl_and_falsey_payloads(monkeypatch, payload):
    now = [100.0]
    monkeypatch.setattr(module.time, "monotonic", lambda: now[0])
    store = Store()

    def slow_build(shared):
        now[0] += 10
        return payload

    mat = ResponseMaterializer("test", lambda: store, {"data": slow_build}, ttl=5)
    assert mat.get_or_refresh("data") == payload
    now[0] += 4
    assert mat.get_or_refresh("data") == payload
    assert store.reads == 1
    now[0] += 1
    assert mat.get("data") is None
    assert mat.get_or_refresh("data") == payload
    assert store.reads == 2
    assert mat.get_or_refresh("unknown") is None
    assert store.reads == 2


def test_continuous_invalidation_is_bounded_and_never_publishes_old_data():
    store = Store()

    def compute(shared):
        mat.invalidate()
        return shared["decisions"]

    mat = ResponseMaterializer("test", lambda: store, {"data": compute})
    assert mat.get_or_refresh("data") is None
    assert store.reads == 3
    assert mat.get("data") is None
