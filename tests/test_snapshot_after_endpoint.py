from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.self_computation_router import mount_self_computation_router
from copilot_sdk.graph import InMemoryGraphStore


def _seed():
    store = InMemoryGraphStore(domain="test")
    decision_id = store.write_decision("test", "quality", "investigate", 0.9, {"x": 1.0}, {"decision_id": "decision-1"})
    store.write_centroid_checkpoint(
        checkpoint_id="checkpoint-1", domain="test", category="quality", action="investigate",
        centroids=[[[0.1]]], decisions_count=1, verified_count=1, iks=1.0, shape=[1, 1, 1],
        factor_names_hash="hash", decision_id=decision_id,
    )
    app = FastAPI()
    mount_self_computation_router(app, store)
    return store, decision_id, TestClient(app)


def test_lineage_endpoint_200():
    store, _, client = _seed()
    try:
        response = client.get("/api/self/centroid-history/checkpoint-1/lineage")
        assert response.status_code == 200
        assert response.json()["triggered_by"]["decision_id"] == "decision-1"
    finally:
        store.close()


def test_lineage_endpoint_404():
    store, _, client = _seed()
    try:
        assert client.get("/api/self/centroid-history/nonexistent/lineage").status_code == 404
    finally:
        store.close()


def test_decision_checkpoints_endpoint_200():
    store, decision_id, client = _seed()
    try:
        response = client.get(f"/api/self/decisions/{decision_id}/checkpoints")
        assert response.status_code == 200
        assert len(response.json()["checkpoints"]) == 1
    finally:
        store.close()
