import time

import numpy as np

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer


def _phase_name(scorer: CompoundingScorer, category_index: int) -> str:
    phase = scorer._scorer._category_states[category_index].phase
    return str(getattr(phase, "name", phase))


def _make_trading_scorer() -> tuple[CompoundingScorer, InMemoryGraphStore, str, int]:
    store = InMemoryGraphStore(domain="trading")
    scorer = CompoundingScorer.from_preset(
        "trading",
        graph_store=store,
        enable_rl=False,
        profile="test",
    )
    category = "trend_following"
    category_index = scorer._preset.shape.category_names.index(category)

    centroids = scorer._scorer.centroids.copy()
    centroids[category_index, :, :] = 0.5
    centroids[category_index, 0, 0] = 1.0
    centroids[category_index, 0, 1] = 0.0
    centroids[category_index, 1, 0] = 0.0
    centroids[category_index, 1, 1] = 1.0
    scorer._scorer.centroids = centroids
    return scorer, store, category, category_index


def _write_verified_decision(
    scorer: CompoundingScorer,
    store: InMemoryGraphStore,
    *,
    category: str,
    category_index: int,
    vector: np.ndarray,
    action_index: int,
    decision_id: str,
) -> None:
    factor_names = list(scorer._preset.shape.factor_names)
    action = scorer._preset.shape.action_names[action_index]
    factors = {name: float(vector[index]) for index, name in enumerate(factor_names)}
    stored_id = store.write_decision(
        "trading",
        category=category,
        action=action,
        confidence=1.0,
        factors=factors,
        metadata={
            "decision_id": decision_id,
            "category_index": category_index,
            "factor_vector": vector.astype(float).tolist(),
            "recommended_index": action_index,
            "probabilities": [1.0, 0.0, 0.0, 0.0],
            "created_at": time.time(),
        },
    )
    scorer.learn(stored_id, action)


def _advance_to_variance_learning(
    scorer: CompoundingScorer,
    store: InMemoryGraphStore,
    *,
    category: str,
    category_index: int,
) -> None:
    n_factors = len(scorer._preset.shape.factor_names)
    warm_vector = np.array([1.0, 0.0] + [0.5] * (n_factors - 2), dtype=np.float64)
    for index in range(200):
        _write_verified_decision(
            scorer,
            store,
            category=category,
            category_index=category_index,
            vector=warm_vector,
            action_index=0,
            decision_id=f"warm-{index}",
        )


def _buffer_signal_and_noise_decisions(
    scorer: CompoundingScorer,
    store: InMemoryGraphStore,
    *,
    category: str,
    category_index: int,
) -> None:
    n_factors = len(scorer._preset.shape.factor_names)
    for index in range(60):
        if index % 2 == 0:
            vector = np.array([1.0, 1.0] + [0.5] * (n_factors - 2), dtype=np.float64)
            action_index = 0
        else:
            vector = np.array([0.0, 0.0] + [0.5] * (n_factors - 2), dtype=np.float64)
            action_index = 1
        _write_verified_decision(
            scorer,
            store,
            category=category,
            category_index=category_index,
            vector=vector,
            action_index=action_index,
            decision_id=f"variance-{index}",
        )


def _train_runtime_dk() -> tuple[CompoundingScorer, str, int]:
    scorer, store, category, category_index = _make_trading_scorer()
    _advance_to_variance_learning(
        scorer,
        store,
        category=category,
        category_index=category_index,
    )
    _buffer_signal_and_noise_decisions(
        scorer,
        store,
        category=category,
        category_index=category_index,
    )
    return scorer, category, category_index


def _probe_factors(scorer: CompoundingScorer) -> dict[str, float]:
    factors = {name: 0.5 for name in scorer._preset.shape.factor_names}
    factors["signal_alignment"] = 0.9
    factors["market_regime"] = 0.1
    return factors


def _softmax_from_effective_weights(
    scorer: CompoundingScorer,
    *,
    category_index: int,
    factors: dict[str, float],
    effective_weights: np.ndarray,
) -> np.ndarray:
    vector = np.asarray(
        [factors[name] for name in scorer._preset.shape.factor_names],
        dtype=np.float64,
    )
    centroids = scorer._scorer.centroids[category_index]
    distances = np.sum(effective_weights * (vector - centroids) ** 2, axis=1)
    logits = -distances / float(scorer._scorer.tau)
    logits -= np.max(logits)
    exp_logits = np.exp(logits)
    return exp_logits / exp_logits.sum()


def test_dk_reestimate_early_return() -> None:
    scorer, _store, _category, _category_index = _make_trading_scorer()

    assert scorer.get_dk_weights() is None
    assert scorer.reestimate_dk_if_due() is False
    assert scorer.get_dk_weights() is None


def test_dk_phase_transition() -> None:
    scorer, store, category, category_index = _make_trading_scorer()
    assert _phase_name(scorer, category_index) == "MEAN_CONVERGENCE"

    n_factors = len(scorer._preset.shape.factor_names)
    warm_vector = np.array([1.0, 0.0] + [0.5] * (n_factors - 2), dtype=np.float64)
    for index in range(199):
        _write_verified_decision(
            scorer,
            store,
            category=category,
            category_index=category_index,
            vector=warm_vector,
            action_index=0,
            decision_id=f"phase-{index}",
        )
    assert _phase_name(scorer, category_index) == "MEAN_CONVERGENCE"
    assert scorer.get_dk_weights() is None

    _write_verified_decision(
        scorer,
        store,
        category=category,
        category_index=category_index,
        vector=warm_vector,
        action_index=0,
        decision_id="phase-199",
    )

    assert _phase_name(scorer, category_index) == "VARIANCE_LEARNING"
    assert scorer.get_verified_count() == 200
    assert scorer.get_dk_weights() is None


def test_dk_learning_actually_works() -> None:
    scorer, category, category_index = _train_runtime_dk()
    probe = _probe_factors(scorer)
    probabilities_before = scorer.score_read_only(probe, category).probabilities

    assert scorer.reestimate_dk_if_due() is True
    weights = np.asarray(scorer.get_dk_weights(), dtype=np.float64)

    assert weights.shape == (
        scorer._preset.shape.n_categories,
        scorer._preset.shape.n_factors,
    )
    signal_weight = weights[category_index, 0]
    noisy_weight = weights[category_index, 1]
    assert signal_weight > noisy_weight
    assert signal_weight > 1.0

    probabilities_after = scorer.score_read_only(probe, category).probabilities
    probability_shift = np.max(
        np.abs(np.asarray(probabilities_after) - np.asarray(probabilities_before))
    )
    assert probability_shift > 0.01


def test_dk_shrinkage_via_fixed_alpha() -> None:
    scorer, category, category_index = _train_runtime_dk()
    assert scorer.reestimate_dk_if_due() is True

    weights = np.asarray(scorer.get_dk_weights(), dtype=np.float64)
    strategy = scorer._scorer._learning_strategy
    assert strategy.shrinkage_schedule.alpha == 0.5
    alpha = strategy.shrinkage_schedule.compute_alpha(
        scorer._scorer._category_states[category_index]
    )
    assert alpha == 0.5

    probe = _probe_factors(scorer)
    observed = np.asarray(scorer.score_read_only(probe, category).probabilities)
    shrunk_weights = alpha * weights[category_index] + (1.0 - alpha)
    raw_weights = weights[category_index]

    expected_shrunk = _softmax_from_effective_weights(
        scorer,
        category_index=category_index,
        factors=probe,
        effective_weights=shrunk_weights,
    )
    expected_raw = _softmax_from_effective_weights(
        scorer,
        category_index=category_index,
        factors=probe,
        effective_weights=raw_weights,
    )

    np.testing.assert_allclose(observed, expected_shrunk, rtol=1e-12, atol=1e-12)
    assert np.max(np.abs(expected_raw - expected_shrunk)) > 0.01


def test_from_preset_enables_learning_strategy_for_all_sdk_presets() -> None:
    for domain in ("trading", "purchasing", "dataops", "s2p"):
        scorer = CompoundingScorer.from_preset(
            domain,
            graph_store=InMemoryGraphStore(domain=domain),
            enable_rl=False,
            profile="test",
        )
        strategy = scorer._scorer._learning_strategy
        assert strategy is not None
        assert strategy.phase_policy.n == 200
        assert strategy.shrinkage_schedule.alpha == 0.5
        assert scorer._scorer.eta_override == 0.01
        assert scorer._scorer.auto_pause_on_amber is True
