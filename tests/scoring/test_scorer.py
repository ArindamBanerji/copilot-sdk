from __future__ import annotations

import json
import sys
from dataclasses import asdict
from dataclasses import replace
from pathlib import Path
from typing import Any

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
from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
from copilot_sdk.backend.scoring_router import _json_safe
from copilot_sdk.rl import BinaryRewardFunction


@pytest.fixture
def store():
    graph_store = InMemoryGraphStore(domain="mock")
    try:
        yield graph_store
    finally:
        graph_store.close()


def build_compounding_scorer(
    mock_preset,
    store,
    graph_store=None,
    reward_function=None,
    credit_assigner=None,
    exploration_policy=None,
):
    gae_scorer = ProfileScorer(
        mu=mock_preset.bootstrap_centroids.copy(),
        actions=list(mock_preset.shape.action_names),
        categories=list(mock_preset.shape.category_names),
    )
    return CompoundingScorer(
        mock_preset,
        gae_scorer,
        graph_store=graph_store or store,
        reward_function=reward_function,
        credit_assigner=credit_assigner,
        exploration_policy=exploration_policy,
    )


def sample_factors(**overrides):
    factors = {"amount": 0.25, "risk": 0.35, "history": 0.45}
    factors.update(overrides)
    return factors


def test_from_preset_unknown_raises():
    assert "nonexistent" not in PRESET_REGISTRY

    with pytest.raises(ValueError, match="Unknown preset"):
        CompoundingScorer.from_preset("nonexistent")


def test_from_preset_with_graph_store(monkeypatch, mock_preset, tmp_path):
    graph_store = InMemoryGraphStore()
    monkeypatch.setitem(PRESET_REGISTRY, mock_preset.name, type(mock_preset))

    scorer = CompoundingScorer.from_preset(
        mock_preset.name,
        db_path=str(tmp_path / "scorer.sqlite"),
        profile="test",
        graph_store=graph_store,
    )
    try:
        assert scorer._graph_store is graph_store
    finally:
        scorer.graph_store.close()


def test_scorer_from_preset_creates_sqlite_graph_store(monkeypatch, mock_preset, tmp_path):
    monkeypatch.setitem(PRESET_REGISTRY, mock_preset.name, type(mock_preset))

    scorer = CompoundingScorer.from_preset(
        mock_preset.name,
        db_path=str(tmp_path / "scorer.sqlite"),
        profile="development",
    )
    try:
        assert isinstance(scorer._graph_store, SQLiteGraphStore)
    finally:
        scorer.graph_store.close()


def test_scorer_from_preset_accepts_custom_graph_store(monkeypatch, mock_preset, tmp_path):
    graph_store = InMemoryGraphStore()
    monkeypatch.setitem(PRESET_REGISTRY, mock_preset.name, type(mock_preset))

    scorer = CompoundingScorer.from_preset(
        mock_preset.name,
        db_path=str(tmp_path / "scorer.sqlite"),
        graph_store=graph_store,
        profile="test",
    )
    try:
        assert scorer._graph_store is graph_store
    finally:
        scorer.graph_store.close()


def test_from_preset_with_rl_components(monkeypatch, mock_preset, tmp_path):
    reward_function = BinaryRewardFunction()
    explorer = RecordingExplorer()
    credit = RecordingCreditAssigner()
    monkeypatch.setitem(PRESET_REGISTRY, mock_preset.name, type(mock_preset))

    scorer = CompoundingScorer.from_preset(
        mock_preset.name,
        db_path=str(tmp_path / "scorer.sqlite"),
        reward_function=reward_function,
        credit_assigner=credit,
        exploration_policy=explorer,
        profile="test",
    )
    try:
        assert scorer._reward_fn is reward_function
        assert scorer._credit is credit
        assert scorer._explorer is explorer
    finally:
        scorer.graph_store.close()


def test_score_returns_valid_result(mock_preset, store):
    scorer = build_compounding_scorer(mock_preset, store)

    result = scorer.score(sample_factors(), "alpha")

    assert result.action in mock_preset.shape.action_names
    assert 0 <= result.action_index < mock_preset.shape.n_actions
    assert 0.0 <= result.confidence <= 1.0
    assert len(result.probabilities) == mock_preset.shape.n_actions
    assert store.get_decision(result.decision_id, domain=store.domain)["recommended_index"] == result.action_index


def test_scorer_score_writes_to_graph_store(mock_preset, store):
    graph_store = InMemoryGraphStore()
    scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)

    result = scorer.score(sample_factors(), "alpha")

    decision = graph_store.get_decision(result.decision_id, domain=graph_store.domain)
    assert decision is not None
    assert decision["decision_id"] == result.decision_id
    assert decision["recommended_action"] == result.action
    assert decision["metadata"]["recommended_index"] == result.action_index
    assert store.get_decision(result.decision_id, domain=store.domain) is None


def test_score_read_only_returns_prediction_without_decision_write(mock_preset, store):
    graph_store = InMemoryGraphStore()
    scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)

    result = scorer.score_read_only(sample_factors(), "alpha")

    assert result.decision_id.startswith("preview-")
    assert result.action in mock_preset.shape.action_names
    assert 0 <= result.action_index < mock_preset.shape.n_actions
    assert 0.0 <= result.confidence <= 1.0
    assert len(result.probabilities) == mock_preset.shape.n_actions
    assert graph_store.count_decisions("mock") == 0
    assert graph_store.get_decision(result.decision_id, domain=graph_store.domain) is None


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
    assert store.count_verified("mock") == 1
    assert store.get_centroid_checkpoints("mock", include_v2=True)[-1]["iks"] == scorer._compute_checkpoint_iks()


def test_scorer_learn_writes_outcome_to_graph_store(mock_preset, store):
    graph_store = InMemoryGraphStore()
    scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)
    result = scorer.score(sample_factors(), "alpha")

    scorer.learn(result.decision_id, result.action)

    verified = graph_store.get_verified_decisions("test")
    assert len(verified) == 1
    assert verified[0]["decision_id"] == result.decision_id
    assert verified[0]["actual_action"] == result.action
    assert verified[0]["is_correct"] is True
    assert store.count_verified("mock") == 0


def test_scorer_learn_writes_centroids_to_graph_store(mock_preset, store):
    graph_store = InMemoryGraphStore()
    scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)
    result = scorer.score(sample_factors(), "alpha")

    learn = scorer.learn(result.decision_id, result.action)

    checkpoints = graph_store.get_centroid_checkpoints("test", include_v2=True)
    assert len(checkpoints) == 1
    assert checkpoints[0]["metadata"]["decision_id"] == result.decision_id
    assert checkpoints[0]["category"] == "alpha"
    assert checkpoints[0]["metadata"]["iks"] == scorer._compute_checkpoint_iks()
    assert checkpoints[0]["metadata"]["composite_iks"] == learn.iks_after
    assert store.get_centroid_checkpoints("mock") == []


def test_checkpoint_iks_is_canonical_centroid_drift(mock_preset, store):
    graph_store = InMemoryGraphStore()
    scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)
    scorer._scorer.centroids = scorer._scorer.centroids + 0.1

    scorer._save_centroids_checkpoint(
        decision_id="iks-checkpoint",
        category="alpha",
        action="approve",
        iks=99.0,
        checkpoint_id="iks-checkpoint",
    )

    checkpoint = graph_store.get_centroid_checkpoints("test", include_v2=True)[0]
    drift = np.linalg.norm(
        scorer._scorer.centroids - mock_preset.bootstrap_centroids,
        axis=2,
    ).mean()
    expected = 100.0 * min(float(drift) / 0.20, 1.0)
    assert checkpoint["iks"] == pytest.approx(round(expected, 1))
    assert checkpoint["metadata"]["composite_iks"] == 99.0


def test_scorer_learn_metadata_roundtrip(mock_preset, store):
    graph_store = InMemoryGraphStore()
    scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)
    result = scorer.score(sample_factors(), "beta")

    decision = graph_store.get_decision(result.decision_id, domain=graph_store.domain)
    assert decision["metadata"]["category_index"] == 1
    assert decision["metadata"]["factor_vector"] == [0.25, 0.35, 0.45]
    assert decision["metadata"]["probabilities"] == result.probabilities

    learn = scorer.learn(result.decision_id, result.action)

    assert learn.centroid_delta > 0


def test_compounding_scorer_learn_allows_on_empty_store(mock_preset, store):
    scorer = build_compounding_scorer(mock_preset, store)
    result = scorer.score(sample_factors(), "alpha")

    learn = scorer.learn(result.decision_id, result.action)

    assert learn.centroid_delta > 0
    assert store.count_verified("mock") == 1


def test_compounding_scorer_learn_pauses_when_below_threshold(mock_preset, store):
    scorer = build_compounding_scorer(mock_preset, store)
    _seed_verified_history(store, total=25, correct=0)
    result = scorer.score(sample_factors(), "alpha")
    before_centroids = scorer.gae_scorer.centroids.copy()

    learn = scorer.learn(result.decision_id, result.action)

    assert learn["status"] == "paused"
    assert learn["reason"] == "conservation_red"
    assert learn["q"] == 0.0
    assert learn["override_rate"] == pytest.approx(1.0)
    assert learn["alpha"] == pytest.approx(1 / 3)
    assert learn["theta_min"] == pytest.approx(23.53 / ((1 / 3) * 25))
    assert learn["verified_count"] == 25
    assert learn["correct_count"] == 0
    np.testing.assert_allclose(scorer.gae_scorer.centroids, before_centroids)
    assert store.count_verified("mock") == 25


def test_compounding_scorer_learn_pauses_when_low_verified_threshold_exceeds_one(
    mock_preset,
    store,
):
    scorer = build_compounding_scorer(mock_preset, store)
    _seed_verified_history(store, total=1, correct=0)
    result = scorer.score(sample_factors(), "alpha")
    before_centroids = scorer.gae_scorer.centroids.copy()

    learn = scorer.learn(result.decision_id, result.action)

    assert learn.decision_id == result.decision_id
    assert learn.centroid_delta > 0
    assert not np.allclose(scorer.gae_scorer.centroids, before_centroids)
    assert store.count_verified("mock") == 2
    assert store.count_correct("mock") == 1


def test_compounding_scorer_learn_allows_when_above_threshold(mock_preset, store):
    scorer = build_compounding_scorer(mock_preset, store)
    _seed_verified_history(store, total=100, correct=90, overrides=50)
    result = scorer.score(sample_factors(), "alpha")
    before_verified = store.count_verified("mock")

    learn = scorer.learn(result.decision_id, result.action)

    assert learn.centroid_delta > 0
    assert store.count_verified("mock") == before_verified + 1


def test_learn_without_rl_no_reward(mock_preset, store):
    scorer = build_compounding_scorer(mock_preset, store)
    result = scorer.score(sample_factors(), "alpha")

    learn = scorer.learn(result.decision_id, result.action)

    assert learn.reward is None
    assert learn.reward_raw is None
    assert learn.exploration_used is False


def test_learn_with_binary_reward_confirm(mock_preset, store):
    scorer = build_compounding_scorer(
        mock_preset,
        store,
        reward_function=BinaryRewardFunction(),
    )
    result = scorer.score(sample_factors(), "alpha")

    learn = scorer.learn(result.decision_id, result.action)

    assert learn.reward_raw == 1.0
    assert learn.reward == 1.0


def test_learn_with_binary_reward_override(mock_preset, store):
    scorer = build_compounding_scorer(
        mock_preset,
        store,
        reward_function=BinaryRewardFunction(),
    )
    result = scorer.score(sample_factors(), "alpha")
    actual_action = _other_action(mock_preset, result.action)

    learn = scorer.learn(result.decision_id, actual_action)

    assert learn.reward_raw == -1.0
    assert learn.reward == pytest.approx(-mock_preset.penalty_ratio)


def test_learn_with_reward_updates_explorer(mock_preset, store):
    explorer = RecordingExplorer()
    scorer = build_compounding_scorer(
        mock_preset,
        store,
        reward_function=BinaryRewardFunction(),
        exploration_policy=explorer,
    )
    result = scorer.score(sample_factors(), "alpha")

    scorer.learn(result.decision_id, result.action)

    assert explorer.updates == [(result.action_index, 1.0)]


def test_learn_reward_in_result(mock_preset, store):
    scorer = build_compounding_scorer(
        mock_preset,
        store,
        reward_function=BinaryRewardFunction(),
    )
    result = scorer.score(sample_factors(), "alpha")

    learn = scorer.learn(result.decision_id, result.action)

    assert learn.reward == 1.0


def test_learn_raw_reward_in_result(mock_preset, store):
    scorer = build_compounding_scorer(
        mock_preset,
        store,
        reward_function=BinaryRewardFunction(),
    )
    result = scorer.score(sample_factors(), "alpha")

    learn = scorer.learn(result.decision_id, result.action)

    assert learn.reward_raw == 1.0


def test_learn_calls_reward_function_once(mock_preset, store):
    reward = RecordingRewardFunction(value=0.75)
    scorer = build_compounding_scorer(
        mock_preset,
        store,
        reward_function=reward,
    )
    result = scorer.score(sample_factors(), "alpha")

    learn = scorer.learn(result.decision_id, result.action)

    assert len(reward.calls) == 1
    assert learn.reward_raw == 0.75
    assert learn.reward == 0.75


def test_learn_stateful_reward_uses_single_raw_value(mock_preset, store):
    reward = SequencedRewardFunction([-0.5, 1.0])
    scorer = build_compounding_scorer(
        mock_preset,
        store,
        reward_function=reward,
    )
    result = scorer.score(sample_factors(), "alpha")

    learn = scorer.learn(result.decision_id, result.action)

    assert len(reward.calls) == 1
    assert learn.reward_raw == -0.5
    assert learn.reward == pytest.approx(-0.5 * mock_preset.penalty_ratio)


def test_learn_with_credit_assigner(mock_preset, store):
    credit = RecordingCreditAssigner()
    scorer = build_compounding_scorer(
        mock_preset,
        store,
        reward_function=BinaryRewardFunction(),
        credit_assigner=credit,
    )
    result = scorer.score(sample_factors(), "alpha")

    scorer.learn(result.decision_id, result.action)

    assert credit.calls == [(1.0, ["amount", "risk", "history"])]


def test_learn_conservation_pause_skips_rl(mock_preset, store):
    graph_store = InMemoryGraphStore()
    _seed_graph_history(graph_store, total=1, correct=0)
    reward = RecordingRewardFunction()
    explorer = RecordingExplorer()
    credit = RecordingCreditAssigner()
    scorer = build_compounding_scorer(
        mock_preset,
        store,
        graph_store=graph_store,
        reward_function=reward,
        exploration_policy=explorer,
        credit_assigner=credit,
    )
    result = scorer.score(sample_factors(), "alpha")

    learn = scorer.learn(result.decision_id, result.action)

    assert learn.decision_id == result.decision_id
    assert learn.reward == pytest.approx(1.0)
    assert reward.calls == [(result.action, result.action, {"outcome": "confirmed"})]
    assert explorer.updates == [(result.action_index, 1.0)]
    assert credit.calls == [(1.0, ["amount", "risk", "history"])]


def test_learn_result_serializable(mock_preset, store):
    scorer = build_compounding_scorer(
        mock_preset,
        store,
        reward_function=BinaryRewardFunction(),
    )
    result = scorer.score(sample_factors(), "alpha")

    learn = scorer.learn(result.decision_id, result.action)
    payload = _json_safe(learn)

    assert payload == _json_safe(asdict(learn))
    assert payload["reward"] == 1.0
    assert payload["reward_raw"] == 1.0
    assert payload["exploration_used"] is False


def test_compounding_scorer_accepts_graph_store(mock_preset, store):
    graph_store = InMemoryGraphStore()
    scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)

    assert scorer._graph_store is graph_store


def test_scorer_exposes_graph_store_property(mock_preset, store):
    graph_store = InMemoryGraphStore()
    scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)

    assert scorer.graph_store is graph_store
    assert scorer.graph_store is scorer._graph_store


def test_maybe_archive_exists(mock_preset, store):
    scorer = build_compounding_scorer(mock_preset, store)

    assert callable(getattr(scorer, "_maybe_archive"))


def test_archive_triggered_on_learn(monkeypatch, mock_preset, store):
    graph_store = InMemoryGraphStore()
    scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)
    monkeypatch.setattr(scorer, "_conservation_pause", lambda: None)
    for index in range(801):
        graph_store.write_decision(
            "test",
            category="alpha",
            action="approve",
            confidence=0.7,
            factors=sample_factors(amount=0.1 + index * 0.001),
            metadata={
                "decision_id": f"archive-seed-{index}",
                "category_index": 0,
                "factor_vector": [0.1, 0.35, 0.45],
                "recommended_index": 0,
                "probabilities": [0.7, 0.3],
                "created_at": float(index),
            },
        )
    result = scorer.score(sample_factors(), "alpha")

    scorer.learn(result.decision_id, result.action)

    assert graph_store.count_decisions("test") == 800
    assert graph_store.count_archived("test") == 2


def test_maybe_archive_failure_is_non_fatal(monkeypatch, mock_preset, store):
    scorer = build_compounding_scorer(mock_preset, store)
    monkeypatch.setattr(scorer.graph_store, "count_decisions", lambda _domain: 801)

    def fail_archive(*_args, **_kwargs):
        raise RuntimeError("archive unavailable")

    monkeypatch.setattr(scorer.graph_store, "archive_old_decisions", fail_archive)

    scorer._maybe_archive()


def test_get_phase_a_on_empty(mock_preset, store):
    graph_store = InMemoryGraphStore()
    scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)

    assert scorer.get_phase() == "A"


def test_get_phase_b_after_verified(mock_preset, store):
    graph_store = InMemoryGraphStore()
    _seed_graph_history(graph_store, total=10, correct=5)
    scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)

    assert scorer.get_phase() == "B"


def test_get_alpha_zero_on_empty(mock_preset, store):
    graph_store = InMemoryGraphStore()
    scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)

    assert scorer.get_alpha() == 0.0


def test_get_alpha_correct_ratio(mock_preset, store):
    graph_store = InMemoryGraphStore()
    _seed_graph_history(graph_store, total=12, correct=7)
    scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)

    assert scorer.get_alpha() == pytest.approx(0.5833)


def test_get_phase_failure_returns_a(monkeypatch, mock_preset, store):
    graph_store = InMemoryGraphStore()
    scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)

    def fail_count_verified(_domain):
        raise RuntimeError("graph unavailable")

    monkeypatch.setattr(graph_store, "count_verified", fail_count_verified)

    assert scorer.get_phase() == "A"
    assert scorer.get_alpha() == 0.0


def test_compounding_scorer_conservation_from_graph_store(mock_preset, store):
    graph_store = InMemoryGraphStore()
    scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)
    _seed_graph_history(graph_store, total=1, correct=0)
    result = scorer.score(sample_factors(), "alpha")
    before_centroids = scorer.gae_scorer.centroids.copy()

    learn = scorer.learn(result.decision_id, result.action)

    assert learn.decision_id == result.decision_id
    assert learn.centroid_delta > 0
    assert not np.allclose(scorer.gae_scorer.centroids, before_centroids)
    assert graph_store.count_verified("test") == 2
    assert store.count_verified("mock") == 0


def test_compounding_scorer_no_graph_store_uses_sqlite(mock_preset, store):
    scorer = build_compounding_scorer(mock_preset, store)
    _seed_verified_history(store, total=1, correct=0)
    result = scorer.score(sample_factors(), "alpha")

    learn = scorer.learn(result.decision_id, result.action)

    assert learn.decision_id == result.decision_id
    assert learn.centroid_delta > 0
    assert store.count_verified("mock") == 2
    assert store.count_correct("mock") == 1


def test_compounding_scorer_graph_store_counts_match(mock_preset, store):
    graph_store = InMemoryGraphStore()
    _seed_graph_history(graph_store, total=25, correct=0)
    scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)

    assert scorer._conservation_pause()["verified_count"] == graph_store.count_verified("test")
    assert scorer._conservation_pause()["correct_count"] == graph_store.count_correct("test")


def test_scorer_conservation_reads_from_graph_store(mock_preset, store):
    graph_store = InMemoryGraphStore()
    _seed_graph_history(graph_store, total=1, correct=0)
    scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)

    pause = scorer._conservation_pause()

    assert pause is None
    assert scorer.get_verified_count() == graph_store.count_verified("test") == 1
    assert graph_store.count_correct("test") == 0


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
    assert store.count_verified("mock") == 1


def test_compounding_scorer_learn_count_method_failure_allows_learning(
    monkeypatch,
    mock_preset,
    store,
):
    scorer = build_compounding_scorer(mock_preset, store)
    result = scorer.score(sample_factors(), "alpha")
    calls = {"count_verified": 0}
    original_count_verified = scorer._graph_store.count_verified

    def flaky_count_verified(domain):
        calls["count_verified"] += 1
        if calls["count_verified"] == 1:
            raise RuntimeError("count failure")
        return original_count_verified(domain)

    monkeypatch.setattr(scorer._graph_store, "count_verified", flaky_count_verified)
    learn = scorer.learn(result.decision_id, result.action)

    assert learn.centroid_delta > 0
    assert store.count_verified("mock") == 1


def test_scorer_no_store_bypass_for_decision_writes(monkeypatch, mock_preset, store):
    graph_store = InMemoryGraphStore()
    scorer = build_compounding_scorer(mock_preset, store, graph_store=graph_store)

    def fail(*_args, **_kwargs):
        raise AssertionError("legacy storage data path used")

    monkeypatch.setattr(store, "save_decision", fail, raising=False)
    monkeypatch.setattr(store, "get_decision", fail)
    monkeypatch.setattr(store, "save_outcome", fail, raising=False)
    monkeypatch.setattr(store, "save_centroids", fail)
    monkeypatch.setattr(store, "count_verified", fail)
    monkeypatch.setattr(store, "count_correct", fail)
    monkeypatch.setattr(store, "get_all_decisions", fail)

    result = scorer.score(sample_factors(), "alpha")
    learn = scorer.learn(result.decision_id, result.action)

    assert learn.centroid_delta > 0
    assert graph_store.count_verified("test") == 1


def test_scorer_has_no_direct_store_data_calls():
    source = Path(scorer_module.__file__).read_text(encoding="utf-8")
    forbidden = [
        "self._store.save_decision",
        "self._store.save_outcome",
        "self._store.save_centroids",
        "self._store.get_decision",
        "self._store.count_verified",
        "self._store.count_correct",
        "self._store.get_all_decisions",
    ]

    for pattern in forbidden:
        assert pattern not in source


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
    _seed_verified_history(store, total=100, correct=90, overrides=50)

    for index in range(10):
        result = scorer.score(sample_factors(amount=0.2 + index * 0.01), "alpha")
        scorer.learn(result.decision_id, result.action)

    assert scorer._compute_iks() > 0
    assert store.count_verified("mock") == 110


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

    original_from_preset = CompoundingScorer.from_preset.__func__

    def test_from_preset(cls, *args, **kwargs):
        kwargs.setdefault("profile", "test")
        return original_from_preset(cls, *args, **kwargs)

    monkeypatch.setattr(CompoundingScorer, "from_preset", classmethod(test_from_preset))

    restored = CompoundingScorer.load(export_path, db_path=str(tmp_path / "restored.sqlite"))
    try:
        np.testing.assert_allclose(restored.gae_scorer.centroids, expected)
    finally:
        restored.graph_store.close()


def _seed_verified_history(
    store,
    total: int,
    correct: int,
    overrides: int | None = None,
) -> None:
    override_count = total - correct if overrides is None else overrides
    for index in range(total):
        decision_id = f"history-{index}"
        stored_id = store.write_decision(
            "mock",
            category="alpha",
            action="approve",
            confidence=0.75,
            factors=sample_factors(amount=0.1 + index * 0.001),
            metadata={
                "decision_id": decision_id,
                "category_index": 0,
                "factor_vector": [0.1 + index * 0.001, 0.35, 0.45],
                "recommended_index": 0,
                "probabilities": [0.75, 0.25],
                "created_at": 1000.0 + index,
            },
        )
        is_correct = index < correct
        is_override = index < override_count
        store.write_outcome(
            decision_id=stored_id,
            actual_action="review" if is_override else "approve",
            is_correct=is_correct,
            metadata={"actual_index": 1 if is_override else 0, "verified_at": 2000.0 + index},
            domain=store.domain,
        )


def _seed_graph_history(graph_store: InMemoryGraphStore, total: int, correct: int) -> None:
    for index in range(total):
        decision_id = graph_store.write_decision(
            getattr(graph_store, "domain", "test"),
            category="alpha",
            action="approve",
            confidence=0.8,
            factors=sample_factors(amount=10.0 + index),
            metadata={"decision_id": f"history-{index}", "entity_id": f"history-{index}", "created_at": 1000.0 + index},
        )
        is_correct = index < correct
        graph_store.write_outcome(
            decision_id,
            actual_action="approve" if is_correct else "review",
            is_correct=is_correct,
            metadata={"verified_at": 2000.0 + index},
            domain=graph_store.domain,
        )


def _other_action(mock_preset, action: str) -> str:
    for candidate in mock_preset.shape.action_names:
        if candidate != action:
            return str(candidate)
    raise AssertionError("mock preset must define at least two actions")


class RecordingExplorer:
    def __init__(self) -> None:
        self.updates: list[tuple[int, float]] = []

    def update(self, action: int, reward: float) -> None:
        self.updates.append((action, reward))


class RecordingCreditAssigner:
    def __init__(self) -> None:
        self.calls: list[tuple[float, list[str]]] = []

    def assign(self, reward: float, factors: list[str]) -> dict[str, float]:
        self.calls.append((reward, factors))
        return {factor: reward / len(factors) for factor in factors}


class RecordingRewardFunction:
    def __init__(self, value: float = 1.0) -> None:
        self.value = value
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def compute(self, recommended_action: str, actual_action: str, outcome: dict) -> float:
        self.calls.append((recommended_action, actual_action, dict(outcome)))
        return self.value


class SequencedRewardFunction:
    def __init__(self, values: list[float]) -> None:
        self.values = list(values)
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def compute(self, recommended_action: str, actual_action: str, outcome: dict) -> float:
        self.calls.append((recommended_action, actual_action, dict(outcome)))
        index = min(len(self.calls) - 1, len(self.values) - 1)
        return self.values[index]
