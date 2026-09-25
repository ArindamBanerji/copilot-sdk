"""Measured production policy, not the A1-R2 experimental detector.

Seed 42: 75/1000 clean IID Bernoulli(0.85) streams trigger G-RATE (7.5%).
The 10% regression ceiling is NOT the unmet <2% target; reaching that target
requires a future gate-policy change. Each trial evaluates one 400-item window.
Recovery tests explicitly add independently verified outcomes to the store;
blocked outcomes alone cannot refresh the wrapper's verified baseline.
"""
from __future__ import annotations

import random
from collections.abc import Iterator
from typing import Any, cast

import pytest

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring import CompoundingScorer
from copilot_sdk.scoring.composite_gate import CompositeGate
from copilot_sdk.scoring.gate_enforced_scorer import GateEnforcedScorer
from copilot_sdk.scoring.presets.trading import TradingPreset


def evaluate(outcomes: list[bool], *, accuracy: float | None = None,
             signal: float = 100.0) -> dict[str, Any]:
    return cast(dict[str, Any], CompositeGate().evaluate(
        alpha_q_v=signal, theta_min=0.766, baseline=0.85,
        rolling_accuracy=(sum(outcomes) / len(outcomes) if outcomes else 0.0)
        if accuracy is None else accuracy,
        verified_outcomes=outcomes,
    ))


def healthy() -> list[bool]:
    return ([True] * 17 + [False] * 3) * 20


def degraded() -> list[bool]:
    return healthy() + [True, False] * 10


def test_grate_detects_20_decision_drop() -> None:
    result = evaluate(degraded())
    assert result["g_rate"]["active"] is True
    assert result["g_rate"]["short_accuracy"] == 0.5
    assert result["g_rate"]["long_baseline"] == pytest.approx(0.8325)


def test_grate_does_not_fire_on_normal_variation() -> None:
    for correct in (16, 17, 18):
        result = evaluate(healthy() + [True] * correct + [False] * (20 - correct))
        assert result["status"] == "GREEN"


def test_grate_false_positive_rate() -> None:
    rng = random.Random(42)
    triggers = sum(evaluate([rng.random() < 0.85 for _ in range(400)])
                   ["g_rate"]["active"] for _ in range(1000))
    assert triggers / 1000 <= 0.10, f"production FPR={triggers / 1000:.1%}"


def test_grel_detects_sustained_drift() -> None:
    # G-REL compares caller-supplied rolling accuracy to its independent baseline.
    result = evaluate([True] * 25 + [False] * 25, accuracy=0.85 * 0.60)
    assert result["g_rel"]["active"] is True
    # A 50-outcome drop appended to 400 healthy outcomes is diluted instead.
    diluted = evaluate(healthy() + [True, False] * 25)
    assert diluted["g_rel"]["active"] is False


def test_grel_tolerates_minor_drop() -> None:
    result = evaluate(healthy(), accuracy=0.85 * 0.75)
    assert result["g_rel"]["active"] is False
    assert result["status"] == "GREEN"


def test_gabs_zero_outcomes_allows_cold_start() -> None:
    result = evaluate([], signal=0.0)
    assert result["g_abs"]["active"] is False
    assert result["status"] == "GREEN"


def test_gabs_passes_after_threshold() -> None:
    assert evaluate([True], signal=0.765)["g_abs"]["active"] is True
    assert evaluate([True], signal=0.766)["g_abs"]["active"] is False


def test_combined_gate_worst_layer_wins() -> None:
    result = evaluate(degraded())
    assert result["g_abs"]["active"] is False
    assert result["g_rel"]["active"] is False
    assert result["g_rate"]["active"] is True
    assert result["status"] == "AMBER"


def seed_verified(store: InMemoryGraphStore, outcomes: list[bool]) -> None:
    preset = TradingPreset()
    # Populate the actual persisted verified stream, without mocking the scorer
    # or bypassing learn() during the enforcement/replay assertions below.
    for index, correct in enumerate(outcomes):
        decision_id = store.write_decision(
            domain="trading", category=preset.shape.category_names[index % 5],
            action=preset.shape.action_names[0], confidence=0.85,
            factors={name: 0.8 for name in preset.shape.factor_names},
        )
        store.write_outcome(
            decision_id, preset.shape.action_names[0 if correct else 1], correct, domain="trading"
        )


@pytest.fixture
def scorer_pair() -> Iterator[tuple[CompoundingScorer, GateEnforcedScorer]]:
    store = InMemoryGraphStore(domain="trading")
    scorer = CompoundingScorer.from_preset(
        "trading", graph_store=store, profile="test", enable_rl=False,
    )
    seed_verified(store, degraded())
    try:
        yield scorer, GateEnforcedScorer(scorer, CompositeGate())
    finally:
        store.close()


def test_gate_enforced_scorer_blocks_on_grate(
    scorer_pair: tuple[CompoundingScorer, GateEnforcedScorer],
) -> None:
    scorer, wrapper = scorer_pair
    score = scorer.score({}, "trend_following")
    count = scorer.graph_store.count_verified("trading")
    result = wrapper.learn(score.decision_id, score.action)
    assert result["blocked_by_gate"] is True
    assert result["gate_status"]["g_rate"]["active"] is True
    assert scorer.graph_store.count_verified("trading") == count


def test_gate_recovery_replays_buffer(
    scorer_pair: tuple[CompoundingScorer, GateEnforcedScorer],
) -> None:
    scorer, wrapper = scorer_pair
    first = scorer.score({}, "trend_following")
    second = scorer.score({}, "mean_reversion")
    assert wrapper.learn(first.decision_id, first.action)["buffered_outcomes"] == 1
    seed_verified(scorer.graph_store, [True] * 20)
    before = scorer.graph_store.count_verified("trading")
    wrapper.learn(second.decision_id, second.action)
    assert scorer.graph_store.count_verified("trading") == before + 2
    assert len(wrapper._outcome_buffer) == 0
