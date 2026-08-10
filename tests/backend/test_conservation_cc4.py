"""CC-4 explainability contract tests for the shared conservation router."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from copilot_sdk.backend.conservation_router import create_conservation_router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(
        create_conservation_router(
            "dataops",
            state_provider=lambda: {
                "verified_count": 100,
                "correct_count": 80,
                "total_decisions": 100,
                "penalty_ratio": 1.0,
                "baseline_q": 0.9,
                "categories_with_data": 5,
                "total_categories": 6,
            },
        )
    )
    return TestClient(app)


def test_conservation_payload_complete() -> None:
    payload = _client().get("/conservation/status").json()
    required = {
        "status",
        "alpha",
        "q",
        "V",
        "theta_min",
        "signal",
        "headroom",
        "baseline",
        "baseline_q",
        "relative_trigger",
        "relative_trigger_ratio",
        "reason",
    }
    assert required.issubset(payload)
    assert payload["V"] == payload["verified_count"] == 100


def test_conservation_reason_is_plain_language() -> None:
    reason = _client().get("/conservation/status").json()["reason"]
    assert isinstance(reason, str)
    assert len(reason.split()) >= 8
    assert "Signal" in reason or "No verified decisions" in reason


def test_conservation_headroom_matches() -> None:
    payload = _client().get("/conservation/status").json()
    assert payload["headroom"] == pytest.approx(
        payload["signal"] - payload["theta_min"]
    )


def test_conservation_relative_trigger() -> None:
    payload = _client().get("/conservation/status").json()
    assert payload["relative_trigger_ratio"] == pytest.approx(0.7)
    assert payload["relative_trigger"] == pytest.approx(
        0.7 * payload["baseline_q"]
    )
