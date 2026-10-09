"""Readiness caching must skip unavailable AGE without substituting a backend."""

from functools import lru_cache
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import psycopg
import pytest

from copilot_sdk.config import GraphConfigError
from copilot_sdk.testing import fixtures


@pytest.fixture
def isolated_probe(monkeypatch):
    # Preserve the session's real readiness cache while exercising a fresh one.
    monkeypatch.setattr(fixtures, "_probe_age", lru_cache(maxsize=None)(fixtures._probe_age.__wrapped__))


def test_disposable_age_skips_82_consumers_after_one_probe(monkeypatch, isolated_probe):
    spec = importlib.util.spec_from_file_location(
        "runtime_root_conftest", Path(__file__).resolve().parents[1] / "conftest.py"
    )
    assert spec is not None and spec.loader is not None
    root = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(root)
    monkeypatch.setattr(root, "_TEST_DSN", "postgresql://unavailable/test")
    connect = MagicMock(side_effect=psycopg.OperationalError("unreachable"))
    monkeypatch.setattr(psycopg, "connect", connect)
    for _ in range(82):
        fixture = root.disposable_age.__wrapped__()
        with pytest.raises(pytest.skip.Exception, match="AGE is not reachable"):
            next(fixture)
    connect.assert_called_once_with(root._TEST_DSN, connect_timeout=3, autocommit=True)


def test_readiness_cache_is_per_dsn_and_reuses_default(monkeypatch, isolated_probe):
    monkeypatch.setattr(fixtures, "age_test_dsn", lambda: "postgresql://primary/test")
    connect = MagicMock()
    monkeypatch.setattr(psycopg, "connect", connect)
    assert fixtures.age_available()
    assert fixtures.age_available("postgresql://primary/test")
    assert fixtures.age_available("postgresql://other/test")
    assert fixtures.age_available("postgresql://other/test")
    assert connect.call_count == 2
    assert connect.return_value.__exit__.call_count == 2


def test_missing_dsn_does_not_connect_or_raise(monkeypatch, isolated_probe):
    monkeypatch.delenv("AGE_TEST_DSN", raising=False)
    load = MagicMock(side_effect=GraphConfigError("missing AGE DSN"))
    monkeypatch.setattr(fixtures.GraphConfig, "load", load)
    monkeypatch.setattr(fixtures, "age_test_dsn", lru_cache(maxsize=1)(fixtures.age_test_dsn.__wrapped__))
    connect = MagicMock()
    monkeypatch.setattr(psycopg, "connect", connect)
    assert fixtures.age_test_dsn() == ""
    assert not fixtures.age_available()
    assert not fixtures.age_available()
    load.assert_called_once_with("trading")
    connect.assert_not_called()


def test_explicit_test_dsn_is_captured_before_environment_mutation(monkeypatch):
    monkeypatch.setattr(fixtures, "age_test_dsn", lru_cache(maxsize=1)(fixtures.age_test_dsn.__wrapped__))
    monkeypatch.setenv("AGE_TEST_DSN", "postgresql://explicit/test")
    load = MagicMock(side_effect=AssertionError("explicit test DSN must win"))
    monkeypatch.setattr(fixtures.GraphConfig, "load", load)
    assert fixtures.age_test_dsn() == "postgresql://explicit/test"
    monkeypatch.setenv("AGE_TEST_DSN", "postgresql://temporary/test")
    assert fixtures.age_test_dsn() == "postgresql://explicit/test"
    load.assert_not_called()
