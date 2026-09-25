"""Fixtures for production-profile AGE contract checks."""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import psycopg
import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "age_required: test requires a live AGE connection"
    )


def _configured_dsn() -> str:
    return (
        os.environ.get("AGE_TEST_DSN", "").strip()
        or os.environ.get("GRAPH_DSN", "").strip()
        or os.environ.get("AGE_DSN", "").strip()
    )


@pytest.fixture(autouse=True)
def _check_age_dsn(request: pytest.FixtureRequest) -> None:
    if request.node.get_closest_marker("age_required") and not _configured_dsn():
        pytest.fail("AGE_REQUIRED: No GRAPH_DSN, AGE_TEST_DSN, or AGE_DSN is set.")


@pytest.fixture
def age_contract_store() -> Iterator[object]:
    """Use one uniquely named graph, then close and drop only that graph."""
    dsn = _configured_dsn()
    if not dsn:
        pytest.fail("AGE_REQUIRED: no AGE DSN configured")

    from ci_platform.graph.age_sdk_adapter import AGEGraphStoreAdapter

    graph_name = f"jm_contract_{uuid.uuid4().hex[:16]}"
    with psycopg.connect(dsn, connect_timeout=5, autocommit=True) as admin:
        admin.execute("LOAD 'age'")
        admin.execute('SET search_path = ag_catalog, "$user", public')
        admin.execute("SELECT create_graph(%s)", (graph_name,))

    store = AGEGraphStoreAdapter(dsn=dsn, graph_name=graph_name, domain="trading")
    try:
        yield store
    finally:
        store.close()
        with psycopg.connect(dsn, connect_timeout=5, autocommit=True) as admin:
            admin.execute("LOAD 'age'")
            admin.execute('SET search_path = ag_catalog, "$user", public')
            admin.execute("SELECT drop_graph(%s, true)", (graph_name,))
