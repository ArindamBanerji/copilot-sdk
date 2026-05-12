from __future__ import annotations

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.conservation_router import create_conservation_router


def build_client(state_provider=None) -> TestClient:
    app = FastAPI()
    app.include_router(create_conservation_router("dataops", state_provider=state_provider))
    return TestClient(app)


def test_factory_creates_apirouter():
    router = create_conservation_router("dataops")

    assert isinstance(router, APIRouter)


def test_status_returns_domain_status_and_engine_without_state():
    client = build_client()

    response = client.get("/conservation/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "dataops"
    assert payload["engine"]["gae"] == "gae.calibration"
    assert payload["engine"]["component"] == "conservation_status"
    assert payload["status"] == "RED"
    assert payload["passed"] is False
    assert payload["verified_count"] == 0


def test_status_uses_state_provider_counts():
    client = build_client(
        state_provider=lambda: {
            "verified_count": 20,
            "correct_count": 16,
            "total_decisions": 25,
            "penalty_ratio": 10.0,
        }
    )

    response = client.get("/conservation/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["verified_count"] == 20
    assert payload["correct_count"] == 16
    assert payload["total_decisions"] == 25
    assert payload["penalty_ratio"] == 10.0
    assert "signal" in payload
    assert "theta_min" in payload


def test_status_accepts_graph_store_like_object():
    class GraphStoreLike:
        penalty_ratio = 7.0

        def count_verified(self) -> int:
            return 3

        def count_correct(self) -> int:
            return 2

        def get_all_decisions(self) -> list[dict]:
            return [{"decision_id": "d-1"}, {"decision_id": "d-2"}, {"decision_id": "d-3"}, {"decision_id": "d-4"}]

    client = build_client(state_provider=GraphStoreLike())

    response = client.get("/conservation/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["verified_count"] == 3
    assert payload["correct_count"] == 2
    assert payload["total_decisions"] == 4
    assert payload["penalty_ratio"] == 7.0


def test_what_if_returns_safe_result_and_engine():
    client = build_client()

    response = client.post(
        "/conservation/what-if",
        json={"alpha": 0.5, "q": 0.9, "V": 100.0},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "dataops"
    assert payload["engine"]["gae"] == "gae.calibration"
    assert payload["engine"]["component"] == "check_conservation"
    assert payload["inputs"]["alpha"] == 0.5
    assert payload["inputs"]["q"] == 0.9
    assert payload["inputs"]["V"] == 100.0
    assert "status" in payload
    assert "passed" in payload


def test_what_if_rejects_invalid_values_without_crashing():
    client = build_client()

    response = client.post(
        "/conservation/what-if",
        json={"alpha": 0.0, "q": 0.9, "V": 100.0},
    )

    assert response.status_code == 422


def test_no_forbidden_modules_loaded():
    import sys

    build_client().get("/conservation/status")

    assert not any("domains.soc" in module for module in sys.modules)
    assert not any("domains.s2p" in module for module in sys.modules)
    assert not any("gen-ai-roi-demo" in module for module in sys.modules)
