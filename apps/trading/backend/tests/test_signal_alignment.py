from __future__ import annotations

from app.factors.signal_alignment import SignalAlignmentFactor


def test_no_context_neutral():
    assert SignalAlignmentFactor().compute({}) == 0.5


def test_tagged_signal_confirmation_ratio():
    assert SignalAlignmentFactor().compute(
        {"tagged_signals": [{"confirmed": True}, {"confirmed": False}]}
    ) == 0.5


def test_technical_indicator_alignment_included():
    value = SignalAlignmentFactor().compute(
        {
            "entry_direction": "long",
            "tagged_signals": [{"confirmed": True}, {"confirmed": True}],
            "rsi_at_entry": 25,
            "macd_signal": "bullish",
            "price_vs_sma": 1.2,
        }
    )

    assert value >= 0.95
