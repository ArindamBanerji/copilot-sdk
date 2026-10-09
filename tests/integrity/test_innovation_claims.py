"""Deterministic checks for product claims about compounding intelligence."""

from __future__ import annotations

import numpy as np

from copilot_sdk.evolution.conservation_contract import evaluate_conservation_safety
from copilot_sdk.evolution.gate import DefaultPromotionGate
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.presets.trading import TradingPreset
from copilot_sdk.scoring.scorer import CompoundingScorer
from gae.kernels import L2Kernel
from integrity.load_benchmark import (
    inject_category_disruption,
    load_benchmark_split,
    load_dk_benchmark_split,
    measure_accuracy,
    measure_dk_weight_effect,
    train_scorer,
    train_scorer_dk,
)


def _fresh(domain: str = "trading") -> CompoundingScorer:
    return CompoundingScorer.from_preset(
        domain,
        graph_store=InMemoryGraphStore(domain=domain),
        enable_rl=False,
        profile="test",
    )


def test_accuracy_improves_with_learning() -> None:
    train, evaluation = load_benchmark_split()
    scorer_50 = train_scorer("trading", train, 50)
    scorer_400 = train_scorer("trading", train, 400)

    accuracy_50 = measure_accuracy(scorer_50, evaluation)
    accuracy_400 = measure_accuracy(scorer_400, evaluation)

    assert accuracy_400 > accuracy_50 + 0.03


def test_dk_weights_improve_scoring_when_active() -> None:
    train, evaluation = load_dk_benchmark_split()
    scorer = train_scorer_dk(train)
    result = measure_dk_weight_effect(scorer, evaluation)

    assert result["weights_non_uniform_ratio"] > 2.0
    assert result["n_vl_examples"] == 100
    assert result["metric"] == "mean_top_action_probability_margin"
    assert result["learned_metric"] > result["uniform_metric"]
    assert result["delta"] > 0.0


def test_conservation_prevents_bad_automation() -> None:
    train, _ = load_benchmark_split()
    gate = DefaultPromotionGate()
    promotable_shadow = {
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
        assert state["verified_count"] == 10
        assert state["correct_count"] == (10 if correct else 0)
        signal = state["alpha"] * state["q"] * state["verified_count"]
        assert (signal > state["theta_min"]) is correct
        assert state["status"] == expected_status
        safety = evaluate_conservation_safety(state)
        assert safety.available
        assert safety.promotion_allowed is correct
        result = gate.evaluate(promotable_shadow, conservation_state=state)
        assert result["promoted"] is correct
        assert result["failed_checks"] == ([] if correct else ["conservation"])


def test_sparse_disruption_preserves_learned_predictions() -> None:
    """Localized corruption retains unaffected knowledge, without a speed claim."""
    train, evaluation = load_benchmark_split()
    fresh = train_scorer("trading", train, 0)
    trained = train_scorer("trading", train, 400)
    categories = tuple(trained._preset.shape.category_names)
    selected = (categories[0],)
    category_mask = np.asarray([name in selected for name in categories])
    eval_mask = np.asarray([row["category"] in selected for row in evaluation])
    phases_before = tuple(trained.get_category_phase(name) for name in categories)
    assert phases_before == ("MEAN_CONVERGENCE",) * len(categories)
    assert isinstance(trained.gae_scorer.scoring_kernel, L2Kernel)

    centroids_before = trained.gae_scorer.centroids.copy()
    raw_weights = trained.get_dk_weights()
    assert raw_weights is not None
    weights_before = np.asarray(raw_weights).copy()
    decisions_before = trained.gae_scorer.decision_count
    probabilities_before = np.asarray(
        [
            trained.score_read_only(row["factors"], str(row["category"])).probabilities
            for row in evaluation
        ]
    )
    accuracy_before = measure_accuracy(trained, evaluation)

    affected = inject_category_disruption(trained, selected, 0.25, seed=42)

    centroids_after = trained.gae_scorer.centroids
    probabilities_after = np.asarray(
        [
            trained.score_read_only(row["factors"], str(row["category"])).probabilities
            for row in evaluation
        ]
    )
    assert affected == selected
    assert int(eval_mask.sum()) == 20
    assert int((~eval_mask).sum()) == 80
    np.testing.assert_array_equal(
        centroids_before[~category_mask], centroids_after[~category_mask]
    )
    assert not np.array_equal(
        centroids_before[category_mask], centroids_after[category_mask]
    )
    assert np.all((centroids_after >= 0.0) & (centroids_after <= 1.0))
    np.testing.assert_array_equal(
        probabilities_before[~eval_mask], probabilities_after[~eval_mask]
    )

    actions = tuple(trained._preset.shape.action_names)
    truth = np.asarray(
        [actions.index(str(row["outcome"]["actual_action"])) for row in evaluation]
    )
    predictions_before = np.argmax(probabilities_before, axis=1)
    predictions_after = np.argmax(probabilities_after, axis=1)
    np.testing.assert_array_equal(
        (predictions_before == truth)[~eval_mask],
        (predictions_after == truth)[~eval_mask],
    )
    assert np.any(predictions_before[eval_mask] != predictions_after[eval_mask])
    np.testing.assert_array_equal(weights_before, trained.get_dk_weights())
    assert phases_before == tuple(
        trained.get_category_phase(name) for name in categories
    )
    assert trained.gae_scorer.decision_count == decisions_before
    assert accuracy_before > measure_accuracy(trained, evaluation) > measure_accuracy(
        fresh, evaluation
    )


def test_iks_increases_monotonically() -> None:
    train, _ = load_benchmark_split()
    values = [
        train_scorer("trading", train, count)._compute_iks(
            persist_artifacts=False
        )
        for count in (100, 300, 400)
    ]
    assert values[0] < values[1] < values[2]


def test_penalty_multiplier_increases_override_movement() -> None:
    class UnitPenaltyPreset(TradingPreset):
        @property
        def penalty_ratio(self) -> float:
            return 1.0

    train, _ = load_benchmark_split()
    row = train[0]
    action = row["outcome"]["actual_action"]

    penalized = _fresh()
    unpenalized = _fresh()
    unpenalized._preset = UnitPenaltyPreset()
    assert penalized._preset.penalty_ratio > unpenalized._preset.penalty_ratio == 1.0
    np.testing.assert_array_equal(
        penalized.gae_scorer.centroids, unpenalized.gae_scorer.centroids
    )
    decisions = [
        scorer.score(row["factors"], str(row["category"]))
        for scorer in (penalized, unpenalized)
    ]
    assert decisions[0].action == decisions[1].action != action
    category_index = penalized._preset.shape.category_names.index(str(row["category"]))
    action_index = penalized._preset.shape.action_names.index(decisions[0].action)
    movements: list[float] = []
    for scorer, decision in zip((penalized, unpenalized), decisions, strict=True):
        before = scorer.gae_scorer.centroids[category_index, action_index].copy()
        learned = scorer.learn(
            decision.decision_id, action,
            context={"benchmark": True}, persist_artifacts=False,
        )
        assert not isinstance(learned, dict)
        movements.append(float(np.linalg.norm(
            scorer.gae_scorer.centroids[category_index, action_index] - before
        )))

    # Both updates override the same action from identical starting geometry.
    assert movements[0] > movements[1] > 0.0


def test_signal_transfer_works() -> None:
    train, evaluation = load_benchmark_split()
    trained = train_scorer("trading", train, 400)
    transferred = _fresh()
    transferred._scorer.centroids = np.asarray(trained._scorer.centroids).copy()
    untrained = _fresh()

    assert measure_accuracy(transferred, evaluation) > measure_accuracy(
        untrained, evaluation
    )


def test_five_copilots_same_engine() -> None:
    domains = ("soc", "s2p", "trading", "purchasing", "dataops")
    for domain in domains:
        scorer = _fresh(domain)
        shape = scorer._preset.shape
        factors = {name: 0.5 for name in shape.factor_names}
        result = scorer.score_read_only(factors, shape.category_names[0])
        assert result.action in shape.action_names
        assert len(result.probabilities) == shape.n_actions
        assert np.isclose(sum(result.probabilities), 1.0)
