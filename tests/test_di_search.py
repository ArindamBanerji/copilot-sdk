from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.di_router import create_di_router
from copilot_sdk.connectors.mock_airflow import MockAirflowConnector
from copilot_sdk.connectors.mock_dbt import MockDBTConnector
from copilot_sdk.connectors.mock_snowflake import MockSnowflakeConnector
from copilot_sdk.di.search_service import DISearchService


def _service() -> DISearchService:
    return DISearchService([MockDBTConnector(), MockAirflowConnector(), MockSnowflakeConnector()], None)


def test_search_returns_results() -> None:
    result = _service().search("orders")
    assert result.results
    assert all("orders" in asset.asset_name for asset in result.results)


def test_search_filters_by_trust_tier() -> None:
    result = _service().search("", {"trust_tier": 1})
    assert result.results
    assert all(asset.trust_tier == 1 for asset in result.results)


def test_search_filters_by_freshness() -> None:
    result = _service().search("", {"freshness_max": 2})
    assert result.results
    assert all(asset.freshness_hours is not None and asset.freshness_hours <= 2 for asset in result.results)


def test_search_filters_by_quality_status() -> None:
    result = _service().search("", {"quality_status": "stale"})
    assert result.results
    assert all(asset.quality_status == "stale" for asset in result.results)


def test_search_ranks_by_quality() -> None:
    assets = _service().search("").results
    assert assets[0].trust_score >= assets[-1].trust_score


def test_search_empty_query_returns_all() -> None:
    result = _service().search("")
    assert result.total == 33


def test_search_combined_filters() -> None:
    result = _service().search("", {"trust_tier": 1, "quality_status": "healthy", "iks_min": 90})
    assert result.results
    assert all(asset.trust_tier == 1 and asset.quality_status == "healthy" and asset.iks >= 90 for asset in result.results)


def test_search_limit_respected() -> None:
    result = _service().search("", {"limit": 4})
    assert len(result.results) == 4
    assert result.total == 33


def test_search_endpoint_isolated() -> None:
    app = FastAPI()
    app.include_router(create_di_router({}, search_service=_service()), prefix="/api")
    response = TestClient(app).get("/api/di/search", params={"q": "orders", "trust_tier": 1})
    assert response.status_code == 200
    assert response.json()["results"]
