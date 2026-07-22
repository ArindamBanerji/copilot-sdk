from __future__ import annotations

from typing import Any

from copilot_sdk.graph.dual_write_store import DualWriteStore
from copilot_sdk.graph.factory import create_graph_store
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore


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
    store.close()


def test_dual_write_without_dsn_falls_back_to_sqlite(monkeypatch, tmp_path, caplog):
    monkeypatch.delenv("GRAPH_DSN", raising=False)
    monkeypatch.delenv("AGE_DSN", raising=False)
    with caplog.at_level("WARNING"):
        store = create_graph_store(backend="dual_write", domain="trading", db_path=tmp_path / "trading.db")
    assert isinstance(store, SQLiteGraphStore)
    assert "falling back to SQLite" in caplog.text
    store.close()


def test_sqlite_backend_is_unchanged(tmp_path):
    store = create_graph_store(backend="sqlite", domain="trading", db_path=tmp_path / "trading.db")
    assert isinstance(store, SQLiteGraphStore)
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
