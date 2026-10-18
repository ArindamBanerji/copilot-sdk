from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from copilot_sdk.backend.conservation_router import build_conservation_status


def test_rsi_summary_returns_timeline(client: TestClient) -> None:
    response = client.get("/api/context/rsi-summary")

    assert response.status_code == 200
    timeline = response.json()["timeline"]
    assert set(timeline) == {"weeks", "alert_volume", "monthly_cost", "auto_approve_pct"}
    assert all(len(values) == 7 for values in timeline.values())
    assert timeline["weeks"] == [1, 4, 8, 12, 16, 20, 24]


def test_rsi_summary_current_from_store(client: TestClient) -> None:
    governance = client.app.state.dataops_governance
    store = client.app.state.graph_store
    trajectory = governance.scorer.trajectory()
    expected_iks = float(getattr(trajectory, "current_iks", 0.0))
    expected_conservation = build_conservation_status("dataops", governance.scorer)

    current = client.get("/api/context/rsi-summary").json()["current"]

    assert current["iks"] == expected_iks
    assert current["conservation_status"] == expected_conservation
    assert current["total_decisions"] == store.count_decisions("dataops")
    assert current["verified_decisions"] == store.count_verified_decisions("dataops")


def test_rsi_summary_headline_computed(client: TestClient) -> None:
    payload = client.get("/api/context/rsi-summary").json()
    timeline = payload["timeline"]

    assert payload["headline"] == {
        "alert_reduction_pct": int(
            (timeline["alert_volume"][0] - timeline["alert_volume"][-1])
            * 100
            / timeline["alert_volume"][0]
        ),
        "cost_reduction_pct": int(
            (timeline["monthly_cost"][0] - timeline["monthly_cost"][-1])
            * 100
            / timeline["monthly_cost"][0]
        ),
        "auto_approve_current": timeline["auto_approve_pct"][-1],
        "value_annual": (timeline["monthly_cost"][0] - timeline["monthly_cost"][-1]) * 12,
    }


def test_rsi_summary_patterns(client: TestClient) -> None:
    current = client.get("/api/context/rsi-summary").json()["current"]

    for key in ("patterns_promoted", "patterns_transferred"):
        assert isinstance(current[key], int)
        assert not isinstance(current[key], bool)
        assert current[key] >= 0


def test_rsi_summary_cached(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    scorer = client.app.state.dataops_governance.scorer
    original_trajectory = scorer.trajectory
    calls = 0

    def tracked_trajectory() -> Any:
        nonlocal calls
        calls += 1
        return original_trajectory()

    monkeypatch.setattr(scorer, "trajectory", tracked_trajectory)

    first = client.get("/api/context/rsi-summary")
    second = client.get("/api/context/rsi-summary")

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert calls == 1
