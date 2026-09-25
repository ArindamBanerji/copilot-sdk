"""Contract tests for the deterministic no-verification trajectory fixture."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.scoring_router import create_scoring_router
from scripts.preseed_verification_gap import GAP_THRESHOLD_DAYS, build_verification_gap_fixture


class FixtureScorer:
    """Minimal scorer seam for the existing /trajectory endpoint contract."""

    graph_store: object = object()

    def trajectory(self) -> dict[str, Any]:
        fixture = build_verification_gap_fixture()
        return {key: value for key, value in fixture.items() if key not in {"decisions", "verification_gap"}}


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(create_scoring_router("dataops", scorer_factory=FixtureScorer))
    return TestClient(app)


def test_trajectory_with_gap() -> None:
    response = _client().get("/trajectory")

    assert response.status_code == 200
    payload = response.json()
    timestamps = [point["timestamp"] for point in payload["points"]]
    gap_seconds = max(right - left for left, right in zip(timestamps, timestamps[1:]))

    assert payload["decisions_total"] == 100
    assert gap_seconds > GAP_THRESHOLD_DAYS * 86_400


def test_trajectory_gap_detection() -> None:
    fixture = build_verification_gap_fixture()
    points = fixture["points"]
    gap_index = next(
        index
        for index, (left, right) in enumerate(zip(points, points[1:]))
        if right["timestamp"] - left["timestamp"] > GAP_THRESHOLD_DAYS * 86_400
    )

    assert points[gap_index]["decisions"] == 28
    assert points[gap_index + 1]["decisions"] == 72
    assert points[gap_index + 1]["win_rate"] > points[gap_index]["win_rate"]
