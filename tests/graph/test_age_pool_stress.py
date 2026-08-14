"""AGE-STRESS: cross-domain concurrency and pool exhaustion stress coverage.

Queue ID: AGE-STRESS

This module uses a real, disposable AGE graph and a deliberately small,
test-owned pool.  It proves that contention is bounded and isolated without
changing the production pool configuration.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FutureTimeout
from contextlib import contextmanager
import importlib
import os
from pathlib import Path
import sys
import time
from typing import Any, Callable, Iterator
import uuid

import pytest


AGE_AVAILABLE = bool(os.environ.get("GRAPH_DSN"))

pytestmark = pytest.mark.skipif(
    not AGE_AVAILABLE,
    reason="AGE-STRESS: requires GRAPH_DSN for live AGE connection",
)

_OPERATION_DEADLINE = 10.0
_POOL_TIMEOUT = 2.0
_DOMAINS = ("trading", "purchasing", "dataops")


def _age_client_class() -> Any:
    repo_root = Path(__file__).resolve().parents[2]
    ci_platform_path = repo_root.parent / "ci-platform"
    if str(ci_platform_path) not in sys.path:
        sys.path.insert(0, str(ci_platform_path))
    from ci_platform.graph.age_client import AGEClient  # noqa: PLC0415

    return AGEClient


def _dsn() -> str:
    value = os.environ.get("AGE_TEST_DSN", "").strip() or os.environ.get("GRAPH_DSN", "").strip()
    if not value:
        pytest.skip("AGE-STRESS: no AGE DSN configured")
    return value


@contextmanager
def _disposable_graph() -> Iterator[tuple[str, str]]:
    dsn = _dsn()
    graph_name = f"age_stress_{uuid.uuid4().hex[:12]}"
    psycopg_module: Any = importlib.import_module("psycopg")
    admin: Any = psycopg_module.connect(dsn, connect_timeout=5, autocommit=True)
    try:
        admin.execute("LOAD 'age'")
        admin.execute('SET search_path = ag_catalog, "$user", public')
        admin.execute(f"SELECT create_graph('{graph_name}')")
        yield dsn, graph_name
    finally:
        try:
            if not admin.closed:
                admin.execute("LOAD 'age'")
                admin.execute('SET search_path = ag_catalog, "$user", public')
                admin.execute(f"SELECT drop_graph('{graph_name}', true)")
        finally:
            admin.close()


@contextmanager
def _stress_resources() -> Iterator[tuple[Any, str]]:
    with _disposable_graph() as (dsn, graph_name):
        client_class = _age_client_class()
        client = client_class(
            dsn=dsn,
            graph_name=graph_name,
            use_pool=True,
            pool_min_size=3,
            pool_max_size=3,
        )
        try:
            asyncio.run(client.connect())
            pool = client._ensure_pool()
            if pool is None:
                pytest.fail("AGE-STRESS: pooled AGE client did not create a pool")
            # This is a real psycopg pool, owned by this test.  The production
            # AGEClient does not expose an acquisition-timeout constructor arg.
            pool.timeout = _POOL_TIMEOUT
            yield client, graph_name
        finally:
            asyncio.run(client.close())


def _query(client: Any, cypher: str) -> list[dict[str, Any]]:
    return asyncio.run(client.run_query(cypher))


def _timed_call(call: Callable[[], Any]) -> tuple[str, float, Any]:
    started = time.monotonic()
    try:
        return "ok", time.monotonic() - started, call()
    except Exception as exc:  # The caller classifies bounded AGE errors.
        return "error", time.monotonic() - started, exc


def _run_bounded(calls: list[Callable[[], Any]], workers: int) -> list[tuple[str, float, Any]]:
    executor = ThreadPoolExecutor(max_workers=workers)
    futures: list[Future[tuple[str, float, Any]]] = []
    try:
        futures = [executor.submit(_timed_call, call) for call in calls]
        results = [future.result(timeout=_OPERATION_DEADLINE) for future in futures]
    except FutureTimeout as exc:
        for future in futures:
            future.cancel()
        pytest.fail(f"AGE-STRESS operation exceeded {_OPERATION_DEADLINE}s: {exc}")
    finally:
        # All supported AGE outcomes are bounded.  Do not wait indefinitely in
        # teardown if a future exposed a real hang; pytest's timeout remains a
        # final safety net for a broken driver.
        executor.shutdown(wait=False, cancel_futures=True)
    return results


def _seed_entities(client: Any) -> None:
    for domain in _DOMAINS:
        for index in range(2):
            entity_id = f"{domain}-seed-{index}"
            rows = _query(
                client,
                "CREATE (n:StressEntity {"
                f"entity_id: '{entity_id}', domain: '{domain}'"
                "}) RETURN n.entity_id AS entity_id",
            )
            assert rows and rows[0]["entity_id"] == entity_id


def _read_call(client: Any, domain: str) -> Callable[[], Any]:
    return lambda: _query(
        client,
        "MATCH (n:StressEntity) "
        f"WHERE n.domain = '{domain}' "
        f"RETURN '{domain}' AS domain, count(n) AS cnt",
    )


def _write_call(client: Any, domain: str, index: int) -> Callable[[], Any]:
    entity_id = f"{domain}-write-{index}"
    return lambda: _query(
        client,
        "CREATE (n:StressEntity {"
        f"entity_id: '{entity_id}', domain: '{domain}'"
        "}) RETURN n.entity_id AS entity_id",
    )


def _assert_no_pool_closed(results: list[tuple[str, float, Any]]) -> None:
    for status, elapsed, value in results:
        assert elapsed <= _OPERATION_DEADLINE, f"operation exceeded deadline: {elapsed:.2f}s"
        if status == "error":
            assert type(value).__name__ != "PoolClosed", f"unexpected PoolClosed cascade: {value}"
            assert "PoolClosed" not in str(value), f"unexpected PoolClosed cascade: {value}"


def _scenario_reads(client: Any) -> list[tuple[str, float, Any]]:
    calls = [_read_call(client, domain) for domain in _DOMAINS for _ in range(2)]
    results = _run_bounded(calls, workers=6)
    _assert_no_pool_closed(results)
    for status, _, value in results:
        assert status == "ok", f"read failed: {value}"
        assert value and value[0]["domain"] in _DOMAINS
    return results


def _scenario_exhaustion(client: Any) -> list[tuple[str, float, Any]]:
    pool = client._ensure_pool()
    assert pool is not None
    # Use standard events for holder coordination: holder functions run in
    # worker threads, while asyncio is reserved for the public client API.
    import threading

    acquired_thread = [threading.Event() for _ in range(3)]
    release_thread = threading.Event()

    def hold_connection(index: int) -> None:
        with pool.connection(timeout=_POOL_TIMEOUT) as connection:
            acquired_thread[index].set()
            release_thread.wait(_OPERATION_DEADLINE)
            connection.execute("SELECT 1")

    holder_executor = ThreadPoolExecutor(max_workers=3)
    holder_futures = [holder_executor.submit(hold_connection, index) for index in range(3)]
    try:
        assert all(event.wait(_OPERATION_DEADLINE) for event in acquired_thread)
        calls = [_read_call(client, domain) for domain in _DOMAINS]
        results = _run_bounded(calls, workers=3)
    finally:
        release_thread.set()
        for future in holder_futures:
            future.result(timeout=_OPERATION_DEADLINE)
        holder_executor.shutdown(wait=True, cancel_futures=True)

    _assert_no_pool_closed(results)
    assert all(status == "error" for status, _, _ in results), (
        "pool exhaustion unexpectedly allowed all acquisitions; contention was not forced"
    )
    for _, _, error in results:
        assert type(error).__name__ in {"PoolTimeout", "TimeoutError"} or "timeout" in str(error).lower(), error

    # The held connections are released before this health query.  It proves
    # exhaustion did not poison the test-owned pool or cascade to later work.
    healthy = _timed_call(lambda: _query(client, "MATCH (n:StressEntity) RETURN count(n) AS cnt"))
    assert healthy[0] == "ok", healthy[2]
    return results


def execute_stress_suite() -> None:
    """Run the shared AGE-STRESS suite for the legacy conformance wrapper."""
    with _stress_resources() as (client, _):
        _seed_entities(client)
        _scenario_reads(client)
        writes = _run_bounded(
            [_write_call(client, domain, index) for domain in _DOMAINS for index in range(2)],
            workers=6,
        )
        _assert_no_pool_closed(writes)
        assert all(status == "ok" for status, _, _ in writes)
        _scenario_exhaustion(client)
        _scenario_reads(client)


class TestAGEPoolStress:
    """Five bounded scenarios against a real disposable AGE graph."""

    def test_concurrent_reads_across_domains(self) -> None:
        with _stress_resources() as (client, _):
            _seed_entities(client)
            results = _scenario_reads(client)
            assert len(results) == 6

    def test_concurrent_writes_independent_domains(self) -> None:
        with _stress_resources() as (client, _):
            _seed_entities(client)
            results = _run_bounded(
                [_write_call(client, domain, index) for domain in _DOMAINS for index in range(2)],
                workers=6,
            )
            _assert_no_pool_closed(results)
            assert len(results) == 6
            assert all(status == "ok" for status, _, _ in results)

    def test_mixed_with_deliberate_failure(self) -> None:
        with _stress_resources() as (client, _):
            _seed_entities(client)
            calls: list[Callable[[], Any]] = [
                _read_call(client, domain) for domain in _DOMAINS
            ]
            calls.extend(_write_call(client, domain, 10) for domain in _DOMAINS[:2])
            calls.append(lambda: _query(client, "THIS IS DELIBERATELY INVALID AGE SYNTAX"))
            results = _run_bounded(calls, workers=6)
            _assert_no_pool_closed(results)
            assert sum(status == "ok" for status, _, _ in results) == 5
            assert sum(status == "error" for status, _, _ in results) == 1

    def test_pool_exhaustion_fails_closed(self) -> None:
        with _stress_resources() as (client, _):
            _seed_entities(client)
            results = _scenario_exhaustion(client)
            assert len(results) == 3

    def test_repeated_stress_no_leakage(self) -> None:
        with _stress_resources() as (client, _):
            _seed_entities(client)
            for _ in range(2):
                _scenario_reads(client)
                _scenario_exhaustion(client)
