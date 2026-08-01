from __future__ import annotations

import os
from contextlib import contextmanager
from collections.abc import Iterator

import pytest

from copilot_sdk.config import GraphConfig, GraphConfigError, require_shared_graph


@contextmanager
def _graph_environment(*, graph: str, backend: str = "age") -> Iterator[None]:
    keys = ("GRAPH_BACKEND", "GRAPH_DSN", "GRAPH_NAME", "AGE_GRAPH_NAME")
    previous = {key: os.environ.get(key) for key in keys}
    try:
        os.environ["GRAPH_BACKEND"] = backend
        os.environ["GRAPH_DSN"] = "host=test dbname=soc_copilot"
        os.environ["GRAPH_NAME"] = graph
        os.environ.pop("AGE_GRAPH_NAME", None)
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _assert_startup_config(domain: str) -> None:
    config = GraphConfig.load(domain, profile="production")
    assert config.graph == "soc_graph"
    require_shared_graph(
        backend=config.backend,
        graph=config.graph,
        domain=domain,
        profile="production",
        test_mode=config.active_test_mode,
    )


def test_age_production_requires_soc_graph() -> None:
    require_shared_graph(
        backend="age", graph="soc_graph", domain="trading", profile="production"
    )


def test_age_production_rejects_non_soc_graph() -> None:
    with pytest.raises(GraphConfigError, match="soc_graph"):
        require_shared_graph(
            backend="age", graph="my_other_graph", domain="trading", profile="production"
        )


def test_age_production_rejects_omitted_graph_name() -> None:
    with pytest.raises(GraphConfigError, match="soc_graph"):
        require_shared_graph(
            backend="age", graph=None, domain="trading", profile="production"
        )


def test_sqlite_allows_any_graph_name() -> None:
    require_shared_graph(
        backend="sqlite", graph="local_scratch_graph", domain="trading", profile="production"
    )


def test_test_profile_allows_non_soc_graph() -> None:
    require_shared_graph(
        backend="age",
        graph="protocol_v2_test_scratch",
        domain="trading",
        profile="test",
        test_mode=True,
    )


def test_trading_startup_resolves_soc_graph() -> None:
    with _graph_environment(graph="soc_graph"):
        _assert_startup_config("trading")


def test_purchasing_startup_resolves_soc_graph() -> None:
    with _graph_environment(graph="soc_graph"):
        _assert_startup_config("purchasing")


def test_dataops_startup_resolves_soc_graph() -> None:
    with _graph_environment(graph="soc_graph"):
        _assert_startup_config("dataops")


def test_s2p_startup_resolves_soc_graph() -> None:
    with _graph_environment(graph="soc_graph"):
        _assert_startup_config("s2p")


def test_soc_startup_resolves_soc_graph() -> None:
    with _graph_environment(graph="soc_graph"):
        _assert_startup_config("soc")


def test_five_configs_same_graph() -> None:
    with _graph_environment(graph="soc_graph"):
        configs = [
            GraphConfig.load(domain, profile="production")
            for domain in ("soc", "trading", "purchasing", "dataops", "s2p")
        ]
    assert {config.graph for config in configs} == {"soc_graph"}
    assert len({config.dsn for config in configs}) == 1
