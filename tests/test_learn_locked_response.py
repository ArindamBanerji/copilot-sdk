"""Exercise HTTP contracts with the real scorer, store, and production gate."""
from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.scoring_router import create_scoring_router
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring import CompoundingScorer
from copilot_sdk.scoring.composite_gate import CompositeGate
from copilot_sdk.scoring.gate_enforced_scorer import GateEnforcedScorer
from copilot_sdk.scoring.presets.trading import TradingPreset


@pytest.fixture
def gate_client() -> Iterator[tuple[TestClient, InMemoryGraphStore, GateEnforcedScorer]]:
    store = InMemoryGraphStore(domain="trading")
    scorer = CompoundingScorer.from_preset(
        "trading", graph_store=store, profile="test", enable_rl=False,
    )
    wrapper = GateEnforcedScorer(scorer, CompositeGate())
    app = FastAPI()
    app.include_router(create_scoring_router("trading", scorer_factory=lambda: wrapper), prefix="/api")
    try:
        with TestClient(app) as client:
            yield client, store, wrapper
    finally:
        store.close()


def test_gate_blocks_returns_structured_423(
    gate_client: tuple[TestClient, InMemoryGraphStore, GateEnforcedScorer],
) -> None:
    client, store, wrapper = gate_client
    preset = TradingPreset()
    outcomes = ([True] * 17 + [False] * 3) * 20 + [True, False] * 10
    for index, correct in enumerate(outcomes):
        decision_id = store.write_decision(
            domain="trading", category=preset.shape.category_names[index % 5],
            action=preset.shape.action_names[0], confidence=0.85,
            factors={name: 0.8 for name in preset.shape.factor_names},
        )
        store.write_outcome(
            decision_id, preset.shape.action_names[0 if correct else 1],
            correct, domain="trading",
        )
    scored = client.post("/api/score", json={"category": "trend_following", "factors": {}})
    assert scored.status_code == 200
    decision = scored.json()
    count = store.count_verified("trading")
    response = client.post("/api/learn", json={
        "decision_id": decision["decision_id"], "actual_action": decision["action"],
    })
    assert response.status_code == 423
    assert response.json() == {
        "blocked": True, "gate_status": "AMBER", "reason": "G-RATE active",
    }
    assert store.count_verified("trading") == count
    assert len(wrapper._outcome_buffer) == 1
    assert "423" in client.get("/openapi.json").json()["paths"]["/api/learn"]["post"]["responses"]


def test_gate_passes_returns_normal_200(
    gate_client: tuple[TestClient, InMemoryGraphStore, GateEnforcedScorer],
) -> None:
    client, store, _wrapper = gate_client
    scored = client.post("/api/score", json={"category": "trend_following", "factors": {}})
    assert scored.status_code == 200
    decision = scored.json()
    response = client.post("/api/learn", json={
        "decision_id": decision["decision_id"], "actual_action": decision["action"],
    })
    assert response.status_code == 200
    body = response.json()
    assert body["decision_id"] == decision["decision_id"]
    assert {"iks_before", "iks_after", "centroid_delta", "decisions_total", "outcome"} <= body.keys()
    assert "blocked" not in body
    assert store.count_verified("trading") == 1
