from __future__ import annotations

from typing import Any

import pytest

from copilot_sdk.graph.dual_write_store import DualWriteStore
from copilot_sdk.graph.factory import create_graph_store
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
from copilot_sdk.config import GraphConfigError


class FactoryAGEAdapter:  # MOCK-OK: factory external adapter loading boundary.
    def __init__(self, dsn: str, graph_name: str) -> None:
        self.dsn = dsn
        self.graph_name = graph_name

    def __getattr__(self, name: str) -> Any:
        return lambda *args, **kwargs: None


def _patch_age_adapter(monkeypatch) -> None:
    monkeypatch.setattr("copilot_sdk.graph.factory._load_age_adapter", lambda: FactoryAGEAdapter)


def test_dual_write_with_dsn_constructs_wrapper(monkeypatch, tmp_path):
    _patch_age_adapter(monkeypatch)
    store = create_graph_store(
        backend="dual_write",
        domain="trading",
        db_path=tmp_path / "trading.db",
        dsn="postgres://test",
        graph_name="dual_write_test",
    )
    assert isinstance(store, DualWriteStore)
    assert store._outbox is not None
    assert (tmp_path / "trading_dual_write_outbox.db").is_file()
    store.close()


def test_dual_write_without_dsn_fails_closed(monkeypatch, tmp_path, caplog):
    monkeypatch.delenv("GRAPH_DSN", raising=False)
    monkeypatch.delenv("AGE_DSN", raising=False)
    with caplog.at_level("WARNING"), pytest.raises(GraphConfigError):
        create_graph_store(backend="dual_write", domain="trading", db_path=tmp_path / "trading.db")


def test_sqlite_backend_is_unchanged(tmp_path):
    store = create_graph_store(backend="sqlite", domain="trading", db_path=tmp_path / "trading.db")
    assert isinstance(store, SQLiteGraphStore)
    assert not hasattr(store, "_durable_outbox")
    store.close()


def test_age_backend_is_unchanged(monkeypatch):
    _patch_age_adapter(monkeypatch)
    store = create_graph_store(backend="age", domain="trading", dsn="postgres://test", graph_name="age_test")
    assert isinstance(store, FactoryAGEAdapter)


def test_dual_write_factory_uses_sqlite_primary_and_age_secondary(monkeypatch, tmp_path):
    _patch_age_adapter(monkeypatch)
    store = create_graph_store(
        backend="dual_write",
        domain="trading",
        db_path=tmp_path / "trading.db",
        dsn="postgres://test",
        graph_name="dual_write_test",
    )
    assert isinstance(store, DualWriteStore)
    assert isinstance(store.primary, SQLiteGraphStore)
    assert isinstance(store.secondary, FactoryAGEAdapter)
    store.close()


def test_dual_write_uses_graph_domain_when_no_graph_name_is_supplied(monkeypatch, tmp_path):
    _patch_age_adapter(monkeypatch)
    store = create_graph_store(
        backend="dual_write",
        domain="trading",
        db_path=tmp_path / "trading.db",
        env={"GRAPH_DOMAIN": "trading", "AGE_DSN": "postgres://test"},
    )
    assert isinstance(store, DualWriteStore)
    assert store.secondary.graph_name == "trading"
    store.close()


def test_dual_write_authorized_shared_soc_graph_constructs(monkeypatch, tmp_path):
    _patch_age_adapter(monkeypatch)
    store = create_graph_store(
        backend="dual_write",
        domain="trading",
        db_path=tmp_path / "trading.db",
        dsn="postgres://test",
        graph_name="soc_graph",
        env={"SHARED_GRAPH_AUTHORIZED": "trading:soc_graph"},
    )
    assert isinstance(store, DualWriteStore)
    assert store.secondary.graph_name == "soc_graph"
    store.close()


@pytest.mark.parametrize("authorization", [None, "purchasing:soc_graph"])
def test_dual_write_shared_soc_graph_requires_matching_pair(monkeypatch, tmp_path, authorization):
    _patch_age_adapter(monkeypatch)
    env = {} if authorization is None else {"SHARED_GRAPH_AUTHORIZED": authorization}
    with pytest.raises(ValueError, match="SHARED_GRAPH_AUTHORIZED=trading:soc_graph"):
        create_graph_store(
            backend="dual_write",
            domain="trading",
            db_path=tmp_path / "trading.db",
            dsn="postgres://test",
            graph_name="soc_graph",
            env=env,
        )


@pytest.mark.parametrize("domain", ["trading", "purchasing"])
def test_dual_write_multiple_shared_soc_authorizations_permit_each(monkeypatch, tmp_path, domain):
    _patch_age_adapter(monkeypatch)
    store = create_graph_store(
        backend="dual_write",
        domain=domain,
        db_path=tmp_path / f"{domain}.db",
        dsn="postgres://test",
        graph_name="soc_graph",
        env={"SHARED_GRAPH_AUTHORIZED": "trading:soc_graph,purchasing:soc_graph"},
    )
    assert isinstance(store, DualWriteStore)
    store.close()


def test_sqlite_backend_still_rejects_shared_soc_graph(monkeypatch, tmp_path):
    _patch_age_adapter(monkeypatch)
    with pytest.raises(ValueError, match="soc_graph is forbidden"):
        create_graph_store(
            backend="age",
            domain="trading",
            dsn="postgres://test",
            graph_name="soc_graph",
            env={"SHARED_GRAPH_AUTHORIZED": "trading:soc_graph"},
        )


def test_active_path_can_pass_explicit_shared_soc_authorization(monkeypatch):
    _patch_age_adapter(monkeypatch)
    store = create_graph_store(
        backend="age",
        domain="trading",
        dsn="postgres://test",
        graph_name="soc_graph",
        env={},
        shared_graph_authorization="trading:soc_graph",
    )
    assert isinstance(store, FactoryAGEAdapter)
    assert store.graph_name == "soc_graph"


def test_dual_write_non_shared_graph_needs_no_authorization(monkeypatch, tmp_path):
    _patch_age_adapter(monkeypatch)
    store = create_graph_store(
        backend="dual_write",
        domain="trading",
        db_path=tmp_path / "trading.db",
        dsn="postgres://test",
        graph_name="trading_graph",
        env={},
    )
    assert isinstance(store, DualWriteStore)
    store.close()
