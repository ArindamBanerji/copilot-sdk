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


def test_dk_weights_change_scoring_sensitivity() -> None:
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
    for index, perturbed in ((high_index, high_perturbed), (low_index, low_perturbed)):
        value = float(baseline[names[index]])
        perturbed[names[index]] = value + delta if value <= 1.0 - delta else value - delta
        assert np.isclose(abs(perturbed[names[index]] - value), delta)

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

    learned_changes = np.asarray([sensitivity(high_perturbed), sensitivity(low_perturbed)])
    try:
        scorer.load_dk_weights_from_l5(uniform.tolist())
        uniform_changes = np.asarray([sensitivity(high_perturbed), sensitivity(low_perturbed)])
    finally:
        scorer.load_dk_weights_from_l5(learned.tolist())

    assert np.all(learned_changes > 1e-6)
    assert np.all(uniform_changes > 1e-6)
    assert np.all(np.abs(learned_changes - uniform_changes) > 1e-6)
    # Geometry also affects sensitivity: a larger weight does not guarantee
    # a larger absolute response. Test the change in relative factor influence.
    assert not np.isclose(
        learned_changes[0] / learned_changes[1],
        uniform_changes[0] / uniform_changes[1],
        rtol=1e-3,
    )


def test_conservation_status_reflects_actual_gate() -> None:
    train, _ = load_benchmark_split()
    gate = DefaultPromotionGate()
    shadow = {
        "total": 1000,
        "baseline_total": 1000,
        "sufficient": True,
        "accuracy": 0.9,
        "baseline_accuracy": 0.1,
        "batch_accuracies": [0.9, 0.9, 0.9],
    }
    for correct, expected_status in ((True, "GREEN"), (False, "RED")):
        scorer = _fresh()
        for row in train[:10]:
            scored = scorer.score(row["factors"], str(row["category"]))
            actual = scored.action if correct else next(
                action for action in scorer._preset.shape.action_names
                if action != scored.action
            )
            learned = scorer.learn(
                scored.decision_id, actual,
                persist_artifacts=False,
            )
            assert not isinstance(learned, dict)

        state = scorer.get_conservation_state()
        assert state["status"] == expected_status
        assert state["verified_count"] == 10
        safety = evaluate_conservation_safety(state)
        assert safety.available
        assert safety.promotion_allowed is correct
        result = gate.evaluate(shadow, conservation_state=state)
        assert result["promoted"] is correct
        assert result["failed_checks"] == ([] if correct else ["conservation"])
