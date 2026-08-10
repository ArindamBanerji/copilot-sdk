from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.self_computation_router import mount_self_computation_router
from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer


def test_trust_traps_endpoint() -> None:
    app = FastAPI()
    mount_self_computation_router(app, InMemoryGraphStore(domain="trust"), domain="trust")
    response = TestClient(app).get("/api/self/trust-traps")
    assert response.status_code == 200
    assert isinstance(response.json()["traps"], list)


def test_rollback_endpoint_404_for_unknown_checkpoint() -> None:
    app = FastAPI()
    store = InMemoryGraphStore(domain="trading")
    scorer = CompoundingScorer.from_preset("trading", graph_store=store, profile="test", enable_rl=False)
    mount_self_computation_router(app, store, domain="trading", scorer_provider=scorer)
    response = TestClient(app).post("/api/self/rollback?checkpoint_id=fake-id")
    assert response.status_code == 404


def test_rollback_endpoint_restores_valid_checkpoint() -> None:
    store = InMemoryGraphStore(domain="trading")
    scorer = CompoundingScorer.from_preset("trading", graph_store=store, profile="test", enable_rl=False)
    factors = {name: 0.7 for name in scorer._preset.shape.factor_names}
    result = scorer.score(factors, "trend_following")
    scorer.learn(result.decision_id, result.action)
    checkpoint = next(
        item for item in store.get_centroid_checkpoints("trading", limit=None, include_v2=True)
        if item.get("checkpoint_id")
    )

    app = FastAPI()
    mount_self_computation_router(app, store, domain="trading", scorer_provider=scorer)
    response = TestClient(app).post(f"/api/self/rollback?checkpoint_id={checkpoint['checkpoint_id']}")
    assert response.status_code == 200
    assert response.json()["rolled_back"] is True
