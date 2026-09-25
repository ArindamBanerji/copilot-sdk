from __future__ import annotations

from typing import Any, cast

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.trust_perturbation_router import (  # type: ignore[import]
    SourceTrustPerturbationService,
    create_trust_perturbation_router,
)


class _Store:
    domain = "dataops"

    def count_verified(self, domain: str) -> int:
        assert domain == self.domain
        return 40

    def count_verified_decisions(self, domain: str) -> int:
        assert domain == self.domain
        return 40

    def count_correct(self, domain: str) -> int:
        assert domain == self.domain
        return 36

    def count_categories_with_n(self, domain: str, n: int = 1) -> int:
        assert domain == self.domain
        assert n == 1
        return 5


class _Scorer:
    graph_store = _Store()

    def fingerprint(self) -> dict[str, object]:
        return {
            "factors": [
                {"name": "source_reliability", "weight": 0.87},
                {"name": "recurrence_frequency", "weight": 0.72},
                {"name": "data_freshness", "weight": 0.68},
                {"name": "downstream_urgency", "weight": 0.75},
            ]
        }


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(
        create_trust_perturbation_router(
            scorer_provider=_Scorer,
            service=SourceTrustPerturbationService(),
        ),
        prefix="/api/dataops",
    )
    return TestClient(app)


def _perturb(client: TestClient, *, kind: str = "degrade", magnitude: float = 0.15) -> dict[str, Any]:
    response = client.post(
        "/api/dataops/trust/perturb",
        json={
            "source_id": "sap_s4hana",
            "perturbation_type": kind,
            "magnitude": magnitude,
            "decisions": 5,
        },
    )
    assert response.status_code == 200
    return cast(dict[str, Any], response.json())


def test_perturb_degrade() -> None:
    result = _perturb(_client())

    assert result["trust_after"] < result["trust_before"]


def test_perturb_improve() -> None:
    result = _perturb(_client(), kind="improve")

    assert result["trust_after"] > result["trust_before"]


def test_perturb_magnitude() -> None:
    small = _perturb(_client(), magnitude=0.05)
    large = _perturb(_client(), magnitude=0.30)

    assert (small["trust_before"] - small["trust_after"]) < (large["trust_before"] - large["trust_after"])


def test_perturb_conservation_check() -> None:
    result = _perturb(_client())

    assert result["conservation_status"] in {"GREEN", "AMBER", "RED", "UNAVAILABLE"}


def test_reset_to_baseline() -> None:
    client = _client()
    perturbed = _perturb(client)
    reset = client.post("/api/dataops/trust/reset", json={"source_id": "sap_s4hana"})

    assert reset.status_code == 200
    assert reset.json()["trust_reset_to"] == perturbed["trust_before"]


def test_perturb_endpoint_200() -> None:
    response = _client().post(
        "/api/dataops/trust/perturb",
        json={"source_id": "celonis_p2p", "perturbation_type": "degrade", "magnitude": 0.10, "decisions": 3},
    )

    assert response.status_code == 200
    assert response.json()["source_id"] == "celonis_p2p"
