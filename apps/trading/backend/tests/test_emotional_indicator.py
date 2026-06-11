from __future__ import annotations

from app.factors.emotional_indicator import EmotionalIndicatorFactor


def test_no_context_neutral():
    assert EmotionalIndicatorFactor().compute({}) == 0.5


def test_revenge_pattern_penalty():
    assert EmotionalIndicatorFactor().compute(
        {"minutes_since_last_trade": 12, "last_trade_was_loss": True}
    ) == 0.6


def test_overconfidence_penalty():
    assert EmotionalIndicatorFactor().compute(
        {"consecutive_wins": 3, "size_vs_rolling_avg": 1.4}
    ) == 0.7


def test_day_extreme_penalty():
    assert EmotionalIndicatorFactor().compute({"entry_at_day_extreme": True}) == 0.8


def test_combined_flags_bounded():
    value = EmotionalIndicatorFactor().compute(
        {
            "minutes_since_last_trade": 5,
            "last_trade_was_loss": True,
            "consecutive_wins": 4,
            "size_vs_rolling_avg": 2.0,
            "entry_at_day_extreme": True,
        }
    )

    assert round(value, 4) == 0.1
    assert 0.0 <= value <= 1.0
