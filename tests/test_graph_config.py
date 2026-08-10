from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest

from copilot_sdk.config import GraphConfig, GraphConfigError


DOMAINS = ("soc", "trading", "purchasing", "dataops", "s2p")
ENV_KEYS = (
    "GRAPH_CONFIG_PATH", "GRAPH_BACKEND", "GRAPH_DSN", "AGE_DSN", "GRAPH_NAME",
    "AGE_GRAPH_NAME", "GRAPH_DOMAIN", "CI_ALLOW_SQLITE_FALLBACK",
    "TRADING_ACTIVE_GRAPH_BACKEND", "TRADING_ACTIVE_AGE_DSN", "TRADING_ACTIVE_AGE_GRAPH",
    "TRADING_ACTIVE_AGE_DOMAIN", "PURCHASING_ACTIVE_GRAPH_BACKEND",
    "PURCHASING_ACTIVE_AGE_DSN", "PURCHASING_ACTIVE_AGE_GRAPH", "DATAOPS_ACTIVE_GRAPH_BACKEND",
    "DATAOPS_ACTIVE_AGE_DSN", "DATAOPS_ACTIVE_AGE_GRAPH", "S2P_ACTIVE_GRAPH_BACKEND",
    "S2P_ACTIVE_AGE_DSN", "S2P_ACTIVE_AGE_GRAPH", "S2P_ACTIVE_AGE_DOMAIN",
    "DATAOPS_ACTIVE_AGE_DOMAIN", "PURCHASING_ACTIVE_AGE_DOMAIN",
    "TRADING_ACTIVE_AGE_TEST_MODE", "PURCHASING_ACTIVE_AGE_TEST_MODE",
    "DATAOPS_ACTIVE_AGE_TEST_MODE", "DATAOPS_ACTIVE_LIVE_AGE_TEST",
    "S2P_ACTIVE_AGE_TEST_MODE", "TRADING_SHADOW_AGE", "PURCHASING_SHADOW_AGE",
    "DATAOPS_SHADOW_AGE", "S2P_SHADOW_AGE", "NARRATIVE_PROVIDER",
)


def clear_graph_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def write_config(path: Path, *, backend: str = "sqlite", expected: str = "sqlite") -> None:
    path.write_text(
        "[defaults]\n"
        f'backend = "{backend}"\n'
        f'expected_backend = "{expected}"\n'
        'dsn = ""\n'
        'graph = "soc_graph"\n'
        "[copilot.trading]\n"
        'domain = "trading"\n'
        'prefix = "TRD-"\n'
        'port = 8010\n',
        encoding="utf-8",
    )


def test_load_from_toml_for_each_domain(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_graph_env(monkeypatch)
    monkeypatch.setenv("GRAPH_BACKEND", "age")
    monkeypatch.setenv("GRAPH_DSN", "host=test password=secret")
    for domain in DOMAINS:
        config = GraphConfig.load(domain)
        assert config.domain == domain
        assert config.backend == "age"
        assert config.graph == "soc_graph"
        assert not hasattr(config, "graph_uri")
        assert not hasattr(config, "graph_password")


def test_env_override_wins_and_source_is_recorded(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    clear_graph_env(monkeypatch)
    config_path = tmp_path / "config.toml"
    write_config(config_path)
    monkeypatch.setenv("GRAPH_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("GRAPH_BACKEND", "age")
    monkeypatch.setenv("GRAPH_DSN", "host=test password=secret")
    config = GraphConfig.load("trading")
    assert config.backend == "age"
    assert dict(config.sources)["backend"] == "env"


def test_collision_warning_contains_values_and_winner(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    clear_graph_env(monkeypatch)
    config_path = tmp_path / "config.toml"
    write_config(config_path)
    monkeypatch.setenv("GRAPH_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("GRAPH_BACKEND", "age")
    monkeypatch.setenv("GRAPH_DSN", "host=test password=secret")
    with caplog.at_level(logging.WARNING):
        GraphConfig.load("trading")
    assert "field=backend" in caplog.text
    assert "file=sqlite" in caplog.text
    assert "env=age" in caplog.text
    assert "winner=env" in caplog.text


def test_missing_dsn_for_age_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    clear_graph_env(monkeypatch)
    config_path = tmp_path / "config.toml"
    write_config(config_path, backend="age", expected="age")
    monkeypatch.setenv("GRAPH_CONFIG_PATH", str(config_path))
    with pytest.raises(GraphConfigError, match="missing AGE DSN"):
        GraphConfig.load("trading")


def test_missing_graph_for_age_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    clear_graph_env(monkeypatch)
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        '[defaults]\nbackend = "age"\nexpected_backend = "age"\n'
        'dsn = "host=test"\ngraph = ""\n[ copilot ]\n',
        encoding="utf-8",
    )
    # Replace malformed optional table with a valid minimal document.
    config_path.write_text(
        '[defaults]\nbackend = "age"\nexpected_backend = "age"\n'
        'dsn = "host=test"\ngraph = ""\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("GRAPH_CONFIG_PATH", str(config_path))
    with pytest.raises(GraphConfigError, match="missing AGE graph"):
        GraphConfig.load("trading")


def test_expected_age_rejects_sqlite(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    clear_graph_env(monkeypatch)
    config_path = tmp_path / "config.toml"
    write_config(config_path, backend="sqlite", expected="age")
    monkeypatch.setenv("GRAPH_CONFIG_PATH", str(config_path))
    with pytest.raises(GraphConfigError, match="expected backend age"):
        GraphConfig.load("trading")


def test_development_explicit_fallback_is_allowed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    clear_graph_env(monkeypatch)
    config_path = tmp_path / "config.toml"
    write_config(config_path, backend="sqlite", expected="age")
    monkeypatch.setenv("GRAPH_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("CI_ALLOW_SQLITE_FALLBACK", "1")
    config = GraphConfig.load("trading", profile="development")
    assert config.backend == "sqlite"


def test_authorization_is_derived(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_graph_env(monkeypatch)
    monkeypatch.setenv("GRAPH_BACKEND", "age")
    monkeypatch.setenv("GRAPH_DSN", "host=test")
    config = GraphConfig.load("trading")
    assert config.authorized == f"{config.domain}:{config.graph}"


def test_source_tracking_populates_every_field(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_graph_env(monkeypatch)
    monkeypatch.setenv("GRAPH_BACKEND", "age")
    monkeypatch.setenv("GRAPH_DSN", "host=test")
    config = GraphConfig.load("trading")
    expected = {"domain", "backend", "expected_backend", "dsn", "graph", "prefix",
                "active_test_mode", "shadow_age", "live_age_test", "port"}
    source_map = dict(config.sources)
    assert expected <= set(source_map)
    assert set(source_map.values()) <= {"env", "file", "default"}


def test_dsn_is_redacted_from_collision_log(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    clear_graph_env(monkeypatch)
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        '[defaults]\nbackend = "sqlite"\nexpected_backend = "sqlite"\n'
        'dsn = "file-secret"\ngraph = "soc_graph"\n', encoding="utf-8"
    )
    monkeypatch.setenv("GRAPH_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("GRAPH_DSN", "env-secret")
    with caplog.at_level(logging.WARNING):
        GraphConfig.load("trading")
    assert "file-secret" not in caplog.text
    assert "env-secret" not in caplog.text
    assert "<redacted>" in caplog.text


def test_search_is_package_relative_not_cwd(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    clear_graph_env(monkeypatch)
    monkeypatch.setenv("GRAPH_BACKEND", "age")
    monkeypatch.setenv("GRAPH_DSN", "host=test")
    monkeypatch.chdir(tmp_path)
    config = GraphConfig.load("trading")
    assert config.prefix == "TRD-"
    assert config.graph == "soc_graph"


def test_requested_domain_mismatch_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_graph_env(monkeypatch)
    monkeypatch.setenv("GRAPH_BACKEND", "age")
    monkeypatch.setenv("GRAPH_DSN", "host=test")
    monkeypatch.setenv("TRADING_ACTIVE_AGE_DOMAIN", "purchasing")
    with pytest.raises(GraphConfigError, match="Domain mismatch"):
        GraphConfig.load("trading")


def test_nonexistent_config_path_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    clear_graph_env(monkeypatch)
    missing = tmp_path / "missing.toml"
    monkeypatch.setenv("GRAPH_CONFIG_PATH", str(missing))
    with pytest.raises(GraphConfigError, match="does not exist"):
        GraphConfig.load("trading")


def test_malformed_toml_raises_graph_config_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    clear_graph_env(monkeypatch)
    malformed = tmp_path / "bad.toml"
    malformed.write_text("[defaults\nbackend = 'age'", encoding="utf-8")
    monkeypatch.setenv("GRAPH_CONFIG_PATH", str(malformed))
    with pytest.raises(GraphConfigError, match="Malformed TOML"):
        GraphConfig.load("trading")


def test_dual_write_backend_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_graph_env(monkeypatch)
    monkeypatch.setenv("GRAPH_BACKEND", "dual_write")
    monkeypatch.setenv("GRAPH_DSN", "host=test")
    config = GraphConfig.load("trading")
    assert config.backend == "dual_write"


def test_file_only_sqlite_profile_loads_without_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    clear_graph_env(monkeypatch)
    config_path = tmp_path / "file_only.toml"
    write_config(config_path, backend="sqlite", expected="sqlite")
    monkeypatch.setenv("GRAPH_CONFIG_PATH", str(config_path))
    config = GraphConfig.load("trading", profile="development")
    assert config.backend == "sqlite"
    assert dict(config.sources)["backend"] == "file"
