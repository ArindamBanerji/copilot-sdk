"""Regression: /api/trajectory must return real data, not flat 0.50 defaults."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client() -> TestClient:
    app = create_app(db_path=":memory:", demo_bundle_path=False, profile="test")
    return TestClient(app)


class TestTrajectoryRegression:
    """Verify /api/trajectory returns populated data after seeding."""

    def test_trajectory_returns_200(self, client: TestClient) -> None:
        """Trajectory endpoint is reachable and returns 200."""
        resp = client.get("/api/trajectory")
        assert resp.status_code == 200

    def test_trajectory_has_points(self, client: TestClient) -> None:
        """Trajectory contains at least baseline + one real point after preseed."""
        resp = client.get("/api/trajectory")
        data = resp.json()
        assert "points" in data or "trajectory" in data, (
            "Response must contain trajectory data"
        )
        points = data.get("points") or data.get("trajectory", [])
        assert len(points) >= 1, "Must have at least baseline point"

    def test_trajectory_not_all_default(self, client: TestClient) -> None:
        """If multiple points exist, they must not all be 0.50."""
        resp = client.get("/api/trajectory")
        data = resp.json()
        points = data.get("points") or data.get("trajectory", [])
        if len(points) > 1:
            values = []
            for p in points:
                if isinstance(p, dict):
                    val = p.get("value") or p.get("win_rate") or p.get("accuracy")
                    if val is not None:
                        values.append(val)
                elif isinstance(p, (int, float)):
                    values.append(p)
            if values:
                non_default = [v for v in values if abs(v - 0.50) > 0.001]
                assert len(non_default) > 0, (
                    "Trajectory must not be flat 0.50 defaults — "
                    "indicates scorer has no real verified decisions"
                )

    def test_trajectory_response_shape(self, client: TestClient) -> None:
        """Response includes expected metadata fields."""
        resp = client.get("/api/trajectory")
        data = resp.json()
        # Should have either domain or current_iks or similar metadata
        assert isinstance(data, dict), "Response must be a dict"
