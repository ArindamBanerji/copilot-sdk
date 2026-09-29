from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import learning_beats, par_router, queue, trust_router
from app.services.alert_engine import PurchasingAlertEngine
from app.services.economic_model import PurchasingEconomicModel
from app.services.predictive_par import PredictivePar
from app.services.purchasing_control import PurchasingClaimRegistry
from app.services.waste_tracker import WasteTracker


@pytest.mark.parametrize("result", [ConnectionError("down"), None])
def test_par_qbo_failure_is_not_labelled_available(monkeypatch: pytest.MonkeyPatch, result: object) -> None:
    if isinstance(result, Exception):
        monkeypatch.setattr(par_router, "qbo_bills_for_spend", MagicMock(side_effect=result))
    else:
        monkeypatch.setattr(par_router, "qbo_bills_for_spend", MagicMock(return_value=result))
    app = FastAPI()
    app.include_router(par_router.create_par_router())
    payload = TestClient(app).get("/api/purchasing/par/status").json()
    assert payload["categories"] == []
    assert payload["qbo_available"] is False
    assert payload["data_source"] == "unavailable"


@pytest.mark.parametrize("result", [OSError("down"), None])
def test_queue_qbo_failure_is_flagged(monkeypatch: pytest.MonkeyPatch, result: object) -> None:
    if isinstance(result, Exception):
        monkeypatch.setattr(queue, "qbo_bills_for_spend", MagicMock(side_effect=result))
    else:
        monkeypatch.setattr(queue, "qbo_bills_for_spend", MagicMock(return_value=result))
    app = FastAPI()
    app.include_router(queue.create_queue_router(scorer_factory=lambda: MagicMock()))
    payload = TestClient(app).get("/api/purchasing/queue").json()
    assert payload["queue"] == []
    assert payload["qbo_available"] is False
    assert payload["source"] == "unavailable"


@pytest.mark.parametrize("failure", [RuntimeError("down"), None])
def test_alert_class_failure_remains_visible(failure: Exception | None) -> None:
    service = MagicMock()
    if failure is None:
        service.build_all.return_value = None
    else:
        service.build_all.side_effect = failure
    rows = PurchasingAlertEngine(scorecard_service=service).evaluate(orders=[], suppliers=[])
    degraded = [row for row in rows if row["alert_type"] == "supplier_degradation"]
    assert degraded
    assert degraded[0]["available"] is False


@pytest.mark.parametrize("result", [RuntimeError("down"), []])
def test_cost_source_failure_marks_economic_model_degraded(result: object) -> None:
    source = MagicMock()
    if isinstance(result, Exception):
        source.side_effect = result
    else:
        source.return_value = result
    model = PurchasingEconomicModel(cost_impact_source=source).compute(1)
    assert model.cost_source_available is False
    assert model.provenance == "degraded"
    assert model.degraded_sources == ["cost_impact_source"]


@pytest.mark.parametrize("result", [RuntimeError("down"), None])
def test_optimizer_failure_returns_typed_par_with_flag(result: object) -> None:
    optimizer = MagicMock()
    if isinstance(result, Exception):
        optimizer.recommend.side_effect = result
    else:
        optimizer.recommend.return_value = result
    value, available = PredictivePar(optimizer=optimizer).base_from_optimizer("salmon", "protein", [{}])
    assert value == 40.0
    assert available is False


@pytest.mark.parametrize("bad_value", [None, "bad"])
def test_malformed_waste_input_is_flagged(bad_value: object) -> None:
    orders = [
        {
            "item": "salmon",
            "category": "protein",
            "waste_pct": bad_value,
            "quantity": 1,
            "unit_cost": 4,
        }
        for _ in range(5)
    ]
    profiles = WasteTracker(orders).analyze_all()
    assert profiles
    assert profiles[0].data_available is False


@pytest.mark.parametrize("result", [ConnectionError("down"), None])
def test_learning_sibling_endpoints_propagate_data_availability(result: object) -> None:
    graph = MagicMock()
    if isinstance(result, Exception):
        graph.get_verified_decisions.side_effect = result
    else:
        graph.get_verified_decisions.return_value = result
    scorer = MagicMock(graph_store=graph)
    scorer.trajectory.return_value = {"current_iks": 0.4}
    scorer.get_conservation_status.return_value = "GREEN"
    app = FastAPI()
    app.include_router(learning_beats.create_learning_beats_router(lambda: scorer))
    client = TestClient(app)
    for path in (
        "/api/purchasing/diagnostics/signal-gate",
        "/api/purchasing/evidence/proof-ledger",
        "/api/purchasing/learning/self-pause",
        "/api/purchasing/diagnostics/ramp",
    ):
        payload = client.get(path).json()
        assert payload["data_available"] is False


@pytest.mark.parametrize("result", [ConnectionError("down"), None])
def test_purchasing_claim_refresh_tracks_staleness(result: object) -> None:
    graph = MagicMock()
    if isinstance(result, Exception):
        graph.get_verified_decisions.side_effect = result
    else:
        graph.get_verified_decisions.return_value = result
    registry = PurchasingClaimRegistry()
    registry.refresh(graph)
    assert registry.last_refresh_available is False
    assert registry.stale is True


@pytest.mark.parametrize("result", [ConnectionError("down"), None])
def test_trust_insights_distinguish_unavailable_from_empty(result: object) -> None:
    scorer = MagicMock()
    if isinstance(result, Exception):
        scorer.get_verified_count.side_effect = result
    else:
        scorer.get_verified_count.return_value = result
    scorer.get_dk_weights.return_value = []
    app = FastAPI()
    app.include_router(trust_router.create_trust_router(lambda: scorer))
    payload = TestClient(app).get("/api/purchasing/trust-weights/insights").json()
    assert payload["insights"] == []
    assert payload["trust_available"] is False
