"""Checks for scorer state persistence and verified-judgment memory."""

from __future__ import annotations

import json

import numpy as np
import pytest

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer
from integrity.load_benchmark import load_benchmark_split, train_scorer


def _fresh() -> CompoundingScorer:
    return CompoundingScorer.from_preset(
        "trading",
        graph_store=InMemoryGraphStore(domain="trading"),
        enable_rl=False,
        profile="test",
    )


def test_export_load_preserves_centroids(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TRADING_PROFILE", "test")
    train, evaluation = load_benchmark_split()
    scorer = train_scorer("trading", train, 100)
    probe = evaluation[0]
    before = scorer.score_read_only(probe["factors"], str(probe["category"]))
    centroids_before = np.asarray(scorer._scorer.centroids).copy()
    export_path = tmp_path / "scorer-state.json"

    scorer.export(export_path)
    exported = json.loads(export_path.read_text(encoding="utf-8"))
    reloaded = CompoundingScorer.load(export_path)
    after = reloaded.score_read_only(probe["factors"], str(probe["category"]))

    assert np.array_equal(centroids_before, np.asarray(reloaded._scorer.centroids))
    assert exported["centroids"] == centroids_before.tolist()
    assert before.action == after.action
    assert before.confidence == pytest.approx(after.confidence)


def test_graphstore_preserves_decision_order() -> None:
    scorer = _fresh()
    train, _ = load_benchmark_split()
    generated_ids: list[str] = []
    for row in train[:20]:
        result = scorer.score(row["factors"], str(row["category"]))
        generated_ids.append(result.decision_id)

    stored = scorer._graph_store.get_decisions("trading", limit=100)
    stored_ids = [str(row["decision_id"]) for row in stored]
    assert stored_ids == generated_ids


def test_verified_count_matches_scorer() -> None:
    train, _ = load_benchmark_split()
    scorer = train_scorer("trading", train, 25)

    store_count = scorer._graph_store.count_verified("trading")
    scorer_count = scorer.get_verified_count()
    cached_belief = len(scorer._verified_decisions())

    assert store_count == 25
    assert scorer_count == store_count
    assert cached_belief == store_count


def test_centroid_moves_toward_verified_outcome() -> None:
    scorer = _fresh()
    train, _ = load_benchmark_split()
    row = train[0]
    result = scorer.score(row["factors"], str(row["category"]))
    category_index = scorer._preset.shape.category_names.index(str(row["category"]))
    actual_index = scorer._preset.shape.action_names.index(
        str(row["outcome"]["actual_action"])
    )
    factor_vector = np.asarray(
        [row["factors"][name] for name in scorer._preset.shape.factor_names],
        dtype=float,
    )
    old_centroid = np.asarray(scorer._scorer.centroids[category_index, actual_index]).copy()
    scorer.learn(
        result.decision_id,
        str(row["outcome"]["actual_action"]),
        context={"benchmark": True},
        persist_artifacts=False,
    )
    new_centroid = np.asarray(scorer._scorer.centroids[category_index, actual_index])

    def cosine(left: np.ndarray, right: np.ndarray) -> float:
        denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
        return float(np.dot(left, right) / denominator) if denominator else 0.0

    assert cosine(new_centroid, factor_vector) > cosine(old_centroid, factor_vector)
