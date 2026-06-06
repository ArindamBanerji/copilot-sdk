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


def test_status_uses_state_provider_verified_count_as_conservation_v():
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
    assert payload["total_decisions"] == 20
    assert payload["penalty_ratio"] == 10.0
    assert "signal" in payload
    assert "theta_min" in payload


def test_status_dict_state_all_pending_count_does_not_inflate_conservation_v():
    client = build_client(
        state_provider=lambda: {
            "verified_count": 0,
            "correct_count": 0,
            "total_decisions": 10,
            "penalty_ratio": 10.0,
        }
    )

    response = client.get("/conservation/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["verified_count"] == 0
    assert payload["correct_count"] == 0
    assert payload["total_decisions"] == 0


def test_status_accepts_graph_store_like_object():
    class GraphStoreLike:
        domain = "dataops"
        penalty_ratio = 7.0

        def count_verified(self, domain: str = "dataops") -> int:
            return 3

        def count_correct(self, domain: str = "dataops") -> int:
            return 2

        def count_verified_decisions(self, domain: str = "dataops") -> int:
            return 3

        def get_all_decisions(self, domain: str = "dataops") -> list[dict]:
            return [{"decision_id": "d-1"}, {"decision_id": "d-2"}, {"decision_id": "d-3"}, {"decision_id": "d-4"}]

    client = build_client(state_provider=GraphStoreLike())

    response = client.get("/conservation/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["verified_count"] == 3
    assert payload["correct_count"] == 2
    assert payload["total_decisions"] == 3
    assert payload["penalty_ratio"] == 7.0


def test_status_uses_verified_decision_count_for_conservation_v():
    class GraphStoreLike:
        domain = "dataops"
        penalty_ratio = 7.0

        def count_verified(self, domain: str = "dataops") -> int:
            assert domain == "dataops"
            return 3

        def count_correct(self, domain: str = "dataops") -> int:
            assert domain == "dataops"
            return 2

        def count_verified_decisions(self, domain: str = "dataops") -> int:
            assert domain == "dataops"
            return 3

        def count_decisions(self, domain: str = "dataops") -> int:
            assert domain == "dataops"
            return 5

        def get_all_decisions(self, domain: str = "dataops") -> list[dict]:
            raise AssertionError("get_all_decisions should not be used for conservation V")

    client = build_client(state_provider=GraphStoreLike())

    response = client.get("/conservation/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["verified_count"] == 3
    assert payload["correct_count"] == 2
    assert payload["total_decisions"] == 3
    assert payload["penalty_ratio"] == 7.0


def test_status_fallback_uses_verified_count_not_all_rows_for_conservation_v():
    class GraphStoreLike:
        domain = "dataops"

        def count_verified(self, domain: str = "dataops") -> int:
            assert domain == "dataops"
            return 2

        def count_correct(self, domain: str = "dataops") -> int:
            assert domain == "dataops"
            return 1

        def count_decisions(self, domain: str = "dataops") -> int:
            raise AssertionError("all-row count_decisions must not define conservation V")

        def get_all_decisions(self, domain: str = "dataops") -> list[dict]:
            raise AssertionError("all-row get_all_decisions must not define conservation V")

    client = build_client(state_provider=GraphStoreLike())

    response = client.get("/conservation/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["verified_count"] == 2
    assert payload["correct_count"] == 1
    assert payload["total_decisions"] == 2


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
