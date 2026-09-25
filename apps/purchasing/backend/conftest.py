"""Scoped graph configuration for purchasing collection and tests."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pytest


@contextmanager
def _graph_environment(directory: Path) -> Iterator[None]:
    config = directory / "graph.toml"
    config.write_text(
        '[defaults]\ndsn = ""\ngraph = "test_graph"\n'
        '[copilot.purchasing]\ndomain = "purchasing"\n'
        'backend = "sqlite"\nexpected_backend = "sqlite"\nprefix = "PUR-"\n',
        encoding="utf-8",
    )
    with pytest.MonkeyPatch.context() as env:
        env.setenv("GRAPH_CONFIG_PATH", str(config))
        env.setenv("GRAPH_BACKEND", "sqlite")
        env.setenv("PURCHASING_ACTIVE_GRAPH_BACKEND", "sqlite")
        env.setenv("PURCHASING_PROFILE", "test")
        env.setenv("PURCHASING_SAMPLE_DATA", "1")
        env.setenv("CROSS_SIGNAL_DB_PATH", str(directory / "signals.db"))
        yield


@pytest.hookimpl(wrapper=True)
def pytest_make_collect_report(collector: pytest.Collector) -> Iterator[Any]:
    # Module-level app construction precedes fixture setup. Bound these writes
    # to collection too; always restore environment and remove temporary files.
    if not collector.path.is_relative_to(Path(__file__).parent):
        return (yield)
    with TemporaryDirectory(prefix="purchasing-collect-") as temporary:
        with _graph_environment(Path(temporary)):
            return (yield)


@pytest.fixture(autouse=True)
def isolated_graph_environment(tmp_path: Path) -> Iterator[None]:
    with _graph_environment(tmp_path):
        yield
