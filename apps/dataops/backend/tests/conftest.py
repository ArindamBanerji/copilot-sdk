from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
WORKSPACE_ROOT = REPO_ROOT.parent
CI_PLATFORM_ROOT = WORKSPACE_ROOT / "ci-platform"

for path in (BACKEND_ROOT, REPO_ROOT, CI_PLATFORM_ROOT):
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))


@pytest.fixture()
def dataops_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.delenv("GRAPH_DSN", raising=False)

    source = BACKEND_ROOT / "data"
    target = tmp_path / "data"
    target.mkdir()
    fallback = target / "fallback"
    fallback.mkdir()

    for name in (
        "evolution_fixtures.json",
        "ae_impact.json",
        "incident.json",
        "conservation_history.json",
        "process_signals.json",
        "transformations.json",
        "schema_changes.json",
    ):
        shutil.copyfile(source / name, target / name)

    for name in ("pipelines.json", "alerts.json", "blast_radius.json"):
        shutil.copyfile(source / "fallback" / name, fallback / name)

    (target / "alert_metadata.json").write_text("{}\n", encoding="utf-8")

    from app import ae_router, context_router, main

    monkeypatch.setattr(context_router, "DATA_DIR", target)
    monkeypatch.setattr(context_router, "METADATA_PATH", target / "alert_metadata.json")
    monkeypatch.setattr(ae_router, "DATA_DIR", target)
    monkeypatch.setattr(main, "DATA_DIR", target)
    monkeypatch.setattr(main, "DEFAULT_DB_PATH", target / "dataops.db")
    return target


@pytest.fixture()
def client(dataops_data_dir: Path) -> TestClient:
    from app.main import create_app

    app = create_app(db_path=dataops_data_dir / "test_dataops.db")
    return TestClient(app)
