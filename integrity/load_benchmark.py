"""Loader for frozen benchmark fixture v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, cast, overload

import numpy as np

from copilot_sdk.scoring.scorer import CompoundingScorer


EXPECTED_VERSION = "v1"
BENCHMARK = {
    "version": EXPECTED_VERSION,
    "seed": 20260711,
    "domain": "trading",
    "n_train": 400,
    "n_eval": 100,
}
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
FACTORS_PATH = FIXTURE_DIR / "benchmark_factors_v1.json"
OUTCOMES_PATH = FIXTURE_DIR / "benchmark_outcomes_v1.json"


def _read_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _validate_header(data: dict[str, Any], key: str) -> None:
    if data.get("version") != EXPECTED_VERSION:
        raise ValueError(f"unsupported benchmark version: {data.get('version')!r}")
    if data.get("frozen") is not True:
        raise ValueError("benchmark fixture must be frozen")
    if key not in data:
        raise ValueError(f"benchmark fixture missing {key!r}")


def load_benchmark() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    factors = _read_json(FACTORS_PATH)
    outcomes = _read_json(OUTCOMES_PATH)
    _validate_header(factors, "decisions")
    _validate_header(outcomes, "outcomes")
    outcome_by_id = {
        str(row["decision_id"]): row
        for row in outcomes["outcomes"]
    }
    combined: list[dict[str, Any]] = []
    for row in factors["decisions"]:
        decision_id = str(row["decision_id"])
        outcome = outcome_by_id.get(decision_id)
        if outcome is None:
            raise ValueError(f"missing outcome for {decision_id}")
        combined.append({**row, "outcome": outcome})
    train = [row for row in combined if row.get("split") == "train"]
    eval_rows = [row for row in combined if row.get("split") == "eval"]
    if len(train) != int(factors["n_train"]) or len(eval_rows) != int(factors["n_eval"]):
        raise ValueError("benchmark split counts do not match header")
    return train, eval_rows


@overload
def load_benchmark_split() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]: ...


@overload
def load_benchmark_split(split: Literal["train", "eval"]) -> list[dict[str, Any]]: ...


def load_benchmark_split(
    split: Literal["train", "eval"] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]] | list[dict[str, Any]]:
    """Load both frozen splits, or one named split."""
    train, evaluation = load_benchmark()
    if split == "train":
        return train
    if split == "eval":
        return evaluation
    return train, evaluation


def train_scorer(
    domain: str,
    train_data: list[dict[str, Any]],
    n_decisions: int,
    *,
    profile: str = "test",
) -> CompoundingScorer:
    """Return a fresh scorer trained on a prefix of the frozen train split."""
    scorer = CompoundingScorer.from_preset(domain, profile=profile, enable_rl=False)
    limit = min(max(int(n_decisions), 0), len(train_data))
    for index, row in enumerate(train_data[:limit]):
        result = scorer.score(row["factors"], str(row["category"]))
        learned = scorer.learn(
            result.decision_id,
            str(row["outcome"]["actual_action"]),
            context={"benchmark": True, "fixture_decision_id": row["decision_id"]},
            persist_artifacts=False,
        )
        if isinstance(learned, dict):
            raise RuntimeError(f"benchmark training paused at {index}: {learned}")
    return scorer


def measure_accuracy(
    scorer: CompoundingScorer,
    eval_data: list[dict[str, Any]],
) -> float:
    """Measure accuracy only on supplied held-out evaluation rows."""
    if not eval_data:
        return 0.0
    correct = 0
    for row in eval_data:
        result = scorer.score_read_only(row["factors"], str(row["category"]))
        correct += int(result.action == str(row["outcome"]["actual_action"]))
    return float(correct / len(eval_data))


def measure_accuracy_with_weights(
    scorer: CompoundingScorer,
    eval_data: list[dict[str, Any]],
    weights: Any,
) -> float:
    """Measure held-out accuracy under temporary DK weights."""
    previous = getattr(scorer._scorer, "_dk_weights", None)
    previous_copy = None if previous is None else np.asarray(previous, dtype=float).copy()
    if not scorer.load_dk_weights_from_l5(weights):
        raise ValueError("weights do not match the scorer shape")
    try:
        return measure_accuracy(scorer, eval_data)
    finally:
        scorer._scorer._dk_weights = previous_copy


def decisions_to_threshold(
    scorer: CompoundingScorer,
    eval_data: list[dict[str, Any]],
    threshold: float,
) -> int:
    """Return the first held-out prefix whose cumulative accuracy reaches threshold."""
    if not 0.0 <= float(threshold) <= 1.0:
        raise ValueError("threshold must be in [0, 1]")
    correct = 0
    for count, row in enumerate(eval_data, start=1):
        result = scorer.score_read_only(row["factors"], str(row["category"]))
        correct += int(result.action == str(row["outcome"]["actual_action"]))
        if correct / count >= threshold:
            return count
    return len(eval_data)


def inject_disruption(scorer: CompoundingScorer, magnitude: float) -> None:
    """Apply deterministic centroid noise for repeatable disruption tests."""
    if float(magnitude) < 0.0:
        raise ValueError("magnitude must be non-negative")
    centroids = np.asarray(scorer._scorer.centroids, dtype=float)
    rng = np.random.default_rng(cast(int, BENCHMARK["seed"]))
    scorer._scorer.centroids = centroids + rng.normal(
        loc=0.0,
        scale=float(magnitude),
        size=centroids.shape,
    )
