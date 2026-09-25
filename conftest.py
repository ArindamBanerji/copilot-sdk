"""Repository-wide disposable AGE infrastructure for integration tests."""
from __future__ import annotations

import os
from types import SimpleNamespace
from uuid import uuid4

import pytest

from copilot_sdk.config import GraphConfig

# Resolve before app-specific fixtures temporarily rewrite their graph configuration.
_TEST_DSN = os.environ.get("AGE_TEST_DSN", "").strip() or GraphConfig.load("trading").dsn


class _DisposableAGE(SimpleNamespace):
    def __repr__(self) -> str:
        return f"DisposableAGE(graph={self.graph!r}, dsn=<redacted>)"


@pytest.fixture
def disposable_age():
    import psycopg
    from ci_platform.graph.age_client import AGEClient
    from ci_platform.graph.age_sdk_adapter import AGEGraphStoreAdapter

    if not _TEST_DSN:
        pytest.skip("AGE DSN is not configured")

    def connect():
        conn = psycopg.connect(_TEST_DSN, connect_timeout=3, autocommit=True)
        conn.execute("LOAD 'age'")
        conn.execute('SET search_path = ag_catalog, "$user", public')
        return conn

    try:
        admin = connect()
    except (psycopg.OperationalError, psycopg.ProgrammingError):
        pytest.skip("AGE is not reachable")
    graph = "protocol_v2_test_mockfix_" + uuid4().hex[:12]
    admin.execute("SELECT create_graph(%s)", (graph,))
    admin.execute("SELECT create_vlabel(%s, %s)", (graph, "EvolutionEvent"))
    resources = []

    def store(domain="test"):
        result = AGEGraphStoreAdapter(dsn=_TEST_DSN, graph_name=graph, domain=domain)
        resources.append(result)
        return result

    def client():
        result = AGEClient(dsn=_TEST_DSN, graph_name=graph)
        resources.append(result)
        return result

    try:
        yield _DisposableAGE(dsn=_TEST_DSN, graph=graph, store=store, client=client, connect=connect)
    finally:
        for resource in resources:
            if isinstance(resource, AGEGraphStoreAdapter):
                resource.close()
            else:
                resource._sync_close()
        # Only the unique graph created above belongs to this fixture.
        admin.execute("SELECT drop_graph(%s, true)", (graph,))
        admin.close()


@pytest.fixture
def shared_age_readonly():
    """Read-only connection to the configured shared graph; never seeds or resets it."""
    import psycopg
    from ci_platform.graph.age_sdk_adapter import AGEGraphStoreAdapter

    if not _TEST_DSN:
        pytest.skip("AGE DSN is not configured")
    store = AGEGraphStoreAdapter(dsn=_TEST_DSN, graph_name="soc_graph", domain="trading")
    try:
        store.count_decisions("trading")
    except (psycopg.OperationalError, psycopg.ProgrammingError):
        store.close()
        pytest.skip("Shared AGE graph is not reachable")
    config = SimpleNamespace(backend="age", graph="soc_graph", dsn=_TEST_DSN,
                             source_keys=(("dsn", "AGE_TEST_DSN"),))
    try:
        yield store, config
    finally:
        store.close()


@pytest.fixture
def migration_probe(disposable_age):
    from tests.age_probe import MigrationProbe
    probes = []

    def make(**kwargs):
        probe = MigrationProbe(disposable_age, **kwargs)
        probes.append(probe)
        return probe

    try:
        yield make
    finally:
        for probe in probes:
            probe.close()
