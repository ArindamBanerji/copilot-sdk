from __future__ import annotations

from typing import cast

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_control_gets_do_not_replay_proof_writes(client: TestClient) -> None:
    app = cast(FastAPI, client.app)
    store = app.state.purchasing_selected_graph_store
    scored = client.post("/api/score", json={"category": "protein", "factors": {}})
    assert scored.status_code == 200
    decision_id = scored.json()["decision_id"]
    before = store.get_evolution_events("purchasing", limit=10000)
    for _ in range(2):
        readiness = client.get("/api/purchasing/day-0-readiness")
        proof = client.get("/api/purchasing/proof-ledger")
        handoff = client.get("/api/purchasing/handoff-pack")
        discovery = client.get("/api/purchasing/discovery-gate")
        assert all(response.status_code == 200 for response in (readiness, proof, handoff, discovery))
        assert readiness.json()["coverage"] == proof.json()["proof_curve"]
        assert any(entry["payload"]["decision_id"] == decision_id for entry in proof.json()["entries"])
    assert store.get_evolution_events("purchasing", limit=10000) == before
