from __future__ import annotations

from copilot_sdk.evolution import AutonomousPromotionGate, PromotionDecision


def _batches(count: int = 3, *, accuracy: float = 0.8, baseline: float = 0.7):
    return [
        {"accuracy": accuracy, "baseline_accuracy": baseline, "win": accuracy >= baseline}
        for _ in range(count)
    ]


def test_green_with_criteria_promotes():
    decision = AutonomousPromotionGate().evaluate(
        {"variant_id": "v1", "win_rate": 0.75},
        "GREEN",
        _batches(),
    )

    assert decision.action == PromotionDecision.PROMOTE
    assert decision.reason == "criteria_met"


def test_amber_blocks():
    decision = AutonomousPromotionGate().evaluate({"variant_id": "v1", "win_rate": 1.0}, "AMBER", _batches())

    assert decision.action == PromotionDecision.BLOCK
    assert decision.reason == "conservation"


def test_red_blocks():
    decision = AutonomousPromotionGate().evaluate({"variant_id": "v1", "win_rate": 1.0}, "RED", _batches())

    assert decision.action == PromotionDecision.BLOCK


def test_unknown_blocks():
    decision = AutonomousPromotionGate().evaluate({"variant_id": "v1", "win_rate": 1.0}, "UNKNOWN", _batches())

    assert decision.action == PromotionDecision.BLOCK


def test_insufficient_batches_continue():
    decision = AutonomousPromotionGate(min_shadow_batches=3).evaluate(
        {"variant_id": "v1", "win_rate": 1.0},
        "GREEN",
        _batches(count=2),
    )

    assert decision.action == PromotionDecision.CONTINUE
    assert decision.reason == "insufficient_shadow_batches"


def test_low_win_rate_continue():
    decision = AutonomousPromotionGate(min_win_rate=0.8).evaluate(
        {"variant_id": "v1", "win_rate": 0.7},
        "GREEN",
        [{"samples": 10}, {"samples": 12}, {"samples": 14}],
    )

    assert decision.action == PromotionDecision.CONTINUE
    assert decision.reason == "win_rate"


def test_shadow_losses_override_stale_variant_win_rate():
    decision = AutonomousPromotionGate(min_shadow_batches=3, min_win_rate=0.7).evaluate(
        {"variant_id": "v1", "win_rate": 1.0},
        "GREEN",
        [{"win": False}, {"win": False}, {"win": False}],
    )

    assert decision.action == PromotionDecision.CONTINUE
    assert decision.reason == "win_rate"
    assert decision.evidence["win_rate"] == 0.0


def test_shadow_better_losses_override_stale_variant_win_rate():
    decision = AutonomousPromotionGate(min_shadow_batches=3, min_win_rate=0.7).evaluate(
        {"variant_id": "v1", "win_rate": 1.0},
        "GREEN",
        [{"better": False}, {"better": False}, {"better": True}],
    )

    assert decision.action == PromotionDecision.CONTINUE
    assert decision.reason == "win_rate"
    assert decision.evidence["win_rate"] == 1 / 3


def test_variant_win_rate_fallback_when_shadow_has_no_win_evidence():
    decision = AutonomousPromotionGate(min_shadow_batches=3, min_win_rate=0.7).evaluate(
        {"variant_id": "v1", "win_rate": 0.8},
        "GREEN",
        [{"samples": 10}, {"samples": 12}, {"samples": 14}],
    )

    assert decision.action == PromotionDecision.PROMOTE
    assert decision.evidence["win_rate"] == 0.8


def test_regression_continue():
    decision = AutonomousPromotionGate().evaluate(
        {"variant_id": "v1", "win_rate": 1.0},
        "GREEN",
        _batches(count=2) + [{"accuracy": 0.6, "baseline_accuracy": 0.7}],
    )

    assert decision.action == PromotionDecision.CONTINUE
    assert decision.reason == "regression"


def test_promote_decision_has_evidence():
    decision = AutonomousPromotionGate().evaluate(
        {"variant_id": "v1", "win_rate": 0.75},
        "GREEN",
        _batches(),
    )

    assert decision.evidence["variant_id"] == "v1"
    assert decision.evidence["win_rate"] == 1.0
    assert decision.evidence["shadow_batches"] == 3
