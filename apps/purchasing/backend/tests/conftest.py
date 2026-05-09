from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]

for path in (BACKEND_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app import context_router  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture
def temp_data_dir(tmp_path, monkeypatch) -> Path:
    source_data = BACKEND_ROOT / "data"
    temp_data = tmp_path / "data"
    temp_data.mkdir()
    for filename in (
        "waste_history.json",
        "weather_cache.json",
        "evolution_fixtures.json",
        "purchasing_seed_v2.json",
        "analytics_cache.json",
    ):
        (temp_data / filename).write_text(
            (source_data / filename).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    (temp_data / "order_metadata.json").write_text(
        json.dumps({}, indent=2),
        encoding="utf-8",
    )

    monkeypatch.setattr(context_router, "_DATA_DIR", temp_data)
    import app.main as main_module

    monkeypatch.setattr(main_module, "DATA_DIR", temp_data)
    return temp_data


@pytest.fixture
def client(tmp_path, temp_data_dir) -> TestClient:
    app = create_app(db_path=tmp_path / "purchasing_test.db")
    return TestClient(app)
