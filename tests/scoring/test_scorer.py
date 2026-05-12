from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

GAE_PATH = Path(__file__).resolve().parents[2] / "graph-attention-engine-v50"
if str(GAE_PATH) not in sys.path:
    sys.path.insert(0, str(GAE_PATH))

profile_module = pytest.importorskip("gae.profile_scorer")
ProfileScorer = profile_module.ProfileScorer

from copilot_sdk.scoring.presets import PRESET_REGISTRY
from copilot_sdk.scoring import scorer as scorer_module
from copilot_sdk.scoring.scorer import CompoundingScorer


def build_compounding_scorer(mock_preset, store):
    gae_scorer = ProfileScorer(
        mu=mock_preset.bootstrap_centroids.copy(),
        actions=list(mock_preset.shape.action_names),
        categories=list(mock_preset.shape.category_names),
    )
    return CompoundingScorer(mock_preset, store, gae_scorer)


def sample_factors(**overrides):
    factors = {"amount": 0.25, "risk": 0.35, "history": 0.45}
    factors.update(overrides)
    return factors


def test_from_preset_unknown_raises():
    assert "nonexistent" not in PRESET_REGISTRY

    with pytest.raises(ValueError, match="Unknown preset"):
        CompoundingScorer.from_preset("nonexistent")


def test_score_returns_valid_result(mock_preset, store):
    scorer = build_compounding_scorer(mock_preset, store)

    result = scorer.score(sample_factors(), "alpha")

    assert result.action in mock_preset.shape.action_names
    assert 0 <= result.action_index < mock_preset.shape.n_actions
    assert 0.0 <= result.confidence <= 1.0
    assert len(result.probabilities) == mock_preset.shape.n_actions
    assert store.get_decision(result.decision_id)["recommended_index"] == result.action_index


def test_score_probabilities_sum_to_1(mock_preset, store):
    scorer = build_compounding_scorer(mock_preset, store)

    result = scorer.score(sample_factors(), "alpha")

    assert sum(result.probabilities) == pytest.approx(1.0)


def test_score_unknown_category_raises(mock_preset, store):
    scorer = build_compounding_scorer(mock_preset, store)

    with pytest.raises(AssertionError, match="unknown category"):
        scorer.score(sample_factors(), "unknown")


def test_score_unknown_factor_raises(mock_preset, store):
    scorer = build_compounding_scorer(mock_preset, store)

    with pytest.raises(AssertionError, match="unknown factors"):
        scorer.score(sample_factors(extra=0.8), "alpha")


def test_learn_changes_centroids(mock_preset, store):
    scorer = build_compounding_scorer(mock_preset, store)
    result = scorer.score(sample_factors(), "alpha")

    learn = scorer.learn(result.decision_id, result.action)

    assert learn.centroid_delta > 0
    assert store.count_verified() == 1
    assert store.get_centroid_checkpoints()[-1]["iks"] == learn.iks_after


def test_compounding_scorer_learn_allows_on_empty_store(mock_preset, store):
    scorer = build_compounding_scorer(mock_preset, store)
    result = scorer.score(sample_factors(), "alpha")

    learn = scorer.learn(result.decision_id, result.action)

    assert learn.centroid_delta > 0
    assert store.count_verified() == 1


def test_compounding_scorer_learn_pauses_when_below_threshold(mock_preset, store):
    scorer = build_compounding_scorer(mock_preset, store)
    _seed_verified_history(store, total=25, correct=0)
    result = scorer.score(sample_factors(), "alpha")
    before_centroids = scorer.gae_scorer.centroids.copy()

    learn = scorer.learn(result.decision_id, result.action)

    assert learn["status"] == "paused"
    assert learn["reason"] == "conservation_red"
    assert learn["q"] == 0.0
    assert learn["theta_min"] == pytest.approx(23.53 / (mock_preset.penalty_ratio * 25))
    assert learn["verified_count"] == 25
    assert learn["correct_count"] == 0
    np.testing.assert_allclose(scorer.gae_scorer.centroids, before_centroids)
    assert store.count_verified() == 25


def test_compounding_scorer_learn_pauses_when_low_verified_threshold_exceeds_one(
    mock_preset,
    store,
):
    scorer = build_compounding_scorer(mock_preset, store)
    _seed_verified_history(store, total=1, correct=0)
    result = scorer.score(sample_factors(), "alpha")
    before_centroids = scorer.gae_scorer.centroids.copy()

    learn = scorer.learn(result.decision_id, result.action)

    assert learn["status"] == "paused"
    assert learn["reason"] == "conservation_red"
    assert learn["q"] == 0.0
    assert learn["theta_min"] == pytest.approx(23.53 / mock_preset.penalty_ratio)
    assert learn["verified_count"] == 1
    assert learn["correct_count"] == 0
    np.testing.assert_allclose(scorer.gae_scorer.centroids, before_centroids)
    assert store.count_verified() == 1


def test_compounding_scorer_learn_allows_when_above_threshold(mock_preset, store):
    scorer = build_compounding_scorer(mock_preset, store)
    _seed_verified_history(store, total=25, correct=25)
    result = scorer.score(sample_factors(), "alpha")
    before_verified = store.count_verified()

    learn = scorer.learn(result.decision_id, result.action)

    assert learn.centroid_delta > 0
    assert store.count_verified() == before_verified + 1


def test_compounding_scorer_learn_store_failure_allows_learning(
    monkeypatch,
    mock_preset,
    store,
):
    scorer = build_compounding_scorer(mock_preset, store)
    result = scorer.score(sample_factors(), "alpha")

    def fail_counts(_store):
        raise RuntimeError("count failure")

    monkeypatch.setattr(scorer_module, "_conservation_counts", fail_counts)
    learn = scorer.learn(result.decision_id, result.action)

    assert learn.centroid_delta > 0
    assert store.count_verified() == 1


def test_compounding_scorer_learn_count_method_failure_allows_learning(
    monkeypatch,
    mock_preset,
    store,
):
    scorer = build_compounding_scorer(mock_preset, store)
    result = scorer.score(sample_factors(), "alpha")
    calls = {"count_verified": 0}
    original_count_verified = store.count_verified

    def flaky_count_verified():
        calls["count_verified"] += 1
        if calls["count_verified"] == 1:
            raise RuntimeError("count failure")
        return original_count_verified()

    monkeypatch.setattr(store, "count_verified", flaky_count_verified)
    learn = scorer.learn(result.decision_id, result.action)

    assert learn.centroid_delta > 0
    assert store.count_verified() == 1


def test_score_learn_score_centroid_delta_is_invariant(mock_preset, store):
    scorer = build_compounding_scorer(mock_preset, store)
    first = scorer.score(sample_factors(), "alpha")

    learn = scorer.learn(first.decision_id, first.action)
    second = scorer.score(sample_factors(), "alpha")

    assert learn.centroid_delta > 0
    assert 0.0 <= second.confidence <= 1.0


def test_iks_zero_at_start(mock_preset, store):
    scorer = build_compounding_scorer(mock_preset, store)

    assert scorer._compute_iks() == 0.0


def test_iks_increases_with_correct_decisions(mock_preset, store):
    high_penalty_preset = replace(mock_preset, penalty_ratio=100.0)
    scorer = build_compounding_scorer(high_penalty_preset, store)

    for index in range(10):
        result = scorer.score(sample_factors(amount=0.2 + index * 0.01), "alpha")
        scorer.learn(result.decision_id, result.action)

    assert scorer._compute_iks() > 0
    assert store.count_verified() == 10


def test_export_json_contains_state(mock_preset, store, tmp_path):
    scorer = build_compounding_scorer(mock_preset, store)
    for index in range(3):
        result = scorer.score(sample_factors(risk=0.3 + index * 0.02), "beta")
        scorer.learn(result.decision_id, result.action)

    export_path = tmp_path / "state.json"
    scorer.export(export_path)
    state = json.loads(export_path.read_text(encoding="utf-8"))

    assert state["domain"] == mock_preset.name
    assert "centroids" in state
    assert len(state["decisions"]) == 3
    assert state["shape"] == {
        "n_categories": 3,
        "n_actions": 2,
        "n_factors": 3,
        "categories": ["alpha", "beta", "gamma"],
        "actions": ["approve", "review"],
        "factors": ["amount", "risk", "history"],
    }


def test_load_restores_centroids(monkeypatch, mock_preset, store, tmp_path):
    scorer = build_compounding_scorer(mock_preset, store)
    result = scorer.score(sample_factors(), "gamma")
    scorer.learn(result.decision_id, result.action)

    export_path = tmp_path / "state.json"
    scorer.export(export_path)
    expected = scorer.gae_scorer.centroids.copy()
    monkeypatch.setitem(PRESET_REGISTRY, mock_preset.name, type(mock_preset))

    restored = CompoundingScorer.load(export_path, db_path=str(tmp_path / "restored.sqlite"))
    try:
        np.testing.assert_allclose(restored.gae_scorer.centroids, expected)
    finally:
        restored.store.close()


def _seed_verified_history(store, total: int, correct: int) -> None:
    for index in range(total):
        decision_id = f"history-{index}"
        store.save_decision(
            decision_id=decision_id,
            domain="mock",
            category="alpha",
            category_index=0,
            factors=sample_factors(amount=0.1 + index * 0.001),
            factor_vector=[0.1 + index * 0.001, 0.35, 0.45],
            recommended_action="approve",
            recommended_index=0,
            confidence=0.75,
            probabilities=[0.75, 0.25],
            created_at=1000.0 + index,
        )
        is_correct = index < correct
        store.save_outcome(
            decision_id=decision_id,
            actual_action="approve" if is_correct else "review",
            actual_index=0 if is_correct else 1,
            is_correct=is_correct,
            verified_at=2000.0 + index,
        )
