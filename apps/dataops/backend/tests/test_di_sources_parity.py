"""Verify /api/di/sources returns the same populated data as /api/di/profiles."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from copilot_sdk.config import GraphConfig


@pytest.fixture()
def client() -> TestClient:
    config = GraphConfig.load("dataops", profile="test")
    app = create_app(db_path=":memory:", demo_bundle_path=False, graph_config=config)
    return TestClient(app)


class TestDISourcesParity:
    """Endpoints /api/di/sources and /api/di/profiles must agree."""

    def test_sources_returns_populated_profiles(self, client: TestClient) -> None:
        """Sources endpoint returns real profile data, not empty cache."""
        resp = client.get("/api/di/sources")
        assert resp.status_code == 200
        data = resp.json()
        assert "sources" in data
        assert data["total"] > 0
        for source in data["sources"]:
            assert source["has_profile"] is True, (
                f"{source['source_name']} should be profiled"
            )
            assert source["latest_profile"] is not None, (
                f"{source['source_name']} should have profile data"
            )

    def test_sources_matches_profiles(self, client: TestClient) -> None:
        """Sources and profiles endpoints return identical data."""
        profiles_resp = client.get("/api/di/profiles")
        sources_resp = client.get("/api/di/sources")
        assert profiles_resp.status_code == 200
        assert sources_resp.status_code == 200
        assert profiles_resp.json() == sources_resp.json()

    def test_prefixed_sources_matches(self, client: TestClient) -> None:
        """The /api/dataops/di/sources alias also returns populated data."""
        resp = client.get("/api/dataops/di/sources")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] > 0
        for source in data["sources"]:
            assert source["has_profile"] is True

    def test_prefixed_sources_matches_prefixed_profiles(self, client: TestClient) -> None:
        """Both /api/dataops/di/ endpoints agree."""
        profiles_resp = client.get("/api/dataops/di/profiles")
        sources_resp = client.get("/api/dataops/di/sources")
        assert profiles_resp.status_code == 200
        assert sources_resp.status_code == 200
        assert profiles_resp.json() == sources_resp.json()
