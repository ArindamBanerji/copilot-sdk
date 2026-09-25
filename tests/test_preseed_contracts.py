"""Demo contract checks using real scorer, store and frozen-twin services."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.modeled_projection import modeled_projection
from copilot_sdk.backend.conservation_router import create_conservation_router
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring import CompoundingScorer


INPUTS = {"setup_cost": 1000, "weekly_decisions": 100, "benefit_per_decision": 2.5,
          "weekly_operating_cost": 20, "required_verified_decisions": 200,
          "provenance": "sample assumptions"}


def test_projection_is_explicit_modeled_break_even() -> None:
    result = modeled_projection(INPUTS, 100)
    assert result["projected_divergence_week"] == 5
    assert result["readiness_score"] == 0.5
    assert "MODELED" in result["evidence_label"]
    assert result["projection_inputs"] == INPUTS


def test_projection_missing_or_unprofitable_does_not_claim_roi() -> None:
    assert modeled_projection(None, 100)["projected_divergence_week"] is None
    assert modeled_projection({**INPUTS, "benefit_per_decision": 0}, 100)["projected_divergence_week"] is None


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1])
def test_projection_rejects_bad_assumptions(value: float) -> None:
    with pytest.raises(ValueError):
        modeled_projection({**INPUTS, "weekly_decisions": value}, 100)


def test_projection_does_not_override_conservation() -> None:
    store = InMemoryGraphStore(domain="purchasing")
    scorer = CompoundingScorer.from_preset("purchasing", graph_store=store, profile="test", enable_rl=False)
    try:
        app = FastAPI()
        app.include_router(create_conservation_router("purchasing", scorer,
            projection_provider=lambda count: {**modeled_projection(INPUTS, count), "passed": False, "status": "RED"}), prefix="/api")
        with TestClient(app) as client:
            body = client.get("/api/conservation/status").json()
        assert body["projected_divergence_week"] == 5
        assert body["status"] != "RED"
    finally:
        store.close()

