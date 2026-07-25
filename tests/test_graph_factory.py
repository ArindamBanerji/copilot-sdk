from __future__ import annotations

import pytest

from copilot_sdk.config import GraphConfigError
from copilot_sdk.graph.factory import create_graph_store
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore


def test_config_driven_age_requires_dsn(monkeypatch):
    monkeypatch.delenv("TRADING_ACTIVE_AGE_DSN", raising=False)
    monkeypatch.delenv("GRAPH_DSN", raising=False)
    monkeypatch.delenv("AGE_DSN", raising=False)
    with pytest.raises(GraphConfigError, match="missing AGE DSN"):
        create_graph_store(domain="trading")


def test_explicit_sqlite_remains_available_for_tests(tmp_path):
    store = create_graph_store(
        backend="sqlite", domain="test", db_path=tmp_path / "test.db", profile="test"
    )
    try:
        assert isinstance(store, SQLiteGraphStore)
    finally:
        store.close()


def test_dual_write_missing_dsn_fails_closed(tmp_path, monkeypatch):
    for name in ("GRAPH_DSN", "AGE_DSN", "GRAPH_NAME", "AGE_GRAPH_NAME", "SHARED_GRAPH_AUTHORIZED"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(GraphConfigError, match="dual_write backend requires an AGE DSN"):
        create_graph_store(
            backend="dual_write", domain="trading", db_path=tmp_path / "trading.db"
        )


def test_expected_age_resolving_to_sqlite_raises(monkeypatch, tmp_path):
    for name in (
        "TRADING_ACTIVE_AGE_DSN",
        "GRAPH_DSN",
        "AGE_DSN",
        "TRADING_ACTIVE_GRAPH_BACKEND",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("TRADING_ACTIVE_GRAPH_BACKEND", "sqlite")
    with pytest.raises(GraphConfigError, match="expected backend age"):
        create_graph_store(domain="trading", db_path=tmp_path / "trading.db")


def test_development_profile_allows_sqlite_fallback(monkeypatch, tmp_path):
    monkeypatch.setenv("TRADING_ACTIVE_GRAPH_BACKEND", "sqlite")
    monkeypatch.setenv("CI_ALLOW_SQLITE_FALLBACK", "1")
    store = create_graph_store(
        domain="trading",
        db_path=tmp_path / "trading.db",
        profile="development",
    )
    try:
        assert isinstance(store, SQLiteGraphStore)
    finally:
        store.close()


def test_wrong_backend_rejection():
    with pytest.raises(ValueError, match="invalid graph backend"):
        create_graph_store(backend="invalid", domain="trading")


def test_age_construction_with_valid_config(monkeypatch):
    class FakeAGEAdapter:
        def __init__(self, dsn: str, graph_name: str) -> None:
            self.dsn = dsn
            self.graph_name = graph_name

    monkeypatch.setattr(
        "copilot_sdk.graph.factory._load_age_adapter", lambda: FakeAGEAdapter
    )
    store = create_graph_store(
        backend="age",
        domain="trading",
        dsn="postgresql://example/test",
        graph_name="trading_graph",
    )
    assert isinstance(store, FakeAGEAdapter)
    assert store.dsn == "postgresql://example/test"
    assert store.graph_name == "trading_graph"


def test_soc_graph_authorization_preserved():
    with pytest.raises(ValueError, match="soc_graph"):
        create_graph_store(
            backend="age",
            domain="trading",
            dsn="postgresql://example/test",
            graph_name="soc_graph",
        )
