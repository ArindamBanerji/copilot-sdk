"""Loader for frozen benchmark fixture v1."""

from __future__ import annotations

import json
import random
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Literal, cast, overload

import numpy as np

from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.scoring.presets.trading import TradingPreset
from integrity.benchmark_fixture import _outcome_action


EXPECTED_VERSION = "v1"
BENCHMARK = {
    "version": EXPECTED_VERSION,
    "seed": 20260711,
    "domain": "trading",
    "preset": "trading",
    "D": 10,
    "n_train": 400,
    "n_eval": 100,
}
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
FACTORS_PATH = FIXTURE_DIR / "benchmark_factors_v1.json"
OUTCOMES_PATH = FIXTURE_DIR / "benchmark_outcomes_v1.json"


def _read_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _validate_header(data: dict[str, Any], key: str, fixture_name: str) -> None:
    if data.get("version") != EXPECTED_VERSION:
        raise ValueError(f"unsupported benchmark version: {data.get('version')!r}")
    if data.get("frozen") is not True:
        raise ValueError("benchmark fixture must be frozen")
    for field in ("seed", "preset", "D", "n_train", "n_eval"):
        if data.get(field) != BENCHMARK[field]:
            raise ValueError(
                f"{fixture_name} benchmark {field} mismatch: "
                f"{data.get(field)!r} != {BENCHMARK[field]!r}"
            )
    if key not in data:
        raise ValueError(f"benchmark fixture missing {key!r}")
    if not isinstance(data[key], list):
        raise ValueError(f"{fixture_name} benchmark {key} must be a list")


def _decision_id(row: object, fixture_name: str) -> str:
    if not isinstance(row, dict):
        raise ValueError(f"{fixture_name} benchmark row must be an object")
    decision_id = row.get("decision_id")
    if not isinstance(decision_id, str) or not decision_id:
        raise ValueError(f"{fixture_name} benchmark row has invalid decision_id")
    return decision_id


def _validate_decisions(rows: list[object]) -> dict[str, dict[str, Any]]:
    decisions: dict[str, dict[str, Any]] = {}
    counts = {"train": 0, "eval": 0}
    expected_dimension = cast(int, BENCHMARK["D"])
    for raw_row in rows:
        decision_id = _decision_id(raw_row, "factors")
        if decision_id in decisions:
            raise ValueError(f"duplicate factor decision_id: {decision_id}")
        row = cast(dict[str, Any], raw_row)
        split = row.get("split")
        if split not in counts:
            raise ValueError(f"invalid factor split for {decision_id}: {split!r}")
        factors = row.get("factors")
        if not isinstance(factors, dict) or len(factors) != expected_dimension:
            actual = len(factors) if isinstance(factors, dict) else "not-a-mapping"
            raise ValueError(
                f"factor dimension mismatch for {decision_id}: "
                f"{actual} != {expected_dimension}"
            )
        for name, value in factors.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"factor {name!r} for {decision_id} is not numeric")
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"factor {name!r} for {decision_id} is outside [0, 1]")
        counts[cast(str, split)] += 1
        decisions[decision_id] = row
    if counts["train"] != BENCHMARK["n_train"]:
        raise ValueError(
            f"actual train count mismatch: {counts['train']} != {BENCHMARK['n_train']}"
        )
    if counts["eval"] != BENCHMARK["n_eval"]:
        raise ValueError(
            f"actual eval count mismatch: {counts['eval']} != {BENCHMARK['n_eval']}"
        )
    return decisions


def _validate_outcomes(
    rows: list[object],
    decisions: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    outcomes: dict[str, dict[str, Any]] = {}
    for raw_row in rows:
        decision_id = _decision_id(raw_row, "outcomes")
        if decision_id in outcomes:
            raise ValueError(f"duplicate outcome decision_id: {decision_id}")
        row = cast(dict[str, Any], raw_row)
        if decision_id not in decisions:
            raise ValueError(f"outcome has no factor row: {decision_id}")
        if row.get("split") != decisions[decision_id].get("split"):
            raise ValueError(f"split mismatch for decision_id: {decision_id}")
        if not isinstance(row.get("actual_action"), str) or not row["actual_action"]:
            raise ValueError(f"outcome has invalid actual_action: {decision_id}")
        outcomes[decision_id] = row
    missing = set(decisions).difference(outcomes)
    if missing:
        raise ValueError(f"missing outcome for {min(missing)}")
    return outcomes


def load_benchmark() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    factors = _read_json(FACTORS_PATH)
    outcomes = _read_json(OUTCOMES_PATH)
    _validate_header(factors, "decisions", "factors")
    _validate_header(outcomes, "outcomes", "outcomes")
    decisions_by_id = _validate_decisions(factors["decisions"])
    outcome_by_id = _validate_outcomes(outcomes["outcomes"], decisions_by_id)
    combined: list[dict[str, Any]] = []
    for row in decisions_by_id.values():
        decision_id = str(row["decision_id"])
        outcome = outcome_by_id.get(decision_id)
        if outcome is None:
            raise ValueError(f"missing outcome for {decision_id}")
        combined.append({**row, "outcome": outcome})
    train = [row for row in combined if row.get("split") == "train"]
    eval_rows = [row for row in combined if row.get("split") == "eval"]
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
    learn_data: list[dict[str, Any]],
    eval_data: list[dict[str, Any]],
    threshold: float,
) -> int:
    """Count additional verified learning updates needed on full held-out accuracy."""
    if not 0.0 <= float(threshold) <= 1.0:
        raise ValueError("threshold must be in [0, 1]")
    if measure_accuracy(scorer, eval_data) >= threshold:
        return 0
    for count, row in enumerate(learn_data, start=1):
        result = scorer.score(row["factors"], str(row["category"]))
        learned = scorer.learn(
            result.decision_id,
            str(row["outcome"]["actual_action"]),
            context={"benchmark": True, "fixture_decision_id": row["decision_id"]},
            persist_artifacts=False,
        )
        if isinstance(learned, dict):
            raise RuntimeError(f"benchmark threshold learning paused at {count}: {learned}")
        if measure_accuracy(scorer, eval_data) >= threshold:
            return count
    return len(learn_data)


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


def inject_category_disruption(
    scorer: CompoundingScorer,
    categories: Sequence[str],
    magnitude: float,
    *,
    seed: int,
) -> tuple[str, ...]:
    """Perturb a proper subset of centroid categories deterministically.

    ``magnitude`` is the Gaussian standard deviation per coordinate. Only
    selected slices are clipped to [0, 1]; other centroids, DK weights, and
    learning phases are preserved. This models localized centroid corruption,
    not a change in the benchmark's underlying outcome distribution.
    """
    selected = tuple(categories)
    category_names = tuple(scorer._preset.shape.category_names)
    if (
        not selected
        or len(set(selected)) != len(selected)
        or not set(selected) < set(category_names)
    ):
        raise ValueError("choose a nonempty, unique proper subset of categories")
    if not np.isfinite(magnitude) or magnitude <= 0.0:
        raise ValueError("magnitude must be finite and positive")

    centroids = scorer.gae_scorer.centroids.copy()
    rng = np.random.RandomState(seed)
    for category in selected:
        index = category_names.index(category)
        centroids[index] = np.clip(
            centroids[index]
            + rng.normal(loc=0.0, scale=magnitude, size=centroids[index].shape),
            0.0,
            1.0,
        )
    scorer.gae_scorer.centroids = centroids
    return selected


DK_TRAIN_DECISIONS = 1000


def load_dk_benchmark_split(
    n_train: int = DK_TRAIN_DECISIONS,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return deterministic training deep enough to activate DK scoring.

    The frozen 400-row training split is preserved verbatim. Additional rows
    follow the same balanced-category and outcome-generation pattern using a
    distinct deterministic stream in the benchmark seed family. The standard
    frozen 100-row evaluation split is returned unchanged.
    """
    requested = int(n_train)
    if requested < cast(int, BENCHMARK["n_train"]):
        raise ValueError(
            f"DK benchmark requires at least {BENCHMARK['n_train']} training rows"
        )

    train, evaluation = load_benchmark_split()
    if requested == len(train):
        return train, evaluation

    shape = TradingPreset().shape
    categories = tuple(shape.category_names)
    actions = tuple(shape.action_names)
    factors = tuple(shape.factor_names)
    rng = random.Random(cast(int, BENCHMARK["seed"]) + 1)
    expanded = list(train)
    for index in range(len(train), requested):
        category_index = index % len(categories)
        factor_values = {
            name: round(0.05 + 0.90 * rng.random(), 6)
            for name in factors
        }
        category = categories[category_index]
        decision_id = f"dk-bench-{index:04d}"
        expanded.append(
            {
                "decision_id": decision_id,
                "split": "train",
                "category": category,
                "factors": factor_values,
                "outcome": {
                    "decision_id": decision_id,
                    "split": "train",
                    "actual_action": _outcome_action(
                        factor_values,
                        factors,
                        actions,
                        category_index,
                    ),
                    "verified": True,
                    "correct": True,
                },
            }
        )
    return expanded, evaluation


def train_scorer_dk(
    train_data: list[dict[str, Any]],
    n_decisions: int = DK_TRAIN_DECISIONS,
    *,
    profile: str = "test",
) -> CompoundingScorer:
    """Train until category-level DK weights are active in scoring.

    The default 1,000 balanced Trading decisions place all five categories in
    ``VARIANCE_LEARNING``. This takes roughly 35 seconds on the reference test
    environment, so callers should allow a timeout of at least 120 seconds.
    """
    scorer = train_scorer(
        "trading",
        train_data,
        n_decisions,
        profile=profile,
    )
    if not any(
        scorer.get_category_phase(category) == "VARIANCE_LEARNING"
        for category in scorer._preset.shape.category_names
    ):
        raise RuntimeError("DK benchmark did not reach VARIANCE_LEARNING")
    return scorer


def _mean_action_margin(probabilities: list[list[float]]) -> float:
    values = np.asarray(probabilities, dtype=np.float64)
    if values.ndim != 2 or values.shape[0] == 0 or values.shape[1] < 2:
        raise ValueError("action probabilities must contain at least two actions")
    ordered = np.sort(values, axis=1)
    return float(np.mean(ordered[:, -1] - ordered[:, -2]))


def measure_dk_weight_effect(
    scorer: CompoundingScorer,
    eval_data: list[dict[str, Any]],
) -> dict[str, Any]:
    """Measure active DK weights by mean top-action probability margin.

    Only evaluation rows whose categories are in ``VARIANCE_LEARNING`` are
    included. Higher margin means the scorer separates its first and second
    action choices more clearly. The learned tensor is restored even if the
    uniform-weight comparison raises.
    """
    vl_categories = [
        category
        for category in scorer._preset.shape.category_names
        if scorer.get_category_phase(category) == "VARIANCE_LEARNING"
    ]
    vl_rows = [row for row in eval_data if row.get("category") in vl_categories]
    if not vl_rows:
        raise ValueError("no evaluation examples in VARIANCE_LEARNING categories")

    raw_weights = scorer.get_dk_weights()
    if raw_weights is None:
        raise ValueError("DK weights are unavailable")
    learned_weights = np.asarray(raw_weights, dtype=np.float64)
    if learned_weights.ndim != 2 or not np.all(np.isfinite(learned_weights)):
        raise ValueError("DK weights must be a finite category-by-factor tensor")
    minimum = float(np.min(learned_weights))
    if minimum <= 0.0:
        raise ValueError("DK weights must be positive")

    def probabilities_for(weights: np.ndarray) -> list[list[float]]:
        scorer.load_dk_weights_from_l5(weights)
        return [
            scorer.score_read_only(
                row["factors"],
                str(row["category"]),
            ).probabilities
            for row in vl_rows
        ]

    try:
        learned_metric = _mean_action_margin(probabilities_for(learned_weights))
        uniform = np.ones_like(learned_weights) / learned_weights.shape[1]
        uniform_metric = _mean_action_margin(probabilities_for(uniform))
    finally:
        scorer.load_dk_weights_from_l5(learned_weights)

    return {
        "vl_categories": vl_categories,
        "n_vl_examples": len(vl_rows),
        "learned_metric": learned_metric,
        "uniform_metric": uniform_metric,
        "delta": learned_metric - uniform_metric,
        "weights_non_uniform_ratio": float(np.max(learned_weights) / minimum),
        "metric": "mean_top_action_probability_margin",
    }
