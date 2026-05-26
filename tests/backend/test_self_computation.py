from __future__ import annotations

import math
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.self_computation_router import mount_self_computation_router
from copilot_sdk.graph import InMemoryGraphStore


def _client(store: InMemoryGraphStore | None = None) -> TestClient:
    app = FastAPI()
    mount_self_computation_router(app, store or InMemoryGraphStore(domain="banking"))
    return TestClient(app)


def _seed_store() -> tuple[InMemoryGraphStore, dict[str, str]]:
    store = InMemoryGraphStore(domain="banking")
    d1 = store.write_decision(
        "banking",
        category="fraud_review",
        action="investigate",
        confidence=0.9,
        factors={"severity": 0.8},
        metadata={"decision_id": "d1", "entity_id": "entity-1", "created_at": 1.0},
    )
    d2 = store.write_decision(
        "banking",
        category="fraud_review",
        action="suppress",
        confidence=0.6,
        factors={"severity": 0.4},
        metadata={"decision_id": "d2", "entity_id": "entity-2", "created_at": 2.0},
    )
    d3 = store.write_decision(
        "banking",
        category="kyc",
        action="escalate",
        confidence=0.3,
        factors={"severity": 0.2},
        metadata={"decision_id": "d3", "entity_id": "entity-3", "created_at": 3.0},
    )
    store.write_outcome(d1, actual_action="investigate", is_correct=True, metadata={"reward": 0.8})
    store.write_outcome(d2, actual_action="escalate", is_correct=False, metadata={"reward": -0.2})
    for index in range(25):
        store.save_centroids(
            "banking",
            "fraud_review" if index % 2 == 0 else "kyc",
            {"centroid": [index / 100]},
            metadata={"iks": float(index)},
            decision_id=d1 if index == 0 else d2,
            checkpoint_time=f"2026-01-{index + 1:02d}T00:00:00Z",
        )
    return store, {"d1": d1, "d2": d2, "d3": d3}


def _assert_json_safe(value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            _assert_json_safe(item)
    elif isinstance(value, list):
        for item in value:
            _assert_json_safe(item)
    elif isinstance(value, float):
        assert math.isfinite(value)
    else:
        assert value is None or isinstance(value, (str, int, bool))


def test_decision_flow_empty_store_returns_defaults() -> None:
    response = _client().get("/api/self/decision-flow")

    assert response.status_code == 200
    payload = response.json()
    assert payload["domain"] == "banking"
    assert payload["total_decisions"] == 0
    assert payload["verified_decisions"] == 0
    assert payload["accuracy"] == 0.0
    assert payload["by_category"] == {}
    assert payload["recent_decisions"] == []
    assert payload["centroid_evolution"] == []
    assert payload["decision_chain"] == []
    assert payload["flow_statistics"]["confirmation_rate"] == 0.0
    _assert_json_safe(payload)


def test_decision_flow_populated_counts_and_accuracy_use_verified_denominator() -> None:
    store, _ = _seed_store()
    payload = _client(store).get("/api/self/decision-flow").json()

    assert payload["domain"] == "banking"
    assert payload["total_decisions"] == 3
    assert payload["verified_decisions"] == 2
    assert payload["accuracy"] == 0.5
    assert payload["by_category"]["fraud_review"] == {
        "total_decisions": 2,
        "verified_decisions": 2,
        "correct_decisions": 1,
        "accuracy": 0.5,
    }
    assert payload["by_category"]["kyc"] == {
        "total_decisions": 1,
        "verified_decisions": 0,
        "correct_decisions": 0,
        "accuracy": 0.0,
    }
    _assert_json_safe(payload)


def test_decision_flow_recent_decisions_limit_and_newest_first() -> None:
    store, _ = _seed_store()
    payload = _client(store).get("/api/self/decision-flow?limit=2").json()

    assert [item["decision_id"] for item in payload["recent_decisions"]] == ["d3", "d2"]
    assert len(payload["decision_chain"]) == 2
    assert payload["decision_chain"][0]["decision_id"] == "d3"
    assert payload["decision_chain"][0]["next"] == "d2"


def test_decision_flow_centroid_evolution_caps_at_twenty() -> None:
    store, _ = _seed_store()
    payload = _client(store).get("/api/self/decision-flow").json()

    assert len(payload["centroid_evolution"]) == 20
    assert payload["centroid_evolution"][0]["iks"] == 5.0
    assert payload["centroid_evolution"][-1]["iks"] == 24.0


def test_decision_flow_flow_statistics() -> None:
    store, _ = _seed_store()
    payload = _client(store).get("/api/self/decision-flow").json()
    stats = payload["flow_statistics"]

    assert stats["avg_confidence"] == 0.6
    assert stats["confirmation_rate"] == round(2 / 3, 6)
    assert stats["override_rate"] == 0.5
    assert stats["mean_reward"] == 0.3


def test_decision_flow_existing_self_endpoints_still_work() -> None:
    store, _ = _seed_store()
    client = _client(store)

    assert client.get("/api/self/centroid-history").status_code == 200
    assert client.get("/api/self/accuracy-by-category").status_code == 200
    assert client.get("/api/self/decisions").status_code == 200
    assert client.get("/api/self/audit-trail").status_code == 200
