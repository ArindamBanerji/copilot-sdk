"""Shared test stores, scorers, and live AGE availability checks."""

from __future__ import annotations

import logging
import os
import uuid
from collections.abc import Generator
from functools import lru_cache
from typing import Any, Callable

import pytest

from copilot_sdk.config import GraphConfig
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer

log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def age_available() -> bool:
    """Return whether configured AGE is reachable, without an env gate."""
    try:
        dsn = os.getenv("AGE_TEST_DSN", "").strip() or (GraphConfig.load("trading").dsn or "")
        if not dsn:
            return False
        import psycopg

        conn: Any = psycopg.connect(dsn, connect_timeout=3, autocommit=True)
        with conn:
            conn.execute("LOAD 'age'")
            conn.execute('SET search_path = ag_catalog, "$user", public')
            conn.execute("SELECT 1")
        return True
    except Exception as exc:  # pragma: no cover - depends on external AGE
        log.debug("AGE unavailable for tests: %s", exc)
        return False


requires_age = pytest.mark.skipif(
    not age_available(),
    reason="AGE not reachable (no DSN configured or connection failed)",
)


@pytest.fixture
def test_graph_store() -> Generator[Callable[[str], InMemoryGraphStore], None, None]:
    """Return a factory for isolated in-memory GraphStores."""
    stores: list[InMemoryGraphStore] = []

    def make(domain: str = "test") -> InMemoryGraphStore:
        store = InMemoryGraphStore(domain=domain)
        stores.append(store)
        return store

    yield make
    for store in stores:
        store.close()


@pytest.fixture
def test_scorer() -> Generator[Callable[[str], CompoundingScorer], None, None]:
    """Return a factory for profile=test scorers backed by memory."""
    scorers: list[CompoundingScorer] = []

    def make(domain: str = "trading") -> CompoundingScorer:
        scorer = CompoundingScorer.from_preset(
            domain,
            graph_store=InMemoryGraphStore(domain=domain),
            profile="test",
        )
        scorers.append(scorer)
        return scorer

    yield make
    for scorer in scorers:
        scorer.graph_store.close()


@pytest.fixture
def age_graph_store() -> Generator[Callable[[str], Any], None, None]:
    """Return a factory for stores on disposable, non-production AGE graphs."""
    if not age_available():
        pytest.skip("AGE not reachable (no DSN configured or connection failed)")

    import psycopg
    from ci_platform.graph import AGEGraphStoreAdapter

    config = GraphConfig.load("trading")
    dsn = config.dsn
    if not dsn:
        pytest.skip("AGE DSN is not configured")
    graph_name = f"sdk_test_{uuid.uuid4().hex[:12]}"
    conn: Any = psycopg.connect(dsn, connect_timeout=3, autocommit=True)
    with conn:
        conn.execute("LOAD 'age'")
        conn.execute('SET search_path = ag_catalog, "$user", public')
        conn.execute(f"SELECT create_graph('{graph_name}')")
    stores: list[Any] = []

    def make(domain: str = "trading") -> Any:
        store = AGEGraphStoreAdapter(dsn=dsn, graph_name=graph_name)
        stores.append(store)
        return store

    try:
        yield make
    finally:
        for store in stores:
            close = getattr(store, "close", None)
            if close is not None:
                close()
        conn = psycopg.connect(dsn, connect_timeout=3, autocommit=True)
        with conn:
            conn.execute("LOAD 'age'")
            conn.execute('SET search_path = ag_catalog, "$user", public')
            conn.execute(f"SELECT drop_graph('{graph_name}', true)")
