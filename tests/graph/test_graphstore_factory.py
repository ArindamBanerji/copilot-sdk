from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from copilot_sdk.graph.factory import create_graph_store
from copilot_sdk.graph.protocol import GraphStore
from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
from copilot_sdk.config import GraphConfigError


def test_graphstore_factory_requires_domain_when_backend_unset():
    with pytest.raises(GraphConfigError):
        create_graph_store(env={})


def test_graphstore_factory_explicit_sqlite_returns_sqlite():
    store = create_graph_store(backend="sqlite", domain="s2p", env={})
    try:
        assert isinstance(store, SQLiteGraphStore)
        assert store.domain == "s2p"
    finally:
        store.close()


def test_graphstore_factory_sqlite_uses_explicit_db_path(tmp_path: Path):
    db_path = tmp_path / "explicit.db"
    store = create_graph_store(backend="sqlite", domain="trading", db_path=db_path, env={})
    try:
        assert isinstance(store, SQLiteGraphStore)
        assert store.db_path == str(db_path)
    finally:
        store.close()


def test_graphstore_factory_sqlite_can_resolve_ci_data_dir(tmp_path: Path):
    store = create_graph_store(
        backend="sqlite",
        domain="purchasing",
        env={"CI_DATA_DIR": str(tmp_path)},
    )
    try:
        assert isinstance(store, SQLiteGraphStore)
        assert store.db_path == str(tmp_path / "purchasing.db")
    finally:
        store.close()


def test_graphstore_factory_rejects_invalid_backend():
    with pytest.raises(ValueError, match="invalid graph backend"):
        create_graph_store(backend="neo4j", env={})


def test_graphstore_factory_age_requires_dsn():
    with pytest.raises(ValueError, match="GRAPH_DSN"):
        create_graph_store(
            backend="age",
            domain="s2p",
            graph_name="product_graph",
            env={},
        )


def test_graphstore_factory_age_requires_graph_name():
    with pytest.raises(ValueError, match="GRAPH_NAME|graph"):
        create_graph_store(
            backend="age",
            domain="s2p",
            dsn="postgresql://example/test",
            env={},
        )


def test_graphstore_factory_age_rejects_blank_graph_name():
    with pytest.raises(ValueError, match="non-blank"):
        create_graph_store(
            backend="age",
            domain="s2p",
            dsn="postgresql://example/test",
            graph_name=" ",
            env={},
        )


def test_graphstore_factory_age_rejects_soc_graph_for_non_soc_write():
    with pytest.raises(ValueError, match="soc_graph"):
        create_graph_store(
            backend="age",
            domain="s2p",
            dsn="postgresql://example/test",
            graph_name="soc_graph",
            env={},
        )


def test_graphstore_factory_age_allows_protocol_v2_test_graph_only_in_test_mode(monkeypatch):
    fake_adapter = _install_fake_age_adapter(monkeypatch)

    with pytest.raises(ValueError, match="test_mode=True"):
        create_graph_store(
            backend="age",
            domain="s2p",
            dsn="postgresql://example/test",
            graph_name="protocol_v2_test_factory",
            env={},
        )

    store = create_graph_store(
        backend="age",
        domain="s2p",
        dsn="postgresql://example/test",
        graph_name="protocol_v2_test_factory",
        env={},
        test_mode=True,
    )
    assert isinstance(store, fake_adapter)
    assert store.graph_name == "protocol_v2_test_factory"


def test_graphstore_factory_age_alias_env_works_when_canonical_absent(monkeypatch):
    fake_adapter = _install_fake_age_adapter(monkeypatch)

    store = create_graph_store(
        backend="age",
        domain="dataops",
        env={
            "AGE_DSN": "postgresql://example/alias",
            "AGE_GRAPH_NAME": "product_graph",
        },
    )

    assert isinstance(store, fake_adapter)
    assert store.dsn == "postgresql://example/alias"
    assert store.graph_name == "product_graph"


def test_graphstore_factory_age_alias_conflict_raises():
    with pytest.raises(ValueError, match="GRAPH_DSN and AGE_DSN"):
        create_graph_store(
            backend="age",
            domain="s2p",
            graph_name="product_graph",
            env={
                "GRAPH_DSN": "postgresql://example/canonical",
                "AGE_DSN": "postgresql://example/alias",
            },
        )

    with pytest.raises(ValueError, match="GRAPH_NAME and AGE_GRAPH_NAME"):
        create_graph_store(
            backend="age",
            domain="s2p",
            dsn="postgresql://example/test",
            env={
                "GRAPH_NAME": "product_graph",
                "AGE_GRAPH_NAME": "other_product_graph",
            },
        )


def test_graphstore_factory_explicit_args_override_env_conflict(monkeypatch):
    fake_adapter = _install_fake_age_adapter(monkeypatch)

    store = create_graph_store(
        backend="age",
        domain="s2p",
        dsn="postgresql://example/explicit",
        graph_name="explicit_graph",
        env={
            "GRAPH_DSN": "postgresql://example/canonical",
            "AGE_DSN": "postgresql://example/alias",
            "GRAPH_NAME": "canonical_graph",
            "AGE_GRAPH_NAME": "alias_graph",
        },
    )

    assert isinstance(store, fake_adapter)
    assert store.dsn == "postgresql://example/explicit"
    assert store.graph_name == "explicit_graph"


def test_graphstore_factory_graph_domain_conflict_raises():
    with pytest.raises(ValueError, match="GRAPH_DOMAIN"):
        create_graph_store(domain="s2p", env={"GRAPH_DOMAIN": "trading"})


def test_graphstore_factory_does_not_read_database_url():
    with pytest.raises(ValueError, match="GRAPH_DSN"):
        create_graph_store(
            backend="age",
            domain="s2p",
            graph_name="product_graph",
            env={"DATABASE_URL": "postgresql://example/legacy"},
        )


def test_graphstore_factory_rejects_soc_graph_even_with_read_only_soc_projection_flag():
    with pytest.raises(ValueError, match="soc_graph"):
        create_graph_store(
            backend="age",
            domain="soc",
            dsn="postgresql://example/soc",
            graph_name="soc_graph",
            env={},
            read_only_soc_projection=True,
        )


def test_graphstore_factory_age_import_error_is_clear(monkeypatch):
    real_import = __import__("importlib").import_module

    def fail_age_import(name: str, package: str | None = None):
        if name == "ci_platform.graph.age_sdk_adapter":
            raise ImportError("missing ci-platform")
        return real_import(name, package)

    monkeypatch.setattr("importlib.import_module", fail_age_import)

    with pytest.raises(RuntimeError, match="AGE graph backend requires ci-platform"):
        create_graph_store(
            backend="age",
            domain="s2p",
            dsn="postgresql://example/test",
            graph_name="product_graph",
            env={},
        )


def test_graphstore_factory_close_remains_store_owned():
    store = create_graph_store(backend="sqlite", domain="test", db_path=":memory:")
    assert isinstance(store, SQLiteGraphStore)
    store.close()
    with pytest.raises(RuntimeError, match="closed"):
        _ = store.connection


def _install_fake_age_adapter(monkeypatch):
    class FakeAGEGraphStoreAdapter:
        def __init__(self, dsn: str | None = None, graph_name: str = "soc_graph", store=None):
            self.dsn = dsn
            self.graph_name = graph_name
            self.store = store

        def close(self) -> None:
            self.closed = True

    module = types.ModuleType("ci_platform.graph.age_sdk_adapter")
    module.AGEGraphStoreAdapter = FakeAGEGraphStoreAdapter
    monkeypatch.setitem(sys.modules, "ci_platform", types.ModuleType("ci_platform"))
    monkeypatch.setitem(sys.modules, "ci_platform.graph", types.ModuleType("ci_platform.graph"))
    monkeypatch.setitem(sys.modules, "ci_platform.graph.age_sdk_adapter", module)
    return FakeAGEGraphStoreAdapter
