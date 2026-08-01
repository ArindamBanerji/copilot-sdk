"""Regression tests for incremental innovation-claim benchmark training."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from integrity import test_innovation_claims as claims
from integrity.load_benchmark import load_benchmark


def _train_from_scratch(count: int):
    train, _ = load_benchmark()
    scorer = claims._scorer()
    for row in train[:count]:
        result = scorer.score(row["factors"], row["category"])
        learned = scorer.learn(
            result.decision_id,
            row["outcome"]["actual_action"],
            context={"benchmark": True, "fixture_decision_id": row["decision_id"]},
        )
        if isinstance(learned, dict):
            pytest.fail(f"benchmark training paused during scratch run: {learned}")
    return scorer


def _conservation_values(scorer) -> tuple[int, float]:
    verified = scorer._graph_store.count_verified(scorer._domain)
    correct = scorer._graph_store.count_correct(scorer._domain)
    return verified, correct / verified


def _assert_equivalent(expected, actual) -> None:
    np.testing.assert_allclose(
        np.asarray(expected._scorer.centroids),
        np.asarray(actual._scorer.centroids),
    )
    expected_weights = expected.get_dk_weights()
    actual_weights = actual.get_dk_weights()
    if expected_weights is None or actual_weights is None:
        assert expected_weights is actual_weights
    else:
        np.testing.assert_allclose(expected_weights, actual_weights)
    expected_v, expected_q = _conservation_values(expected)
    actual_v, actual_q = _conservation_values(actual)
    assert expected_v == actual_v
    np.testing.assert_allclose(expected_q, actual_q)


def test_incremental_matches_from_scratch_50() -> None:
    claims._SCORER_CACHE.clear()
    scratch = _train_from_scratch(50)
    claims._confirmed_training(25)
    incremental = claims._confirmed_training(50)

    _assert_equivalent(scratch, incremental)


def test_incremental_matches_from_scratch_200() -> None:
    claims._SCORER_CACHE.clear()
    scratch = _train_from_scratch(200)
    claims._confirmed_training(50)
    incremental = claims._confirmed_training(200)

    _assert_equivalent(scratch, incremental)


def test_cache_reuse_returns_independent_copies() -> None:
    claims._SCORER_CACHE.clear()
    first = claims._confirmed_training(50)
    second = claims._confirmed_training(50)
    original = np.asarray(second._scorer.centroids).copy()

    first._scorer.centroids[0, 0, 0] += 1.0

    np.testing.assert_array_equal(second._scorer.centroids, original)


def test_incremental_no_cache_trains_from_zero() -> None:
    claims._SCORER_CACHE.clear()
    scorer = claims._confirmed_training(10)

    verified, _ = _conservation_values(scorer)
    assert verified == 10
    assert 10 in claims._SCORER_CACHE


def test_conservation_pause_failure_message_is_preserved() -> None:
    source = Path(claims.__file__).read_text(encoding="utf-8")

    assert "benchmark training paused at step {i}/{count}: {learned}" in source


def test_write_outcome_in_benchmark_uses_correct_domain() -> None:
    claims._SCORER_CACHE.clear()
    scorer = claims._confirmed_training(5)
    train, _ = load_benchmark()
    row = train[5]
    result = scorer.score(row["factors"], row["category"])

    scorer._graph_store.write_outcome(
        result.decision_id,
        result.action,
        True,
        domain="trading",
        metadata={"benchmark": True},
    )

    decision = scorer._graph_store.get_decision(
        result.decision_id,
        domain="trading",
    )
    assert decision is not None
    assert decision["domain"] == "trading"
