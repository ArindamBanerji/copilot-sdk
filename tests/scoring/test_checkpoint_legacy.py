from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from gae.profile_scorer import ProfileScorer

from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.transfer import TransferPattern


@pytest.fixture(autouse=True)
def isolate_persistence_outbox(tmp_path: Path) -> Iterator[None]:
    previous = os.environ.get("CI_PERSISTENCE_OUTBOX_PATH")
    os.environ["CI_PERSISTENCE_OUTBOX_PATH"] = str(tmp_path / "persistence-outbox.db")
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("CI_PERSISTENCE_OUTBOX_PATH", None)
        else:
            os.environ["CI_PERSISTENCE_OUTBOX_PATH"] = previous


def _scorer(mock_preset: Any, store: InMemoryGraphStore) -> CompoundingScorer:
    engine = ProfileScorer(
        mu=mock_preset.bootstrap_centroids.copy(),
        actions=list(mock_preset.shape.action_names),
        categories=list(mock_preset.shape.category_names),
    )
    return CompoundingScorer(mock_preset, engine, graph_store=store)


def _score_and_learn(
    scorer: CompoundingScorer,
    mock_preset: Any,
    iteration: int = 0,
) -> None:
    category = mock_preset.shape.category_names[iteration % mock_preset.shape.n_categories]
    result = scorer.score(
        {"amount": 0.25, "risk": 0.35, "history": 0.45},
        category,
    )
    scorer.learn(result.decision_id, result.action)


def test_learn_writes_v2_checkpoint_not_legacy(mock_preset: Any) -> None:
    store = InMemoryGraphStore(domain="mock")
    scorer = _scorer(mock_preset, store)
    try:
        _score_and_learn(scorer, mock_preset)

        assert len(store._protocol_centroid_checkpoints) >= 1
        assert len(store._centroid_checkpoints) == 0
    finally:
        store.close()


def test_explicit_write_legacy_true_still_writes_both(mock_preset: Any) -> None:
    store = InMemoryGraphStore(domain="mock")
    scorer = _scorer(mock_preset, store)
    try:
        scorer._save_centroids_checkpoint(
            decision_id="explicit-legacy",
            category=mock_preset.shape.category_names[0],
            action=mock_preset.shape.action_names[0],
            iks=1.0,
            write_legacy=True,
        )

        assert len(store._protocol_centroid_checkpoints) == 1
        assert len(store._centroid_checkpoints) == 1
    finally:
        store.close()


def test_trajectory_works_from_v2_checkpoints_only(mock_preset: Any) -> None:
    store = InMemoryGraphStore(domain="mock")
    scorer = _scorer(mock_preset, store)
    try:
        for iteration in range(40):
            _score_and_learn(scorer, mock_preset, iteration)

        trajectory = scorer.trajectory()

        assert trajectory.points
        assert trajectory.decisions_total == 40
        assert trajectory.points == sorted(
            trajectory.points,
            key=lambda point: (point.decisions, point.timestamp),
        )
        assert len(store._centroid_checkpoints) == 0
    finally:
        store.close()


def test_checkpoint_count_matches_expected(mock_preset: Any) -> None:
    store = InMemoryGraphStore(domain="mock")
    scorer = _scorer(mock_preset, store)
    try:
        for _ in range(5):
            _score_and_learn(scorer, mock_preset)

        assert len(store._protocol_centroid_checkpoints) == 5
        assert len(store._centroid_checkpoints) == 0
    finally:
        store.close()


def test_warm_start_centroid_save_unaffected(mock_preset: Any) -> None:
    store = InMemoryGraphStore(domain="mock")
    scorer = _scorer(mock_preset, store)
    pattern = TransferPattern(
        pattern_id="warm-start-test",
        source_copilot="source",
        pattern_type="centroid_delta",
        category=mock_preset.shape.category_names[0],
        action=mock_preset.shape.action_names[0],
        win_rate=0.8,
        centroid_delta=[1.0] * mock_preset.shape.n_factors,
        confidence=0.8,
    )
    try:
        result = scorer.warm_start([pattern])

        assert result["applied"] == 1
        assert len(store._centroid_checkpoints) == 1
        assert store._centroid_checkpoints[0]["metadata"]["source"] == "warm_start"
    finally:
        store.close()
