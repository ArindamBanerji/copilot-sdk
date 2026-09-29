from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pytest

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
from integrity import load_benchmark as benchmark_loader


def _write_tampered_fixtures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    mutate_factors: Callable[[dict[str, Any]], None] | None = None,
    mutate_outcomes: Callable[[dict[str, Any]], None] | None = None,
) -> None:
    factors = json.loads(Path(FACTORS_PATH).read_text(encoding="utf-8"))
    outcomes = json.loads(Path(OUTCOMES_PATH).read_text(encoding="utf-8"))
    if mutate_factors is not None:
        mutate_factors(factors)
    if mutate_outcomes is not None:
        mutate_outcomes(outcomes)
    factors_path = tmp_path / "factors.json"
    outcomes_path = tmp_path / "outcomes.json"
    factors_path.write_text(json.dumps(factors), encoding="utf-8")
    outcomes_path.write_text(json.dumps(outcomes), encoding="utf-8")
    monkeypatch.setattr(benchmark_loader, "FACTORS_PATH", factors_path)
    monkeypatch.setattr(benchmark_loader, "OUTCOMES_PATH", outcomes_path)


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
    assert 0 <= decisions_to_threshold(scorer, train[50:60], evaluation, 0.25) <= 10


def test_threshold_not_lucky_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    train, evaluation = load_benchmark_split()
    scorer = train_scorer("trading", train, 5)
    observed_eval_sets: list[list[dict[str, Any]]] = []
    accuracies = iter((0.1, 0.2, 0.6))

    def full_eval(_scorer: object, rows: list[dict[str, Any]]) -> float:
        observed_eval_sets.append(rows)
        return next(accuracies)

    monkeypatch.setattr(benchmark_loader, "measure_accuracy", full_eval)
    before = scorer.get_verified_count()

    count = decisions_to_threshold(scorer, train[5:10], evaluation, 0.5)

    assert count == 2
    assert scorer.get_verified_count() == before + 2
    assert observed_eval_sets == [evaluation, evaluation, evaluation]


def test_malformed_seed_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_tampered_fixtures(
        tmp_path,
        monkeypatch,
        mutate_factors=lambda data: data.__setitem__("seed", 42),
    )
    with pytest.raises(ValueError, match="seed mismatch"):
        benchmark_loader.load_benchmark_split()


def test_malformed_dimensions_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def remove_factor(data: dict[str, Any]) -> None:
        data["decisions"][0]["factors"].pop(next(iter(data["decisions"][0]["factors"])))

    _write_tampered_fixtures(tmp_path, monkeypatch, mutate_factors=remove_factor)
    with pytest.raises(ValueError, match="factor dimension mismatch"):
        benchmark_loader.load_benchmark_split()


def test_malformed_range_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def exceed_range(data: dict[str, Any]) -> None:
        first_factor = next(iter(data["decisions"][0]["factors"]))
        data["decisions"][0]["factors"][first_factor] = 1.1

    _write_tampered_fixtures(tmp_path, monkeypatch, mutate_factors=exceed_range)
    with pytest.raises(ValueError, match=r"outside \[0, 1\]"):
        benchmark_loader.load_benchmark_split()


def test_missing_outcome_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_tampered_fixtures(
        tmp_path,
        monkeypatch,
        mutate_outcomes=lambda data: data["outcomes"].pop(),
    )
    with pytest.raises(ValueError, match="missing outcome"):
        benchmark_loader.load_benchmark_split()


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
