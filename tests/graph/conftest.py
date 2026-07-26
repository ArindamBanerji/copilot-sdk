"""Shared live AGE fixtures for graph conformance tests."""

from __future__ import annotations

import os
import uuid

import pytest

from copilot_sdk.config import GraphConfig
from copilot_sdk.testing import age_available


_MISSING = object()
_DEFAULT_AGE_DSN = "postgresql://localhost:5432/soc_copilot"


@pytest.fixture(scope="session")
def age_test_graph():
    """Create and clean up an isolated AGE graph for the test session."""
    if not age_available():
        pytest.skip("AGE not available")

    dsn = os.getenv("AGE_TEST_DSN", "").strip()
    if not dsn:
        dsn = (GraphConfig.load("trading").dsn or "").strip()
    if not dsn or dsn == _DEFAULT_AGE_DSN:
        pytest.skip("AGE not available")

    import psycopg

    graph_name = f"protocol_v2_test_{uuid.uuid4().hex[:8]}"
    conn = psycopg.connect(dsn, connect_timeout=3, autocommit=True)
    old_graph = os.environ.get("AGE_TEST_GRAPH", _MISSING)
    try:
        conn.execute("LOAD 'age'")
        conn.execute('SET search_path = ag_catalog, "$user", public')
        conn.execute(f"SELECT create_graph('{graph_name}')")
        os.environ["AGE_TEST_GRAPH"] = graph_name
        yield graph_name
    finally:
        if old_graph is _MISSING:
            os.environ.pop("AGE_TEST_GRAPH", None)
        else:
            os.environ["AGE_TEST_GRAPH"] = old_graph
        try:
            if not conn.closed:
                conn.execute("LOAD 'age'")
                conn.execute('SET search_path = ag_catalog, "$user", public')
                conn.execute(f"SELECT drop_graph('{graph_name}', true)")
        finally:
            conn.close()
