from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.di_router import create_di_router
from copilot_sdk.di.models import SourceProfile


class FakeConnector:
    source_name = "erp"
    entity_type = "invoice"
    trust_tier = 1


class FakeProfiler:
    def __init__(self, source_name: str = "erp") -> None:
        self.connector = FakeConnector()
        self.connector.source_name = source_name
        self.calls: list[list[str]] = []
        self.sequence = 0

    def profile(self, entity_ids: list[str]) -> SourceProfile:
        self.calls.append(list(entity_ids))
        self.sequence += 1
        return SourceProfile(
            source_name=self.connector.source_name,
            entity_type=self.connector.entity_type,
            trust_tier=self.connector.trust_tier,
            freshness_score=0.8,
            completeness_score=0.7,
            consistency_score=0.5,
            validation_pass_rate=1.0,
            record_count=len(entity_ids),
            last_profiled=datetime(2026, 1, self.sequence, tzinfo=timezone.utc),
            overall_quality=0.75 + self.sequence / 100,
            errors=[],
        )


def _client(registry: dict[str, Any], ttl: int | None = 300) -> TestClient:
    app = FastAPI()
    app.include_router(create_di_router(registry, cache_ttl_seconds=ttl), prefix="/api")
    return TestClient(app)


def test_empty_registry_returns_empty_profiles():
    response = _client({}).get("/api/di/profiles")

    assert response.status_code == 200
    assert response.json() == {"sources": [], "total": 0}


def test_registered_source_appears_in_profiles():
    response = _client({"erp": FakeProfiler()}).get("/api/di/profiles")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["sources"][0]["source_name"] == "erp"
    assert payload["sources"][0]["has_profile"] is False
    assert payload["sources"][0]["cache_status"] == "not_profiled"


def test_registered_source_not_yet_profiled_returns_structured_status():
    response = _client({"erp": FakeProfiler()}).get("/api/di/profile/erp")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_name"] == "erp"
    assert payload["has_profile"] is False
    assert payload["cache_status"] == "not_profiled"
    assert payload["profile"] is None


def test_unknown_source_get_returns_404():
    response = _client({}).get("/api/di/profile/missing")

    assert response.status_code == 404


def test_unknown_source_refresh_returns_404():
    response = _client({}).post("/api/di/profile/missing/refresh", json={"entity_ids": ["A"]})

    assert response.status_code == 404


def test_empty_entity_ids_on_refresh_returns_400():
    response = _client({"erp": FakeProfiler()}).post("/api/di/profile/erp/refresh", json={"entity_ids": []})

    assert response.status_code == 400


def test_refresh_runs_profiler_and_caches_profile():
    profiler = FakeProfiler()
    client = _client({"erp": profiler})

    response = client.post("/api/di/profile/erp/refresh", json={"entity_ids": ["A", "B"]})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["profile"]["record_count"] == 2
    assert payload["cache_status"] == "fresh"
    assert profiler.calls == [["A", "B"]]


def test_get_after_refresh_returns_cached_profile_without_running_profiler():
    profiler = FakeProfiler()
    client = _client({"erp": profiler})
    assert client.post("/api/di/profile/erp/refresh", json={"entity_ids": ["A"]}).status_code == 200
    profiler.calls.clear()

    response = client.get("/api/di/profile/erp")

    assert response.status_code == 200
    payload = response.json()
    assert payload["has_profile"] is True
    assert payload["profile"]["record_count"] == 1
    assert profiler.calls == []


def test_second_refresh_overwrites_latest_profile():
    profiler = FakeProfiler()
    client = _client({"erp": profiler})

    assert client.post("/api/di/profile/erp/refresh", json={"entity_ids": ["A"]}).status_code == 200
    response = client.post("/api/di/profile/erp/refresh", json={"entity_ids": ["A", "B", "C"]})

    assert response.status_code == 200
    assert response.json()["profile"]["record_count"] == 3
    assert client.get("/api/di/profile/erp").json()["profile"]["record_count"] == 3


def test_ttl_metadata_reports_fresh_cache():
    client = _client({"erp": FakeProfiler()}, ttl=300)

    assert client.post("/api/di/profile/erp/refresh", json={"entity_ids": ["A"]}).status_code == 200
    payload = client.get("/api/di/profile/erp").json()

    assert payload["cache_status"] == "fresh"
    assert payload["is_stale"] is False
    assert isinstance(payload["age_seconds"], float)


def test_stale_get_returns_cached_profile_and_does_not_auto_run_profiler():
    profiler = FakeProfiler()
    client = _client({"erp": profiler}, ttl=-1)
    assert client.post("/api/di/profile/erp/refresh", json={"entity_ids": ["A"]}).status_code == 200
    profiler.calls.clear()

    payload = client.get("/api/di/profile/erp").json()

    assert payload["cache_status"] == "stale"
    assert payload["is_stale"] is True
    assert payload["profile"]["record_count"] == 1
    assert profiler.calls == []


def test_response_model_serialization_in_profiles_list():
    client = _client({"erp": FakeProfiler()})

    assert client.post("/api/di/profile/erp/refresh", json={"entity_ids": ["A"]}).status_code == 200
    payload = client.get("/api/di/profiles").json()

    source = payload["sources"][0]
    assert source["latest_profile"]["last_profiled"] == "2026-01-01T00:00:00+00:00"
    assert source["latest_profile"]["source_name"] == "erp"


def test_dataops_app_mounts_di_profiles_empty_registry():
    backend_root = Path(__file__).resolve().parents[1] / "apps" / "dataops" / "backend"
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))
    from app.main import create_app

    client = TestClient(create_app(db_path=":memory:", demo_bundle_path=False))

    response = client.get("/api/di/profiles")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert {source["source_name"] for source in payload["sources"]} == {
        "airflow",
        "dbt",
        "snowflake",
    }


def _dataops_app():
    backend_root = Path(__file__).resolve().parents[1] / "apps" / "dataops" / "backend"
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))
    from app.main import create_app

    return create_app(db_path=":memory:", demo_bundle_path=False)


def test_snowflake_in_profiler_registry():
    app = _dataops_app()

    assert "snowflake" in app.state.dataops_profiler_registry


def test_dbt_in_profiler_registry():
    app = _dataops_app()

    assert "dbt" in app.state.dataops_profiler_registry


def test_airflow_in_profiler_registry():
    app = _dataops_app()

    assert "airflow" in app.state.dataops_profiler_registry


def test_profiles_endpoint_includes_snowflake():
    response = TestClient(_dataops_app()).get("/api/di/profiles")

    assert response.status_code == 200
    sources = [source["source_name"] for source in response.json()["sources"]]
    assert "snowflake" in sources


def test_profiles_endpoint_includes_dbt():
    response = TestClient(_dataops_app()).get("/api/di/profiles")

    assert response.status_code == 200
    sources = [source["source_name"] for source in response.json()["sources"]]
    assert "dbt" in sources


def test_profiles_endpoint_includes_airflow():
    response = TestClient(_dataops_app()).get("/api/di/profiles")

    assert response.status_code == 200
    sources = [source["source_name"] for source in response.json()["sources"]]
    assert "airflow" in sources


def test_intelligence_map_has_connector_nodes():
    response = TestClient(_dataops_app()).get("/api/di/intelligence-map")

    assert response.status_code == 200
    labels = {node["label"] for node in response.json()["nodes"]}
    assert {"orders", "stg_orders", "etl_orders"} <= labels


def test_connector_provenance_demo():
    app = _dataops_app()
    backend_root = Path(__file__).resolve().parents[1] / "apps" / "dataops" / "backend"
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))
    from app.main import _dataops_intelligence_map_sources

    sources = _dataops_intelligence_map_sources(app.state.dataops_profiler_registry)

    assert sources
    assert all(source["provenance"] == "demo" for source in sources)


def test_profiled_snowflake_has_quality():
    app = _dataops_app()

    assert app.state.dataops_profiles["snowflake"]["overall_quality"] > 0


def test_profiled_dbt_has_quality():
    app = _dataops_app()

    assert app.state.dataops_profiles["dbt"]["overall_quality"] > 0


def test_profiled_airflow_has_quality():
    app = _dataops_app()

    assert app.state.dataops_profiles["airflow"]["overall_quality"] > 0


def test_profiles_endpoint_has_data():
    response = TestClient(_dataops_app()).get("/api/di/profiles")

    assert response.status_code == 200
    sources = response.json()["sources"]
    assert sources
    assert all(source["has_profile"] is True for source in sources)
    assert all(source["latest_profile"]["overall_quality"] > 0 for source in sources)
