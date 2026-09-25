"""G042/G043: production policy tests never inherit app test-profile fixtures."""

from __future__ import annotations

import os
from dataclasses import replace

import pytest

from copilot_sdk.config.graph_config import GraphConfig, GraphConfigError, GraphIdentity, resolve_profile
from copilot_sdk.graph.factory import create_graph_store
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.production import (
    GraphStoreWrapper, _probe_client_identity, validate_production_store,
)
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
from copilot_sdk.graph.tenant_store import TenantScopedGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer


@pytest.fixture
def config(monkeypatch, tmp_path):
    # Isolate configuration and outbox writes, without hiding production paths.
    for key in tuple(os.environ):
        if key.startswith(("GRAPH_", "AGE_", "TRADING_", "PURCHASING_", "DATAOPS_", "S2P_", "SOC_", "COPILOT_PROFILE")):
            monkeypatch.delenv(key)
    path = tmp_path / "graph.toml"
    path.write_text('[defaults]\nbackend="age"\nexpected_backend="age"\ngraph="soc_graph"\n', encoding="utf-8")
    monkeypatch.setenv("GRAPH_CONFIG_PATH", str(path))
    monkeypatch.setenv("GRAPH_DSN", "host=unit-canonical dbname=shared password=unit-secret")
    monkeypatch.setenv("CI_DATA_DIR", str(tmp_path))
    return GraphConfig.load("trading", profile="production")


@pytest.mark.parametrize("backend", ["sqlite", "memory", "dual_write"])
def test_g042_production_factory_rejects_explicit_local_primary(config, backend, tmp_path):
    path = tmp_path / "must-not-exist.db"
    with pytest.raises(GraphConfigError):
        create_graph_store(backend=backend, domain="trading", db_path=path, profile="production")
    assert not path.exists()


@pytest.mark.parametrize("profile", ["test", "offline", "development"])
@pytest.mark.parametrize("backend", ["sqlite", "memory"])
def test_g042_explicit_local_profiles_work(config, profile, backend, tmp_path):
    store = create_graph_store(backend=backend, domain="trading", profile=profile, db_path=tmp_path / "test.db")
    try:
        assert store.domain == "trading"
    finally:
        store.close()


def test_g042_test_flags_cannot_select_profile(config):
    with pytest.raises(GraphConfigError, match="test_mode"):
        create_graph_store(domain="trading", backend="age", test_mode=True, profile="production")
    with pytest.raises(GraphConfigError):
        replace(config, backend="sqlite", expected_backend="sqlite").require_shared_graph()
    with pytest.raises(GraphConfigError, match="soc_graph"):
        replace(config, graph="private_graph").require_shared_graph()
    with pytest.raises(GraphConfigError, match="missing AGE DSN"):
        replace(config, dsn=None).require_shared_graph()


def test_g042_profile_is_explicit_not_inferred(config, monkeypatch):
    monkeypatch.setenv("CI_ALLOW_SQLITE_FALLBACK", "1")
    assert resolve_profile(domain="trading") == "production"
    monkeypatch.setenv("GRAPH_PROFILE", "offline")
    assert GraphConfig.load("trading").profile == "offline"
    monkeypatch.setenv("TRADING_PROFILE", "test")
    assert GraphConfig.load("trading").profile == "test"
    assert GraphConfig.load("trading", profile="production").profile == "production"
    with pytest.raises(GraphConfigError, match="profile must"):
        GraphConfig.load("trading", profile="typo")


@pytest.mark.parametrize("kind", ["sqlite", "memory", "tenant", "declared", "unknown", "fake_age", "dual"])
def test_g042_scorer_checks_actual_primary_before_reads(config, kind):
    local = SQLiteGraphStore(":memory:", domain="trading") if kind == "sqlite" else InMemoryGraphStore(domain="trading")

    class Declared(GraphStoreWrapper):
        domain = "trading"
        def __init__(self):
            self._store = local

    class Unknown:
        backend = "age"
        domain = "trading"
        primary = local
        secondary = object()
        def __getattr__(self, name):
            return getattr(local, name)

    store = local
    if kind == "tenant":
        store = TenantScopedGraphStore(local)
    elif kind == "declared":
        store = Declared()
    elif kind == "dual":
        from copilot_sdk.graph.dual_write_store import DualWriteStore

        # No outbox construction is needed to prove a wrapper cannot make its
        # SQLite primary into an AGE primary.
        dual = object.__new__(DualWriteStore)
        dual.primary = local
        dual.secondary = Unknown()
        dual.domain = "trading"
        store = TenantScopedGraphStore(dual)
    elif kind in {"unknown", "fake_age"}:
        store = Unknown()
    try:
        with pytest.raises(RuntimeError, match="AGE-backed"):
            CompoundingScorer.from_preset("trading", graph_store=store, graph_config=config, profile="production")
    finally:
        local.close()


def test_g042_config_overrides_cannot_bypass_validation(config):
    for kwargs in ({"backend": "sqlite"}, {"profile": "test"}, {"domain": "s2p"}, {"dsn": "other"}, {"test_mode": True}):
        with pytest.raises(GraphConfigError, match="conflicts"):
            create_graph_store(config=config, **kwargs)


def test_g043_load_has_winning_key_provenance_without_mutation(config, monkeypatch):
    monkeypatch.setenv("TRADING_ACTIVE_AGE_DSN", "host=domain-specific password=hidden")
    before = dict(os.environ)
    loaded = GraphConfig.load("trading")
    assert dict(os.environ) == before
    assert dict(loaded.source_keys)["dsn"] == "TRADING_ACTIVE_AGE_DSN"
    assert dict(loaded.source_keys)["graph"] == "toml:defaults.graph"
    explicit = GraphConfig.load("trading", overrides={"dsn": "host=explicit"})
    assert dict(explicit.source_keys)["dsn"] == "argument:dsn"
    assert "hidden" not in repr(loaded)
    assert "unit-secret" not in repr(loaded)


def test_g043_mapping_load_does_not_read_or_change_process_settings(config):
    before = dict(os.environ)
    loaded = GraphConfig.load("dataops", profile="test", env={"GRAPH_BACKEND": "sqlite"})
    assert loaded.backend == "sqlite"
    assert dict(loaded.source_keys)["backend"] == "GRAPH_BACKEND"
    assert dict(os.environ) == before


def test_g043_default_cannot_supply_production_sqlite(config, monkeypatch):
    monkeypatch.setattr(GraphConfig, "_read_file", classmethod(lambda cls, domain, **kwargs: ({}, {})))
    with pytest.raises(GraphConfigError, match="missing AGE DSN"):
        GraphConfig.load("trading", env={})


def test_g043_all_five_compare_actual_identity_and_aliases(config, monkeypatch):
    identity = GraphIdentity("server-db-hash", "soc_graph", 42)
    monkeypatch.setattr("copilot_sdk.graph.production.probe_graph_identity", lambda dsn, graph: identity)
    configs = [GraphConfig.load(domain) for domain in ("soc", "trading", "purchasing", "dataops", "s2p")]
    for loaded in configs:
        assert loaded.require_shared_graph() == identity
        assert loaded.same_destination(configs[0])
    assert replace(config, dsn="host=alias").require_shared_graph() == identity


def test_g043_same_graph_name_on_other_database_is_rejected(config, monkeypatch):
    def probe(dsn, graph):
        return GraphIdentity("other-db" if "other" in dsn else "canonical-db", graph, 42)
    monkeypatch.setattr("copilot_sdk.graph.production.probe_graph_identity", probe)
    with pytest.raises(GraphConfigError, match="destination differs"):
        replace(config, dsn="host=other").require_shared_graph()
    assert not config.same_destination(replace(config, dsn="host=other"))


def test_g043_probe_is_read_only_redacted_and_checks_graph_oid(config):
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.execute.return_value.fetchone.return_value = ("123456789", 17, "private_db", 42, "soc_graph")
    client = SimpleNamespace(_graph="soc_graph", _connect_fresh=lambda **kwargs: conn)
    identity = _probe_client_identity(client)
    assert len(identity.database_id) == 64
    assert identity.graph_oid == 42
    assert "private_db" not in repr(identity)
    conn.execute.assert_any_call("SET TRANSACTION READ ONLY")
    conn.__exit__.assert_called_once()
    conn.execute.return_value.fetchone.return_value = None
    with pytest.raises(GraphConfigError, match="identity probe failed"):
        _probe_client_identity(client)

    def unavailable(**kwargs):
        raise ConnectionError("host=secret password=never-print-me")
    client._connect_fresh = unavailable
    with pytest.raises(GraphConfigError) as error:
        _probe_client_identity(client)
    assert "never-print-me" not in str(error.value)
    assert error.value.__suppress_context__


def test_g042_age_adapter_binding_rechecks_injected_destination(config, monkeypatch):
    from ci_platform.graph.age_sdk_adapter import AGEGraphStoreAdapter

    canonical = GraphIdentity("same-db", "soc_graph", 42)
    monkeypatch.setattr("copilot_sdk.graph.production._probe_client_identity", lambda client: canonical)
    store = create_graph_store(config=config)
    try:
        assert store.graph_capabilities.authoritative_backend == "age"
        assert store.graph_config is config
        assert validate_production_store(TenantScopedGraphStore(store), config).identity == canonical
        wrong = AGEGraphStoreAdapter(dsn="host=other", graph_name="soc_graph", domain="trading")
        monkeypatch.setattr("copilot_sdk.graph.production._probe_client_identity", lambda client: GraphIdentity(
            "other-db" if "other" in client._dsn else "same-db", "soc_graph", 42,
        ))
        try:
            with pytest.raises(GraphConfigError, match="destination differs"):
                validate_production_store(wrong, config)
        finally:
            wrong.close()
    finally:
        store.close()
