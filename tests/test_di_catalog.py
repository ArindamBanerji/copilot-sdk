from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.di_router import create_di_router
from copilot_sdk.di.catalog import ExternalDataCatalog


def _catalog() -> ExternalDataCatalog:
    return ExternalDataCatalog()


def test_catalog_loads_entries() -> None:
    entries = _catalog().list_all()
    assert len(entries) >= 10
    assert entries[0].provider_id


def test_catalog_search_by_domain() -> None:
    entries = _catalog().for_domain("purchasing")
    assert entries
    assert all("purchasing" in entry.domains for entry in entries)


def test_catalog_search_by_cost_tier() -> None:
    entries = _catalog().search(cost_tier="free")
    assert entries
    assert all(entry.cost_tier == "free" for entry in entries)


def test_catalog_search_by_data_type() -> None:
    entries = _catalog().search(data_type="commodity")
    assert entries
    assert all(entry.data_type == "commodity" for entry in entries)


def test_catalog_get_by_id() -> None:
    entry = _catalog().get_by_id("openweathermap")
    assert entry is not None
    assert entry.provider_name == "OpenWeatherMap"


def test_catalog_estimated_value() -> None:
    assert _catalog().estimated_value("openweathermap", "purchasing") == 15.0
    assert _catalog().estimated_value("missing", "purchasing") == 0.0


def test_catalog_endpoint_returns_list() -> None:
    app = FastAPI()
    app.include_router(create_di_router({}, catalog=_catalog()), prefix="/api")
    response = TestClient(app).get("/api/di/catalog")
    assert response.status_code == 200
    assert response.json()["entries"]


def test_catalog_filters_work() -> None:
    app = FastAPI()
    app.include_router(create_di_router({}, catalog=_catalog()), prefix="/api")
    response = TestClient(app).get("/api/di/catalog", params={"domain": "purchasing", "cost_tier": "free"})
    assert response.status_code == 200
    entries = response.json()["entries"]
    assert entries
    assert all("purchasing" in entry["domains"] and entry["cost_tier"] == "free" for entry in entries)
