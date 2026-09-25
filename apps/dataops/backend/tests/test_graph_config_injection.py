"""G043: DataOps topology must use the same resolved config and primary."""

from __future__ import annotations

import os
from dataclasses import replace

import pytest

from app.graph_queries import DataOpsGraphClient, _load_topology_config
from copilot_sdk.config import GraphConfig, GraphConfigError
from copilot_sdk.graph.memory_store import InMemoryGraphStore


def test_topology_resolution_does_not_mutate_environment(monkeypatch):
    monkeypatch.setenv("DATAOPS_ACTIVE_AGE_DSN", "host=domain")
    monkeypatch.setenv("GRAPH_DSN", "host=generic")
    before = dict(os.environ)
    config = _load_topology_config(profile="test")
    assert config.dsn == "host=domain"
    assert dict(config.source_keys)["dsn"] == "DATAOPS_ACTIVE_AGE_DSN"
    assert dict(os.environ) == before


def test_injected_topology_config_is_not_reresolved(monkeypatch):
    config = GraphConfig.load("dataops", profile="test")
    store = InMemoryGraphStore(domain="dataops")
    monkeypatch.setenv("GRAPH_DSN", "host=changed-after-resolution")
    before = dict(os.environ)
    monkeypatch.setattr(GraphConfig, "load", lambda *args, **kwargs: pytest.fail("config was resolved twice"))
    client = DataOpsGraphClient(config=config, graph_store=store)
    assert client.graph_config is config
    assert client.graph_store is store
    assert dict(os.environ) == before


def test_production_topology_requires_shared_store_not_client_double():
    config = replace(
        GraphConfig.load("dataops", profile="test"), profile="production",
        backend="age", expected_backend="age", graph="soc_graph", dsn="host=unit",
    )
    with pytest.raises(GraphConfigError, match="shared GraphStore"):
        DataOpsGraphClient(config=config, age_client=object())


def test_topology_rejects_conflicting_config_and_profile():
    config = GraphConfig.load("dataops", profile="test")
    with pytest.raises(GraphConfigError, match="profile conflicts"):
        DataOpsGraphClient(config=config, profile="production")
    with pytest.raises(GraphConfigError, match="DSN override conflicts"):
        DataOpsGraphClient(config=config, dsn="host=other")
    with pytest.raises(GraphConfigError, match="dataops GraphConfig"):
        DataOpsGraphClient(config=replace(config, domain="trading"))


def test_age_initialization_failure_raises_instead_of_fixture_success():
    config = replace(GraphConfig.load("dataops", profile="test"), backend="age", dsn="host=unit")

    class Unavailable:
        def __init__(self, **kwargs):
            raise ConnectionError("unavailable")

    with pytest.raises(ConnectionError, match="unavailable"):
        DataOpsGraphClient(config=config, age_client_cls=Unavailable)


def test_app_passes_one_resolved_config_and_store_to_topology(dataops_data_dir, monkeypatch):
    from app.main import create_app

    config = GraphConfig.load("dataops", profile="test")
    monkeypatch.setattr(GraphConfig, "load", lambda *args, **kwargs: pytest.fail("app re-resolved injected config"))
    app = create_app(
        db_path=dataops_data_dir / "injection.db", demo_bundle_path=False,
        graph_config=config,
    )
    assert app.state.graph_config is config
    assert app.state.dataops_topology.graph_config is config
    assert app.state.dataops_topology.graph_store is app.state.graph_store
    app.state.graph_store.close()


def test_startup_seed_preserves_explicit_profile(monkeypatch):
    from app import main

    selected = {}
    store = InMemoryGraphStore(domain="dataops")
    monkeypatch.setenv("DATAOPS_PROFILE", "production")

    def scorer_factory(*args, **kwargs):
        selected.update(kwargs)
        return object()

    monkeypatch.setattr(main.CompoundingScorer, "from_preset", scorer_factory)
    monkeypatch.setattr(main, "_seed_from_fixtures", lambda *args: {
        "decisions_seeded": 0, "outcomes_seeded": 0,
    })
    try:
        assert main._auto_seed_if_needed(store, profile="offline") == 0
        assert selected["profile"] == "offline"
        assert selected["graph_store"] is store
    finally:
        store.close()
