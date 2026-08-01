from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.main import DEFAULT_DB_PATH, PurchasingPathConfig
from copilot_sdk.config import GraphConfig


@contextmanager
def _temporary_env(name: str, value: str | None) -> Iterator[None]:
    previous = os.environ.get(name)
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = previous


def test_ci_data_dir_controls_sqlite_path(tmp_path: Path) -> None:
    data_dir = tmp_path / "ci-data"
    with _temporary_env("CI_DATA_DIR", str(data_dir)):
        config = PurchasingPathConfig.from_environment(None)

    assert Path(config.scoring_db) == data_dir / "purchasing.db"


def test_ci_data_dir_cannot_alter_graph_backend(tmp_path: Path) -> None:
    before = GraphConfig.load("purchasing")
    with _temporary_env("CI_DATA_DIR", str(tmp_path / "other")):
        after = GraphConfig.load("purchasing")

    assert after.backend == before.backend
    assert after.graph == before.graph
    assert after.dsn == before.dsn


def test_default_path_without_ci_data_dir() -> None:
    with _temporary_env("CI_DATA_DIR", None):
        config = PurchasingPathConfig.from_environment(None)

    assert Path(config.scoring_db) == DEFAULT_DB_PATH


def test_memory_db_for_test_profile() -> None:
    config = PurchasingPathConfig.from_environment(":memory:")

    assert config.scoring_db == ":memory:"
