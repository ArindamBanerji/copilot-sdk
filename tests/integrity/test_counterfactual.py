"""Counterfactual checks for factor and conservation influence."""

from __future__ import annotations

import numpy as np

from copilot_sdk.evolution.conservation_contract import evaluate_conservation_safety
from copilot_sdk.evolution.gate import DefaultPromotionGate
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer
from integrity.load_benchmark import (
    load_benchmark_split,
    load_dk_benchmark_split,
    measure_dk_weight_effect,
    train_scorer,
    train_scorer_dk,
)


def _fresh() -> CompoundingScorer:
    return CompoundingScorer.from_preset(
        "trading",
        graph_store=InMemoryGraphStore(domain="trading"),
        enable_rl=False,
        profile="test",
    )


def test_displayed_factor_influences_score() -> None:
    train, evaluation = load_benchmark_split()
    scorer = train_scorer("trading", train, 200)
    probe = evaluation[0]
    original = dict(probe["factors"])
    original_result = scorer.score_read_only(original, str(probe["category"]))

    differences: list[float] = []
    for name, value in original.items():
        flipped = dict(original)
        flipped[name] = 1.0 - float(value)
        counterfactual = scorer.score_read_only(flipped, str(probe["category"]))
        differences.append(
            float(np.max(np.abs(
                np.asarray(original_result.probabilities)
                - np.asarray(counterfactual.probabilities)
            )))
        )

    assert max(differences) > 1e-6


def test_dk_weight_reflects_actual_trust() -> None:
    train, evaluation = load_dk_benchmark_split()
    scorer = train_scorer_dk(train)
    weights = np.asarray(scorer.get_dk_weights(), dtype=float)
    active_categories = [
        i for i, category in enumerate(scorer._preset.shape.category_names)
        if scorer.get_category_phase(category) == "VARIANCE_LEARNING"
    ]
    category_index = max(active_categories, key=lambda index: float(np.ptp(weights[index])))
    high_index = int(np.argmax(weights[category_index]))
    low_index = int(np.argmin(weights[category_index]))
    assert weights[category_index, high_index] > weights[category_index, low_index]
    category = scorer._preset.shape.category_names[category_index]
    probe = next(row for row in evaluation if row["category"] == category)
    names = list(scorer._preset.shape.factor_names)
    baseline = dict(probe["factors"])
    high_perturbed = dict(baseline)
    low_perturbed = dict(baseline)
    delta = 0.2
    high_perturbed[names[high_index]] = min(1.0, float(high_perturbed[names[high_index]]) + delta)
    low_perturbed[names[low_index]] = min(1.0, float(low_perturbed[names[low_index]]) + delta)

    learned = np.asarray(scorer.get_dk_weights(), dtype=float)
    uniform = np.full_like(learned, 1.0 / learned.shape[-1])

    def sensitivity(factors: dict[str, float]) -> float:
        base = scorer.score_read_only(baseline, category)
        changed = scorer.score_read_only(factors, category)
        return float(
            np.linalg.norm(
                np.asarray(changed.probabilities) - np.asarray(base.probabilities)
            )
        )

    high_change = sensitivity(high_perturbed)
    scorer.load_dk_weights_from_l5(uniform.tolist())
    uniform_high_change = sensitivity(high_perturbed)
    scorer.load_dk_weights_from_l5(learned.tolist())

    assert high_change > uniform_high_change


def test_conservation_status_reflects_actual_gate() -> None:
    train, _ = load_benchmark_split()
    scorer = train_scorer("trading", train, 200)
    safe_state = scorer.get_conservation_state()
    safe_decision = evaluate_conservation_safety(safe_state)
    gate = DefaultPromotionGate(min_shadow_decisions=1, accuracy_floor=0.0, alpha=1.0)
    shadow = {
        "total": 100,
        "baseline_total": 100,
        "sufficient": True,
        "accuracy": 0.9,
        "baseline_accuracy": 0.1,
        "batch_accuracies": [0.9, 0.9, 0.9],
    }
    assert safe_decision.promotion_allowed
    assert gate.evaluate(shadow, conservation_state=safe_state)["checks"]["conservation"]

    unsafe_state = {**safe_state, "status": "RED", "overallSafe": False}
    unsafe_decision = evaluate_conservation_safety(unsafe_state)
    assert not unsafe_decision.promotion_allowed
    assert not gate.evaluate(shadow, conservation_state=unsafe_state)["checks"]["conservation"]
