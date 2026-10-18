from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from copilot_sdk.backend.response_materializer import ResponseMaterializer


class Store:
    def __init__(self) -> None:
        self.value = 1
        self.reads = 0
        self.verified_reads = 0

    def get_all_decisions(self, domain: str):
        self.reads += 1
        return [{"value": self.value}]

    def get_verified_decisions(self, domain: str):
        self.verified_reads += 1
        return []


def _materializer(store: Store, **computations):
    return ResponseMaterializer("test", lambda: store, computations, ttl=5.0)


def test_one_refresh_publishes_all_responses_from_one_snapshot() -> None:
    store = Store()
    mat = _materializer(store, data=lambda s: s["decisions"], total=lambda s: len(s["decisions"]))
    assert mat.get_or_refresh("data") == [{"value": 1}]
    assert mat.get("total") == 1
    assert (store.reads, store.verified_reads) == (1, 1)


def test_fresh_get_performs_no_graph_callbacks() -> None:
    store = Store()
    mat = _materializer(store, data=lambda s: s["decisions"])
    mat.refresh()
    before = (store.reads, store.verified_reads)
    assert mat.get("data") == [{"value": 1}]
    assert mat.get_or_refresh("data") == [{"value": 1}]
    assert (store.reads, store.verified_reads) == before


def test_display_cycle_uses_two_queries_then_zero_within_generation() -> None:
    """One cold display read refreshes both snapshots; peers reuse them."""
    store = Store()
    mat = _materializer(
        store,
        fingerprint=lambda s: len(s["verified"]),
        conservation=lambda s: len(s["decisions"]),
    )

    assert mat.get_or_refresh("fingerprint") == 0
    assert (store.reads, store.verified_reads) == (1, 1)

    store.reads = 0
    store.verified_reads = 0
    assert mat.get_or_refresh("conservation") == 1
    assert (store.reads, store.verified_reads) == (0, 0)


def test_concurrent_cold_reads_share_one_refresh() -> None:
    store = Store()
    entered = threading.Event()
    release = threading.Event()

    def compute(shared):
        entered.set()
        assert release.wait(2.0)
        return shared["decisions"]

    mat = _materializer(store, data=compute)
    with ThreadPoolExecutor(max_workers=4) as executor:
        first = executor.submit(mat.get_or_refresh, "data")
        assert entered.wait(1.0)
        others = [executor.submit(mat.get_or_refresh, "data") for _ in range(3)]
        release.set()
        assert first.result() == [{"value": 1}]
        assert [future.result() for future in others] == [[{"value": 1}]] * 3
    assert (store.reads, store.verified_reads) == (1, 1)
    assert mat.generation_id == 1


def test_stale_read_is_nonblocking_during_refresh() -> None:
    store = Store()
    entered = threading.Event()
    release = threading.Event()
    block = False

    def compute(shared):
        if block:
            entered.set()
            assert release.wait(2.0)
        return shared["decisions"]

    mat = _materializer(store, data=compute)
    mat.refresh()
    store.value = 2
    mat.invalidate()
    block = True
    worker = threading.Thread(target=mat.refresh)
    worker.start()
    assert entered.wait(1.0)
    assert mat.get("data") == [{"value": 1}]
    assert mat.get_or_refresh("data") == [{"value": 1}]
    release.set()
    worker.join(2.0)
    assert mat.get("data") == [{"value": 2}]


def test_failed_refresh_preserves_last_good_generation() -> None:
    store = Store()
    fail = False

    def compute(shared):
        if fail:
            raise RuntimeError("compute failed")
        return shared["decisions"]

    mat = _materializer(store, data=compute)
    mat.refresh()
    generation = mat.generation_id
    fail = True
    mat.invalidate()
    assert mat.get_or_refresh("data") == [{"value": 1}]
    assert mat.generation_id == generation


def test_mutation_during_refresh_never_serves_pre_mutation_generation() -> None:
    store = Store()
    entered = threading.Event()
    release = threading.Event()
    block = False

    def compute(shared):
        if block:
            entered.set()
            assert release.wait(2.0)
        return shared["decisions"]

    mat = _materializer(store, data=compute)
    mat.refresh()
    assert mat.get("data") == [{"value": 1}]

    store.value = 2
    mat.invalidate()
    block = True
    worker = threading.Thread(target=mat.refresh)
    worker.start()
    assert entered.wait(1.0)

    store.value = 3
    mat.invalidate_mutation()
    assert mat.get("data") is None
    release.set()
    worker.join(2.0)
    assert not worker.is_alive()

    block = False
    assert mat.get_or_refresh("data") == [{"value": 3}]
    assert mat.status()["mutation_pending"] is False
    assert mat.status()["last_refresh_query_count"] == 2


def test_source_failure_propagates_without_a_generation() -> None:
    def unavailable():
        raise ValueError("source offline")

    mat = ResponseMaterializer("test", unavailable, {"data": lambda shared: shared})
    with pytest.raises(ValueError, match="source offline"):
        mat.get_or_refresh("data")


def test_returned_payload_is_an_independent_copy() -> None:
    store = Store()
    mat = _materializer(store, data=lambda s: s["decisions"])
    first = mat.get_or_refresh("data")
    first[0]["value"] = 99
    assert mat.get("data") == [{"value": 1}]
