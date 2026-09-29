from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from integrity.benchmark_fixture import SEED, build_fixture
from integrity.load_benchmark import (
    BENCHMARK,
    FACTORS_PATH,
    OUTCOMES_PATH,
    decisions_to_threshold,
    inject_disruption,
    load_benchmark_split,
    measure_accuracy,
    measure_accuracy_with_weights,
    train_scorer,
)


def test_fixture_loads_with_frozen_split_and_shape() -> None:
    train, evaluation = load_benchmark_split()
    assert len(train) == 400
    assert len(evaluation) == 100
    assert len(train[0]["factors"]) == 10
    assert BENCHMARK["seed"] == 20260711


def test_fixture_generation_is_deterministic_and_matches_files() -> None:
    factors, outcomes = build_fixture()
    assert SEED == 20260711
    assert factors == json.loads(Path(FACTORS_PATH).read_text(encoding="utf-8"))
    assert outcomes == json.loads(Path(OUTCOMES_PATH).read_text(encoding="utf-8"))


def test_train_and_evaluation_sets_never_overlap() -> None:
    train, evaluation = load_benchmark_split()
    train_ids = {row["decision_id"] for row in train}
    evaluation_ids = {row["decision_id"] for row in evaluation}
    assert train_ids.isdisjoint(evaluation_ids)


def test_train_scorer_runs_with_fresh_state() -> None:
    train = load_benchmark_split("train")
    first = train_scorer("trading", train, 5)
    second = train_scorer("trading", train, 5)
    assert first is not second
    assert first.get_verified_count() == 5
    assert second.get_verified_count() == 5


def test_measure_accuracy_is_bounded_on_held_out_data() -> None:
    train, evaluation = load_benchmark_split()
    scorer = train_scorer("trading", train, 100)
    accuracy = measure_accuracy(scorer, evaluation)
    assert 0.0 <= accuracy <= 1.0


def test_trained_scorer_outperforms_random_on_held_out_data() -> None:
    train, evaluation = load_benchmark_split()
    scorer = train_scorer("trading", train, 200)
    assert measure_accuracy(scorer, evaluation) > 0.25


def test_temporary_weights_and_threshold_helpers_preserve_contract() -> None:
    train, evaluation = load_benchmark_split()
    scorer = train_scorer("trading", train, 50)
    weights = np.ones((5, 10), dtype=float)
    accuracy = measure_accuracy_with_weights(scorer, evaluation, weights)
    assert 0.0 <= accuracy <= 1.0
    assert 1 <= decisions_to_threshold(scorer, evaluation, 0.25) <= 100


def test_disruption_changes_centroid_state() -> None:
    train = load_benchmark_split("train")
    scorer = train_scorer("trading", train, 100)
    before = np.asarray(scorer._scorer.centroids).copy()
    inject_disruption(scorer, magnitude=2.0)
    assert not np.array_equal(before, scorer._scorer.centroids)


def test_disruption_affects_held_out_accuracy() -> None:
    train, evaluation = load_benchmark_split()
    scorer = train_scorer("trading", train, 200)
    before = measure_accuracy(scorer, evaluation)
    inject_disruption(scorer, magnitude=2.0)
    after = measure_accuracy(scorer, evaluation)
    assert after != before
