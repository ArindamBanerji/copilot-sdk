"""Synthetic evidence ingestion still uses the real investigation/scoring path."""
from importlib import import_module
from pathlib import Path
import json
import shutil

import pytest
from fastapi.testclient import TestClient


def install_fixture(root: Path) -> Path:
    source = Path(__file__).resolve().parents[4] / "data/demo_fixtures/dataops_investigation_evidence.json"
    target = root / "demo_fixtures/investigation_evidence.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return target


def test_startup_loads_fixture_and_real_investigation_flips(dataops_data_dir: Path) -> None:
    install_fixture(dataops_data_dir)
    app = import_module("app.main").create_app(db_path=dataops_data_dir / "k14.db", demo_bundle_path=False)
    with TestClient(app) as client:
        before = client.get("/api/fingerprint").json()["decisions_analyzed"]
        response = client.post("/api/investigation/investigate", json={"decision_id": "PL-DO-5",
            "category": "pipeline_failure", "factor_vector": [0.5] * 6, "budget": 2, "use_K": True})
        assert response.status_code == 200
        body = response.json()
        assert body["action_changed"] is True
        assert body["surface_action"] != body["final_action"]
        assert body["steps"]
        assert all(step["evidence_source"].endswith(":synthetic") for step in body["steps"])
        assert client.get("/api/fingerprint").json()["decisions_analyzed"] == before


def test_import_requires_provenance_and_does_not_replace_real_data(tmp_path: Path) -> None:
    module = import_module("app.evidence_provider")
    path = install_fixture(tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.pop("planted")
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="provenance"):
        module.build_dataops_evidence_source(tmp_path)
    install_fixture(tmp_path)
    fallback = tmp_path / "fallback"
    fallback.mkdir()
    (fallback / "alerts.json").write_text(json.dumps({"alerts": [{"alert_id": "PL-DO-5"}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="overwrite"):
        module.build_dataops_evidence_source(tmp_path)


def test_without_explicit_import_no_planted_alert(tmp_path: Path) -> None:
    source = import_module("app.evidence_provider").build_dataops_evidence_source(tmp_path)
    assert "PL-DO-5" not in source["alerts"]
