"""Option B point-in-time checkpoint replay tests."""

from __future__ import annotations

import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.self_computation_router import mount_self_computation_router
from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring import CompoundingScorer


DOMAIN = "trading"


def _setup() -> tuple[CompoundingScorer, InMemoryGraphStore, TestClient, str, dict[str, float]]:
    store = InMemoryGraphStore(domain=DOMAIN)
    scorer = CompoundingScorer.from_preset(DOMAIN, graph_store=store, profile="test")
    preset = scorer._preset.shape
    category = preset.category_names[0]
    factors = {name: 0.5 for name in preset.factor_names}
    checkpoint_id = "replay-checkpoint"
    scorer._save_centroids_checkpoint(
        decision_id="decision-replay",
        category=category,
        action=preset.action_names[0],
        iks=0.8,
        checkpoint_id=checkpoint_id,
    )
    app = FastAPI()
    mount_self_computation_router(
        app,
        store,
        scorer_provider=lambda: scorer,
        domain=DOMAIN,
    )
    return scorer, store, TestClient(app), checkpoint_id, factors


def test_checkpoint_includes_dk_weights_and_temperature() -> None:
    _, store, _, checkpoint_id, _ = _setup()
    checkpoint = next(
        item for item in store.get_centroid_checkpoints(DOMAIN, limit=None, include_v2=True)
        if item.get("checkpoint_id") == checkpoint_id
    )
    metadata = checkpoint["metadata"]
    assert isinstance(metadata["dk_weights"], list)
    assert all(isinstance(value, float) for row in metadata["dk_weights"] for value in row)
    assert isinstance(metadata["temperature"], float)


def test_replay_endpoint_returns_full_state() -> None:
    _, store, client, checkpoint_id, _ = _setup()
    response = client.get(f"/api/self/centroid-history/{checkpoint_id}/replay")
    assert response.status_code == 200
    body = response.json()
    assert body["checkpoint_id"] == checkpoint_id
    assert body["centroids"] is not None
    assert body["dk_weights"] is not None
    assert isinstance(body["temperature"], float)
    assert "quality" in body
    assert body["iks"] is not None
    store.close()


def test_replay_score_uses_historical_centroids() -> None:
    scorer, store, client, checkpoint_id, factors = _setup()
    category = scorer._preset.shape.category_names[0]
    historical = scorer.score_read_only(factors, category)
    scorer._scorer.centroids = np.clip(scorer._scorer.centroids + 0.35, 0.0, 1.0)
    current = scorer.score_read_only(factors, category)
    replay = client.post(
        "/api/self/replay-score",
        json={"checkpoint_id": checkpoint_id, "category": category, "factors": factors},
    )
    assert replay.status_code == 200
    assert replay.json()["probabilities"] == historical.probabilities
    assert replay.json()["probabilities"] != current.probabilities
    store.close()


def test_replay_score_404_on_missing_checkpoint() -> None:
    _, store, client, _, factors = _setup()
    response = client.post(
        "/api/self/replay-score",
        json={"checkpoint_id": "missing", "category": "trend_following", "factors": factors},
    )
    assert response.status_code == 404
    store.close()


def test_legacy_checkpoint_replay_returns_null_dk() -> None:
    store = InMemoryGraphStore(domain=DOMAIN)
    store.write_centroid_checkpoint(
        checkpoint_id="legacy-checkpoint",
        domain=DOMAIN,
        category="trend_following",
        action="strong_execution",
        centroids=np.zeros((5, 4, 7)),
        decisions_count=1,
        verified_count=1,
        iks=0.5,
        shape=[5, 4, 7],
        factor_names_hash="legacy",
    )
    app = FastAPI()
    mount_self_computation_router(app, store, domain=DOMAIN)
    body = TestClient(app).get(
        "/api/self/centroid-history/legacy-checkpoint/replay"
    ).json()
    assert body["dk_weights"] is None
    assert body["temperature"] is None
    assert body["quality"] is None
    store.close()
