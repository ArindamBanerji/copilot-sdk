from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.coalesced_read import CoalescedRead
from copilot_sdk.backend.self_computation_router import mount_self_computation_router
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore


def test_overlapping_real_reads_share_work_but_own_their_results(tmp_path: Path) -> None:
    store = SQLiteGraphStore(tmp_path / "reads.db", domain="purchasing")
    decision = store.write_decision("purchasing", "produce", "order", 0.8, {})
    store.write_outcome(decision, "order", True, domain="purchasing")
    reader = CoalescedRead()
    started, release = threading.Event(), threading.Event()
    calls = 0

    def load() -> list[dict[str, Any]]:
        nonlocal calls
        calls += 1
        started.set()
        assert release.wait(5)
        return cast(list[dict[str, Any]], store.get_verified_decisions("purchasing"))

    try:
        with ThreadPoolExecutor(max_workers=8) as pool:
            first = pool.submit(reader.run, "history", load)
            assert started.wait(5)
            followers = [pool.submit(reader.run, "history", load) for _ in range(7)]
            # Keep the actual store read in flight while all callers arrive.
            time.sleep(0.1)
            release.set()
            results = [first.result(), *(future.result() for future in followers)]
        assert calls == 1
        results[0][0]["category"] = "changed by caller"
        assert all(result[0]["category"] == "produce" for result in results[1:])
        reader.run("history", load)
        assert calls == 2  # A subsequent read is fresh, not a retained cache hit.
    finally:
        store.close()


def test_error_does_not_poison_later_read_and_keys_are_isolated(tmp_path: Path) -> None:
    reader = CoalescedRead()
    store = SQLiteGraphStore(tmp_path / "retry.db", domain="purchasing")
    store.close()
    with pytest.raises(Exception):
        reader.run(("purchasing", "tenant-a"), lambda: store.get_all_decisions("purchasing"))
    store = SQLiteGraphStore(tmp_path / "retry.db", domain="purchasing")
    try:
        assert reader.run(("purchasing", "tenant-a"), lambda: store.get_all_decisions("purchasing")) == []
        store.write_decision("purchasing", "produce", "order", 0.8, {})
        assert len(reader.run(("purchasing", "tenant-b"), lambda: store.get_all_decisions("purchasing"))) == 1
    finally:
        store.close()


def test_sc_reads_observe_committed_outcomes_without_waiting_for_ttl(tmp_path: Path) -> None:
    store = SQLiteGraphStore(tmp_path / "fresh.db", domain="purchasing")
    app = FastAPI()
    mount_self_computation_router(app, store, domain="purchasing")
    try:
        with TestClient(app) as client:
            assert client.get("/api/self/accuracy-alerts").json()["overall_verified"] == 0
            decision = store.write_decision("purchasing", "produce", "order", 0.8, {})
            store.write_outcome(decision, "order", True, domain="purchasing")
            assert client.get("/api/self/accuracy-alerts").json()["overall_verified"] == 1
            assert client.get("/api/self/decisions").json()["decisions"][0]["is_correct"] is True
            assert client.get("/api/self/audit-trail").json()["total"] == 1
    finally:
        store.close()
