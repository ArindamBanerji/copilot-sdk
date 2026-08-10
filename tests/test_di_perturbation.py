from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.dataops.backend.app.routers.perturbation_router import create_perturbation_router
from copilot_sdk.di.perturbation import PerturbationService


class FakeScorer:
    def __init__(self) -> None:
        self.decisions = [{"id": "existing-1"}]

    def fingerprint(self) -> dict[str, object]:
        return {
            "factors": [
                {"name": "source_reliability", "weight": 0.94},
                {"name": "data_freshness", "weight": 0.80},
                {"name": "downstream_urgency", "weight": 0.60},
            ]
        }


def test_perturb_degrades_target_source() -> None:
    scorer = FakeScorer()
    result = PerturbationService().perturb(
        scorer, source_name="snowflake", perturbation="degrade", magnitude=0.5, decisions=20
    )

    assert result["before"]["source_reliability"] == 0.94
    assert result["after"]["source_reliability"] == 0.47
    assert result["delta"]["source_reliability"] < 0


def test_perturb_only_affects_target_factor() -> None:
    scorer = FakeScorer()
    result = PerturbationService().perturb(
        scorer, source_name="snowflake", perturbation="degrade", magnitude=0.5, decisions=20
    )

    assert result["after"]["data_freshness"] == result["before"]["data_freshness"]
    assert result["after"]["downstream_urgency"] == result["before"]["downstream_urgency"]


def test_revert_restores_original_weights() -> None:
    service = PerturbationService()
    scorer = FakeScorer()
    original = scorer.fingerprint()
    service.perturb(scorer, source_name="snowflake", perturbation="degrade", magnitude=0.5, decisions=20)

    restored = service.revert()

    assert restored["restored"] is True
    assert restored["trust"]["factors"] == {
        "source_reliability": 0.94,
        "data_freshness": 0.80,
        "downstream_urgency": 0.60,
    }
    assert scorer.fingerprint() == original


def test_revert_removes_injected_decisions() -> None:
    scorer = FakeScorer()
    service = PerturbationService()
    service.perturb(scorer, source_name="snowflake", perturbation="degrade", magnitude=0.5, decisions=20)
    service.revert()

    assert scorer.decisions == [{"id": "existing-1"}]
    assert service.status()["active"] is False


def test_only_one_perturbation_at_a_time() -> None:
    service = PerturbationService()
    scorer = FakeScorer()
    service.perturb(scorer, source_name="snowflake", perturbation="degrade", magnitude=0.5, decisions=20)

    with pytest.raises(ValueError, match="already active"):
        service.perturb(scorer, source_name="airflow", perturbation="degrade", magnitude=0.5, decisions=20)


def test_perturb_requires_demo_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATAOPS_DEMO_MODE", raising=False)
    app = FastAPI()
    app.include_router(
        create_perturbation_router(scorer_provider=FakeScorer, service=PerturbationService()),
        prefix="/api/di",
    )

    response = TestClient(app).post(
        "/api/di/perturb",
        json={"source_name": "snowflake", "perturbation": "degrade", "magnitude": 0.5, "decisions": 20},
    )

    assert response.status_code == 403
