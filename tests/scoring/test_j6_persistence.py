from __future__ import annotations

from typing import Any

from gae.profile_scorer import ProfileScorer
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.scoring_router import (
    _persist_conservation_state_l5,
    create_scoring_router,
)
from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer


def _scorer(mock_preset, store: InMemoryGraphStore) -> CompoundingScorer:
    engine = ProfileScorer(
        mu=mock_preset.bootstrap_centroids.copy(),
        actions=list(mock_preset.shape.action_names),
        categories=list(mock_preset.shape.category_names),
    )
    return CompoundingScorer(mock_preset, engine, graph_store=store)


class FailingV2Store(InMemoryGraphStore):
    def write_conservation_status(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("conservation persistence failed")

    def write_fingerprint(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("fingerprint persistence failed")

    def write_centroid_checkpoint(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("checkpoint persistence failed")

    def append_evidence_receipt(self, *args: Any, **kwargs: Any) -> tuple[int, str]:
        raise RuntimeError("evidence persistence failed")

    def save_centroids(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("legacy checkpoint persistence failed")


class L5InMemoryStore(InMemoryGraphStore):
    def count_categories_with_n(self, domain: str, n: int = 1) -> int:
        counts: dict[str, int] = {}
        for decision in self.get_verified_decisions(domain):
            category = str(decision.get("category", ""))
            counts[category] = counts.get(category, 0) + 1
        return sum(count >= n for count in counts.values())


def test_scorer_persists_v2_evidence_fingerprint_and_checkpoint(mock_preset):
    store = L5InMemoryStore(domain="mock")
    scorer = _scorer(mock_preset, store)

    try:
        result = scorer.score(
            {"amount": 0.25, "risk": 0.35, "history": 0.45},
            mock_preset.shape.category_names[0],
        )
        scorer.learn(result.decision_id, result.action)

        assert len(store._evidence_receipts) == 1
        receipt = next(iter(store._evidence_receipts.values()))
        assert receipt["domain"] == "mock"
        assert receipt["decision_id"] == result.decision_id

        assert len(store._protocol_centroid_checkpoints) == 1
        checkpoint = next(iter(store._protocol_centroid_checkpoints.values()))
        assert checkpoint["domain"] == "mock"
        assert checkpoint["metadata"]["decision_id"] == result.decision_id

        fingerprint = scorer.fingerprint()
        assert fingerprint.decisions_analyzed == 1
        assert len(store._fingerprints) == 2
        assert all(snapshot["domain"] == "mock" for snapshot in store._fingerprints.values())
        assert any(snapshot["window"] == 1 for snapshot in store._fingerprints.values())
        scorer.fingerprint()
        assert len(store._fingerprints) == 2
    finally:
        store.close()


def test_persistence_failures_do_not_block_learning_or_fingerprint(mock_preset):
    store = FailingV2Store(domain="mock")
    scorer = _scorer(mock_preset, store)

    try:
        result = scorer.score(
            {"amount": 0.25, "risk": 0.35, "history": 0.45},
            mock_preset.shape.category_names[0],
        )
        learned = scorer.learn(result.decision_id, result.action)
        fingerprint = scorer.fingerprint()
        _persist_conservation_state_l5(domain="mock", scorer=scorer)

        assert learned.decision_id == result.decision_id
        assert fingerprint.decisions_analyzed == 1
        assert store.count_verified("mock") == 1
    finally:
        store.close()


def test_learn_route_persists_conservation_snapshot(mock_preset):
    store = L5InMemoryStore(domain="mock")
    scorer = _scorer(mock_preset, store)
    app = FastAPI()
    app.include_router(
        create_scoring_router(
            domain="mock",
            scorer_factory=lambda: scorer,
        )
    )

    try:
        with TestClient(app) as client:
            score_payload = client.post(
                "/score",
                json={
                    "category": mock_preset.shape.category_names[0],
                    "factors": {"amount": 0.25, "risk": 0.35, "history": 0.45},
                },
            ).json()
            decision_id = score_payload["decision_id"]
            response = client.post(
                "/learn",
                json={"decision_id": decision_id, "actual_action": score_payload["action"]},
            )

        assert response.status_code == 200
        assert len(store._conservation_snapshots) == 1
        snapshot = next(iter(store._conservation_snapshots.values()))
        assert snapshot["domain"] == "mock"
        assert snapshot["verified_count"] == 1
    finally:
        store.close()
