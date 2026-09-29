from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from psycopg import OperationalError, ProgrammingError

from copilot_sdk.backend.graph_access import graph_call
from copilot_sdk.backend.health_builder import build_graph_health, health_status_code
from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
from copilot_sdk.graph.production import GraphStoreWrapper


@pytest.mark.parametrize("backend", ["memory", "sqlite"])
@pytest.mark.parametrize("domain", ["trading", "purchasing", "dataops", "s2p", "soc"])
def test_health_uses_actual_primary_and_domain_count(tmp_path: Path, backend: str, domain: str) -> None:
    store = (SQLiteGraphStore(str(tmp_path / "health.db"), domain=domain)
             if backend == "sqlite" else InMemoryGraphStore(domain=domain))
    try:
        store.write_decision(domain, "category", "action", 0.5, {"signal": 0.5})
        # Deliberately incorrect configuration must not masquerade as AGE.
        config = SimpleNamespace(requested_backend="age", graph="soc_graph")
        payload = build_graph_health(store, config, domain)
        assert payload["graph_backend"] == backend
        assert payload["node_count"] == 1
        assert payload["node_count_scope"] == "domain_decisions"
        assert payload["graph_connected"] is True
        assert payload["ready"] is False  # production AGE readiness remains separate
        assert payload["product_claim_allowed"] is False
        # Probe on every request, not a cached count.
        store.write_decision(domain, "category", "action", 0.5, {"signal": 0.5})
        assert build_graph_health(store, config, domain)["node_count"] == 2
    finally:
        store.close()


@pytest.mark.parametrize("failure", [OperationalError("connection lost"), ConnectionError("offline"), TimeoutError("timeout")])
def test_health_unavailable_is_not_a_zero_node_graph(failure: Exception) -> None:
    store = InMemoryGraphStore(domain="purchasing")
    with patch.object(store, "count_decisions", side_effect=failure):
        payload = build_graph_health(store, SimpleNamespace(backend="age"), "purchasing")
    assert payload["graph_backend"] == "memory"
    assert payload["graph_connected"] is False
    assert payload["node_count"] is None
    assert health_status_code(payload) == 503


def test_health_missing_store() -> None:
    payload = build_graph_health(None, SimpleNamespace(requested_backend="age"), "trading")
    assert payload["graph_connected"] is False
    assert payload["node_count"] is None
    assert health_status_code(payload) == 503


@pytest.mark.parametrize("domain", ["trading", "purchasing", "dataops", "s2p", "soc"])
def test_age_health_probes_primary_and_reports_readiness(domain: str) -> None:
    from ci_platform.graph.age_graph_store import AGEGraphStore
    from ci_platform.graph.age_sdk_adapter import AGEGraphStoreAdapter

    with patch("ci_platform.graph.age_graph_store.AGEClient", autospec=True):
        primary = AGEGraphStore(dsn="host=unit", graph_name="soc_graph")
    store = AGEGraphStoreAdapter(store=primary, domain=domain)
    with patch.object(primary, "count_decisions", return_value=7) as count:
        payload = build_graph_health(store, SimpleNamespace(backend="sqlite", graph="soc_graph"), domain)
    count.assert_called_once_with(domain)
    assert payload["graph_backend"] == "age"
    assert payload["node_count"] == 7
    assert payload["graph_connected"] is True
    assert health_status_code(payload) == 200
    with patch.object(primary, "count_decisions", side_effect=OperationalError("connection lost")):
        payload = build_graph_health(store, SimpleNamespace(graph="soc_graph"), domain)
    assert payload["node_count"] is None
    assert payload["graph_connected"] is False
    assert health_status_code(payload) == 503


def test_health_follows_wrapper_primary() -> None:
    wrapper = GraphStoreWrapper()
    wrapper._store = InMemoryGraphStore(domain="s2p")
    payload = build_graph_health(wrapper, SimpleNamespace(backend="age"), "s2p")
    assert payload["graph_backend"] == "memory"
    assert payload["node_count"] == 0
    assert payload["graph_connected"] is True


@pytest.mark.parametrize("failure", [ValueError("bug"), TypeError("bug"), ProgrammingError("bad SQL")])
def test_guards_do_not_hide_programming_errors(failure: Exception) -> None:
    store = InMemoryGraphStore(domain="dataops")
    with patch.object(store, "count_decisions", side_effect=failure):
        with pytest.raises(type(failure)):
            graph_call(store.count_decisions, "dataops")
        with pytest.raises(type(failure)):
            build_graph_health(store, SimpleNamespace(backend="age"), "dataops")


def test_graph_guard_logs_and_translates_connection_error(caplog: pytest.LogCaptureFixture) -> None:
    store = InMemoryGraphStore(domain="dataops")
    with patch.object(store, "get_all_decisions", side_effect=OperationalError("lost")):
        with pytest.raises(HTTPException) as error:
            graph_call(store.get_all_decisions, "dataops")
    assert error.value.status_code == 503
    assert error.value.detail == "Graph store unavailable"
    assert "Graph store operation failed" in caplog.text
