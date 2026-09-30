"""Deterministic checks for product claims about compounding intelligence."""

from __future__ import annotations

import numpy as np

from copilot_sdk.evolution.conservation_contract import evaluate_conservation_safety
from copilot_sdk.evolution.gate import DefaultPromotionGate
from copilot_sdk.graph.memory_store import InMemoryGraphStore
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
    scorer = train_scorer("trading", train, 200)
    green_state = scorer.get_conservation_state()
    green = evaluate_conservation_safety(green_state)
    assert green.promotion_allowed is True

    gate = DefaultPromotionGate(
        min_shadow_decisions=1,
        accuracy_floor=0.0,
        superiority_threshold_pp=-100.0,
        alpha=1.0,
    )
    promotable_shadow = {
        "total": 100,
        "baseline_total": 100,
        "sufficient": True,
        "accuracy": 0.9,
        "baseline_accuracy": 0.1,
        "batch_accuracies": [0.9, 0.9, 0.9],
    }
    green_gate = gate.evaluate(promotable_shadow, conservation_state=green_state)
    assert green_gate["checks"]["conservation"] is True

    # Exercise the production contract with a concrete unsafe snapshot. The
    # scorer's conservation panel is derived from its store and cannot be
    # forced RED by replacing fixture outcomes after the fact.
    red_state = {"status": "RED"}
    red = evaluate_conservation_safety(red_state)
    assert red.available is True
    assert red.promotion_allowed is False
    red_gate = gate.evaluate(promotable_shadow, conservation_state=red_state)
    assert red_gate["checks"]["conservation"] is False


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


def test_penalty_asymmetry_is_conservative() -> None:
    train, _ = load_benchmark_split()
    row = train[0]
    action = row["outcome"]["actual_action"]

    confirmed = _fresh()
    confirmed_decision = confirmed.score(row["factors"], str(row["category"]))
    confirmed_before = np.asarray(confirmed._scorer.centroids).copy()
    confirmed.learn(
        confirmed_decision.decision_id,
        confirmed_decision.action,
        context={"benchmark": True},
        persist_artifacts=False,
    )
    confirmed_movement = float(
        np.linalg.norm(np.asarray(confirmed._scorer.centroids) - confirmed_before)
    )

    overridden = _fresh()
    overridden_decision = overridden.score(row["factors"], str(row["category"]))
    assert overridden_decision.action != action
    overridden_before = np.asarray(overridden._scorer.centroids).copy()
    overridden.learn(
        overridden_decision.decision_id,
        action,
        context={"benchmark": True},
        persist_artifacts=False,
    )
    override_movement = float(
        np.linalg.norm(np.asarray(overridden._scorer.centroids) - overridden_before)
    )

    assert override_movement > confirmed_movement


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
