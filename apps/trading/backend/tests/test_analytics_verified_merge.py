"""Tests for /api/context/analytics verified-decision merge."""

from __future__ import annotations

from typing import cast

from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestAnalyticsVerifiedMerge:
    """Analytics must use verified decisions for rolling correctness."""

    def test_analytics_returns_200(self, client: TestClient) -> None:
        response = client.get("/api/context/analytics")

        assert response.status_code == 200
        counterfactual = response.json()["counterfactual"]
        if counterfactual["dollars_saved"] is None:
            assert counterfactual["dollars_saved_available"] is False
            assert counterfactual["status"] == "unavailable"

    def test_analytics_has_rolling(self, client: TestClient) -> None:
        response = client.get("/api/context/analytics")
        data = response.json()
        rolling = (
            data.get("rolling_10")
            or data.get("rolling_accuracy")
            or data.get("rolling_metrics")
        )

        assert rolling is not None or "rolling" in str(data.keys()).lower()

    def test_rolling_no_null_correct(self, client: TestClient) -> None:
        app = cast(FastAPI, client.app)
        store = app.state.graph_store
        verified_id = store.write_decision(
            "trading",
            "trend_following",
            "strong_execution",
            0.8,
            {"signal_alignment": 0.9},
            {"created_at": 100.0},
        )
        store.write_outcome(
            verified_id,
            "strong_execution",
            True,
            {"verified_at": 200.0, "dollars_saved": 25.0},
            domain="trading",
        )
        for created_at in range(300, 312):
            store.write_decision(
                "trading",
                "trend_following",
                "strong_execution",
                0.7,
                {"signal_alignment": 0.7},
                {"created_at": float(created_at)},
            )

        analytics = client.get("/api/context/analytics").json()
        rolling = analytics["rolling_10"]

        assert any(entry["decision_id"] == verified_id for entry in rolling)
        assert all(isinstance(entry["correct"], bool) for entry in rolling)
        assert analytics["counterfactual"]["dollars_saved"] >= 25.0
        assert analytics["counterfactual"]["dollars_saved_available"] is True

    def test_regime_not_silently_null(self, client: TestClient) -> None:
        app = cast(FastAPI, client.app)
        store = app.state.graph_store
        store.write_decision(
            "trading",
            "trend_following",
            "strong_execution",
            0.8,
            {"signal_alignment": 0.9},
            {"created_at": 9_999_999_999.0, "regime_tag": "volatile"},
        )

        regime = client.get("/api/context/analytics").json()["regime_analysis"]

        assert regime["regime"] == "volatile"
        assert regime["available"] is True
        assert regime["source"] == "decision_metadata"
