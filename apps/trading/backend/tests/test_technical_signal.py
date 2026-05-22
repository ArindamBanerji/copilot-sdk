from __future__ import annotations

from app.factors.technical_signal import TechnicalSignalFactor


def test_no_context_returns_neutral():
    assert TechnicalSignalFactor().compute({}) == 0.5


def test_non_dict_returns_neutral():
    assert TechnicalSignalFactor().compute(object()) == 0.5


def test_all_signals_confirmed():
    assert TechnicalSignalFactor().compute(
        {"tagged_signals": [{"confirmed": True}, {"confirmed": True}]}
    ) == 1.0


def test_no_signals_confirmed():
    assert TechnicalSignalFactor().compute(
        {"tagged_signals": [{"confirmed": False}, {"confirmed": False}]}
    ) == 0.0


def test_rsi_long_cases():
    factor = TechnicalSignalFactor()

    assert factor.compute({"entry_direction": "long", "rsi_at_entry": 25}) == 0.9
    assert factor.compute({"entry_direction": "long", "rsi_at_entry": 45}) == 0.7
    assert factor.compute({"entry_direction": "long", "rsi_at_entry": 65}) == 0.5
    assert factor.compute({"entry_direction": "long", "rsi_at_entry": 75}) == 0.2


def test_rsi_short_cases():
    factor = TechnicalSignalFactor()

    assert factor.compute({"entry_direction": "short", "rsi_at_entry": 75}) == 0.9
    assert factor.compute({"entry_direction": "short", "rsi_at_entry": 55}) == 0.7
    assert factor.compute({"entry_direction": "short", "rsi_at_entry": 45}) == 0.5
    assert factor.compute({"entry_direction": "short", "rsi_at_entry": 20}) == 0.2


def test_macd_aligned_conflicting_neutral():
    factor = TechnicalSignalFactor()

    assert factor.compute({"entry_direction": "long", "macd_signal": "bullish"}) == 1.0
    assert factor.compute({"entry_direction": "long", "macd_signal": "bearish"}) == 0.1
    assert factor.compute({"entry_direction": "long", "macd_signal": "neutral"}) == 0.5
    assert factor.compute({"entry_direction": "short", "macd_signal": "bearish"}) == 1.0


def test_price_vs_sma_long_cases():
    factor = TechnicalSignalFactor()

    assert round(factor.compute({"entry_direction": "long", "price_vs_sma": 1.2}), 4) == 1.0
    assert round(factor.compute({"entry_direction": "long", "price_vs_sma": 0.8}), 4) == 0.6667


def test_all_bullish_long_high():
    value = TechnicalSignalFactor().compute(
        {
            "entry_direction": "long",
            "tagged_signals": [{"confirmed": True}, {"confirmed": True}],
            "rsi_at_entry": 25,
            "macd_signal": "bullish",
            "price_vs_sma": 1.2,
        }
    )

    assert value >= 0.95


def test_all_bearish_long_low():
    value = TechnicalSignalFactor().compute(
        {
            "entry_direction": "long",
            "tagged_signals": [{"confirmed": False}, {"confirmed": False}],
            "rsi_at_entry": 75,
            "macd_signal": "bearish",
            "price_vs_sma": 0.8,
        }
    )

    assert value < 0.30


def test_result_bounded():
    value = TechnicalSignalFactor().compute(
        {"entry_direction": "long", "price_vs_sma": 10.0, "rsi_at_entry": -100.0}
    )

    assert 0.0 <= value <= 1.0
