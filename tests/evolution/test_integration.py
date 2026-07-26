from __future__ import annotations

from copilot_sdk.evolution import (
    AutonomousPromotionGate,
    ContextAwareSelector,
    PromotionDecision,
    SelectionContext,
    StepCreditAssigner,
    StepRecord,
)
from copilot_sdk.scoring.scorer import CompoundingScorer


def test_selector_and_credit_compose():
    selector = ContextAwareSelector(exploration_bonus=0.5)
    selected = selector.select(
        [
            {"variant_id": "stable", "win_rate": 0.8, "decision_count": 100},
            {"variant_id": "new", "win_rate": 0.5, "decision_count": 0},
        ],
        SelectionContext("payments", 0.6, "A", 2),
    )
    credits = StepCreditAssigner().assign(
        [
            StepRecord("score", "score", 100.0),
            StepRecord("verify", "outcome", 130.0),
        ],
        1.0,
    )

    assert selected["variant_id"] == "new"
    assert credits[1].credit > credits[0].credit


def test_promotion_respects_conservation():
    gate = AutonomousPromotionGate()

    decision = gate.evaluate({"variant_id": "v1", "win_rate": 1.0}, "RED", [{"win": True}] * 3)

    assert decision.action == PromotionDecision.BLOCK


def test_new_components_importable():
    assert ContextAwareSelector
    assert StepCreditAssigner
    assert AutonomousPromotionGate
    assert PromotionDecision.PROMOTE == "promote"


def test_compounding_scorer_default_path_without_evolution_config(tmp_path):
    scorer = CompoundingScorer.from_preset("trading", db_path=str(tmp_path / "trading.db"), profile="test")
    factors = {
        "signal_alignment": 0.5,
        "market_regime": 0.5,
        "position_sizing": 0.5,
        "timing_quality": 0.5,
        "risk_reward_actual": 0.5,
        "emotional_indicator": 0.5,
    }

    result = scorer.score(factors, "trend_following")

    assert result.action
    assert 0.0 <= result.confidence <= 1.0
    assert getattr(scorer, "_evolve") is False
