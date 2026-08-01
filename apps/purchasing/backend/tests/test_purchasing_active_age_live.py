from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from copilot_sdk.testing import age_available


PURCHASING_FACTORS = {
    "expected_demand": 0.72,
    "day_of_week": 0.2,
    "weather_forecast": 0.35,
    "event_flag": 0.1,
    "historical_waste": 0.18,
    "supplier_lead_time": 0.45,
    "price_memory_index": 0.50,
}


pytestmark = pytest.mark.skipif(
    not age_available(),
    reason="AGE is not reachable",
)


def test_live_active_age_score_learn_status_and_read_safety(tmp_path: Path, purchasing_live_age_graph):
    _require_live_env()
    client = TestClient(create_app(db_path=tmp_path / "unused.sqlite", demo_bundle_path=False))
    store = client.app.state.purchasing_selected_graph_store

    status = client.get("/api/purchasing/graph/status").json()
    assert status["active_backend"] == "age"
    assert status["age_active"] is True
    assert status["graph_kind"] == "test"
    assert status["active_domain"] == "purchasing"
    assert status["active_test_mode"] is True
    assert status["active_graph_name"] != "soc_graph"
    assert "postgres" not in str(status).lower()

    before = int(store.count_decisions("purchasing"))
    score = client.post(
        "/api/score",
        json={"category": "protein", "factors": PURCHASING_FACTORS},
    )
    assert score.status_code == 200
    score_payload = score.json()
    decision_id = score_payload["decision_id"]
    decision = store.get_decision(decision_id, domain="purchasing")
    assert decision is not None
    assert decision["decision_id"] == decision_id
    assert str(decision.get("status") or "").lower() == "pending"

    read = client.get("/api/purchasing/evidence/summary")
    assert read.status_code == 200
    assert int(store.count_decisions("purchasing")) == before + 1

    learn = client.post(
        "/api/learn",
        json={"decision_id": decision_id, "actual_action": score_payload["action"]},
    )
    assert learn.status_code == 200
    learned = store.get_decision(decision_id, domain="purchasing")
    assert learned is not None
    assert str(learned.get("status") or learned.get("outcome") or "").lower() == "confirmed"
    assert _has_outcome(learned)

    duplicate = client.post(
        "/api/learn",
        json={"decision_id": decision_id, "actual_action": score_payload["action"]},
    )
    assert duplicate.status_code == 400


def _require_live_env() -> None:
    required = {
        "PURCHASING_ACTIVE_GRAPH_BACKEND": "age",
        "PURCHASING_ACTIVE_AGE_TEST_MODE": "1",
        "PURCHASING_ACTIVE_AGE_DOMAIN": "purchasing",
    }
    for key, expected in required.items():
        assert os.environ.get(key) == expected
    assert os.environ.get("PURCHASING_ACTIVE_AGE_DSN")
    assert os.environ.get("PURCHASING_ACTIVE_AGE_GRAPH", "").startswith("protocol_v2_test_")


def _has_outcome(decision: dict[str, Any]) -> bool:
    if str(decision.get("status") or decision.get("outcome") or "").lower() in {
        "confirmed",
        "overridden",
    }:
        return True
    if decision.get("outcome") is not None or decision.get("is_correct") is not None:
        return True
    outcomes = decision.get("outcomes")
    return isinstance(outcomes, list) and len(outcomes) == 1
