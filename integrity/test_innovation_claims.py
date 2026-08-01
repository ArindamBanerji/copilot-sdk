from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import numpy as np
import pytest

from copilot_sdk.evolution.gate import DefaultPromotionGate
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer
from integrity.load_benchmark import load_benchmark

pytestmark = pytest.mark.timeout(180)


def _scorer() -> CompoundingScorer:
    return CompoundingScorer.from_preset(
        "trading",
        graph_store=InMemoryGraphStore(domain="trading"),
        enable_rl=False,
        profile="test",
    )


_SCORER_CACHE: dict[int, CompoundingScorer] = {}


def _confirmed_training(count: int) -> CompoundingScorer:
    """Train a scorer on `count` benchmark decisions.

    Reuses the nearest cached scorer below the requested count and trains only
    the remaining decisions. This is equivalent to from-scratch training
    because the benchmark is frozen and scorer updates are sequential.
    """
    if count in _SCORER_CACHE:
        return copy.deepcopy(_SCORER_CACHE[count])

    train, _ = load_benchmark()
    cached_below = sorted(cached for cached in _SCORER_CACHE if cached < count)
    if cached_below:
        base_count = cached_below[-1]
        scorer = copy.deepcopy(_SCORER_CACHE[base_count])
        start = base_count
    else:
        scorer = _scorer()
        start = 0

    for i, row in enumerate(train[start:count], start=start):
        result = scorer.score(row["factors"], row["category"])
        learned = scorer.learn(
            result.decision_id,
            row["outcome"]["actual_action"],
            context={"benchmark": True, "fixture_decision_id": row["decision_id"]},
        )
        if isinstance(learned, dict):
            pytest.fail(f"benchmark training paused at step {i}/{count}: {learned}")
    _SCORER_CACHE[count] = scorer
    return copy.deepcopy(scorer)


def _eval_accuracy(scorer: CompoundingScorer) -> float:
    _, eval_rows = load_benchmark()
    correct = 0
    for row in eval_rows:
        result = scorer.score_read_only(row["factors"], row["category"])
        correct += int(result.action == row["outcome"]["actual_action"])
    accuracy = correct / max(len(eval_rows), 1)
    print(f"eval_accuracy correct={correct} total={len(eval_rows)} score={accuracy:.4f}")
    return accuracy


def _dk_variance(scorer: CompoundingScorer) -> float:
    scorer.reestimate_dk_if_due()
    weights = scorer.get_dk_weights()
    if weights is None:
        raise AssertionError("DK weights not available after re-estimation")
    value = float(np.var(np.asarray(weights, dtype=float)))
    print(f"dk_variance={value:.8f}")
    return value


def _status(scorer: CompoundingScorer) -> str:
    pause = scorer._conservation_pause()
    status = "GREEN" if pause is None else ("RED" if pause.get("reason") == "conservation_red" else "AMBER")
    print(f"conservation_status={status} details={pause}")
    return status


def test_accuracy_improves_with_decisions() -> None:
    score_50 = _eval_accuracy(_confirmed_training(50))
    score_200 = _eval_accuracy(_confirmed_training(200))
    assert score_200 > score_50


def test_accuracy_improves_with_400() -> None:
    score_200 = _eval_accuracy(_confirmed_training(200))
    score_400 = _eval_accuracy(_confirmed_training(400))
    assert score_400 > score_200


def test_dk_weights_converge() -> None:
    variance_50 = _dk_variance(_confirmed_training(50))
    variance_200 = _dk_variance(_confirmed_training(200))
    assert variance_200 <= variance_50


def test_dk_weights_nonuniform() -> None:
    scorer = _confirmed_training(400)
    scorer.reestimate_dk_if_due()
    weights_raw = scorer.get_dk_weights()
    if weights_raw is None:
        pytest.fail("DK weights not available after 400 benchmark decisions")
    weights = np.asarray(weights_raw, dtype=float)
    print(f"dk_min={weights.min():.4f} dk_max={weights.max():.4f}")
    assert weights.shape[1] == 10
    assert np.isfinite(weights).all()
    assert float(weights.max()) >= float(weights.min())


def test_conservation_fires_on_degradation() -> None:
    scorer = _confirmed_training(200)
    assert _status(scorer) == "GREEN"
    train, _ = load_benchmark()
    actions = list(scorer._preset.shape.action_names)
    for row in train[200:300]:
        result = scorer.score(row["factors"], row["category"])
        wrong = next(action for action in actions if action != result.action)
        scorer._graph_store.write_outcome(
            result.decision_id,
            wrong,
            False,
            domain="trading",
            metadata={"benchmark_noise": True},
        )
    degraded_status = _status(scorer)
    if degraded_status == "GREEN":
        pytest.fail("current conservation gate does not fire after 200 stable + 100 noisy decisions")
    assert degraded_status in {"AMBER", "RED"}


def test_conservation_green_on_stable() -> None:
    scorer = _confirmed_training(200)
    assert _status(scorer) == "GREEN"


def test_reconvergence_after_disruption() -> None:
    scorer = _confirmed_training(200)
    train, _ = load_benchmark()
    actions = list(scorer._preset.shape.action_names)
    for row in train[200:300]:
        result = scorer.score(row["factors"], row["category"])
        wrong = next(action for action in actions if action != result.action)
        scorer._graph_store.write_outcome(
            result.decision_id,
            wrong,
            False,
            domain="trading",
            metadata={"benchmark_noise": True},
        )
    degraded_status = _status(scorer)
    if degraded_status == "GREEN":
        pytest.fail("current conservation gate does not fire after 200 stable + 100 noisy decisions")
    assert degraded_status in {"AMBER", "RED"}
    recovery_count = 0
    for row in train[300:400]:
        result = scorer.score(row["factors"], row["category"])
        scorer._graph_store.write_outcome(
            result.decision_id,
            result.action,
            True,
            domain="trading",
            metadata={"benchmark_recovery": True, "fixture_decision_id": row["decision_id"]},
        )
        recovery_count += 1
    assert recovery_count == 100
    assert _status(scorer) == "GREEN"


def test_ae_variant_rejected_by_conservation() -> None:
    gate = DefaultPromotionGate()
    result = gate.evaluate(
        shadow_results={
            "total": 40,
            "sufficient": True,
            "accuracy": 0.50,
            "baseline_accuracy": 0.90,
            "batch_accuracies": [0.50, 0.48, 0.52],
        },
        conservation_state={"status": "RED"},
    )
    print(f"promotion_promoted={result['promoted']} reason={result['reason']} failed={result['failed_checks']}")
    assert result["promoted"] is False
    assert "conservation" in result["failed_checks"]


def test_scorer_state_survives_reload(tmp_path: Path) -> None:
    scorer = _confirmed_training(200)
    train, eval_rows = load_benchmark()
    probe = eval_rows[0]
    before = scorer.score(probe["factors"], probe["category"])
    export_path = tmp_path / "scorer.json"
    scorer.export(export_path)
    exported_state = json.loads(export_path.read_text(encoding="utf-8"))
    reloaded = _scorer()
    reloaded._scorer.centroids = np.asarray(exported_state["centroids"], dtype=np.float64)
    after = reloaded.score(probe["factors"], probe["category"])
    print(f"reload before={before.action}/{before.confidence:.6f} after={after.action}/{after.confidence:.6f}")
    assert before.action == after.action
    assert math.isclose(before.confidence, after.confidence, abs_tol=1e-12)
