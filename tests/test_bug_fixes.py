from __future__ import annotations

import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.self_computation_router import mount_self_computation_router
from copilot_sdk.evolution import DefaultPromotionGate
from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer, ScoreResult


def _shadow(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "sufficient": True,
        "total": 30,
        "accuracy": 0.90,
        "baseline_accuracy": 0.75,
        "batch_accuracies": [0.90, 0.90, 0.90],
    }
    data.update(overrides)
    return data


def _real_scorer(domain: str = "trading") -> tuple[CompoundingScorer, InMemoryGraphStore]:
    store = InMemoryGraphStore(domain=domain)
    scorer = CompoundingScorer.from_preset(
        domain,
        graph_store=store,
        profile="test",
        enable_rl=False,
    )
    return scorer, store


def _learn(scorer: CompoundingScorer, count: int) -> ScoreResult:
    factors = {name: 0.7 for name in scorer._preset.shape.factor_names}
    last = None
    for _ in range(count):
        scored = scorer.score(factors, "trend_following")
        scorer.learn(scored.decision_id, scored.action, context={"preseed": True})
        last = scored
    assert last is not None
    return last


def _write_checkpoint(scorer: CompoundingScorer, scored: ScoreResult) -> str:
    checkpoint_id = "rollback-state-checkpoint"
    scorer._save_centroids_checkpoint(
        decision_id=scored.decision_id,
        category=scored.category,
        action=scored.action,
        iks=0.0,
        checkpoint_id=checkpoint_id,
        raise_on_error=True,
    )
    return checkpoint_id


def test_gate_rejects_single_batch() -> None:
    result = DefaultPromotionGate().evaluate(
        _shadow(batch_accuracies=[0.90]),
        conservation_state={"status": "GREEN"},
    )
    assert result["promoted"] is False
    assert "insufficient_batches" in str(result["reason"])


def test_gate_accepts_three_batches() -> None:
    result = DefaultPromotionGate().evaluate(
        _shadow(batch_accuracies=[0.90, 0.89, 0.91]),
        conservation_state={"status": "GREEN"},
    )
    assert result["promoted"] is True


def test_scorer_none_returns_503() -> None:
    app = FastAPI()
    mount_self_computation_router(
        app,
        InMemoryGraphStore(domain="none-provider"),
        domain="none-provider",
        scorer_provider=lambda: None,
    )
    response = TestClient(app).post("/api/self/rollback?checkpoint_id=missing")
    assert response.status_code == 503


def test_scorer_available_returns_200() -> None:
    scorer, store = _real_scorer()
    app = FastAPI()
    mount_self_computation_router(
        app,
        store,
        domain="trading",
        scorer_provider=scorer,
    )
    response = TestClient(app).get("/api/self/diagnostics")
    assert response.status_code == 200


def test_rollback_restores_decision_count_and_dk_weights() -> None:
    scorer, store = _real_scorer()
    checkpoint_source = _learn(scorer, 50)
    checkpoint_id = _write_checkpoint(scorer, checkpoint_source)
    checkpoint = next(
        item for item in store.get_centroid_checkpoints("trading", limit=None, include_v2=True)
        if item.get("checkpoint_id") == checkpoint_id
    )
    metadata = checkpoint["metadata"]
    expected_dk = np.asarray(metadata["dk_weights"], dtype=np.float64)
    expected_count = int(metadata["decision_count"])

    _learn(scorer, 50)
    scorer._scorer._dk_weights = expected_dk + 0.25
    result = scorer.rollback_to_checkpoint(checkpoint_id)

    assert result["rolled_back"] is True
    assert scorer._scorer.decision_count == expected_count == 50
    np.testing.assert_allclose(np.asarray(scorer.get_dk_weights()), expected_dk)


def test_post_rollback_scoring_matches_checkpoint() -> None:
    scorer, _ = _real_scorer()
    checkpoint_source = _learn(scorer, 50)
    checkpoint_id = _write_checkpoint(scorer, checkpoint_source)
    factors = {name: 0.35 for name in scorer._preset.shape.factor_names}
    expected = scorer.score(factors, "trend_following")

    _learn(scorer, 50)
    scorer.rollback_to_checkpoint(checkpoint_id)
    actual = scorer.score(factors, "trend_following")

    assert actual.action == expected.action
    np.testing.assert_allclose(actual.probabilities, expected.probabilities)
    assert actual.confidence == expected.confidence
