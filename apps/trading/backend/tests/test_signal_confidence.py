from __future__ import annotations

import builtins
import importlib
import sys

from app.factors.registry import (
    ALL_FACTOR_NAMES,
    TRADING_FACTOR_COMPUTERS,
    compute_factors,
)
from app.factors.signal_confidence import SignalConfidenceFactor


def test_no_context_neutral():
    assert SignalConfidenceFactor().compute({}) == 0.5


def test_non_dict_neutral():
    assert SignalConfidenceFactor().compute(object()) == 0.5


def test_factor_coverage():
    assert round(SignalConfidenceFactor().compute({"factors_with_data": 4}), 4) == 0.4


def test_factor_coverage_clamped():
    assert SignalConfidenceFactor().compute({"factors_with_data": 10}) == 1.0


def test_category_accuracy():
    assert SignalConfidenceFactor().compute({"category_accuracy": 0.82}) == 0.82


def test_category_accuracy_clamped():
    assert SignalConfidenceFactor().compute({"category_accuracy": 2.0}) == 1.0


def test_sample_size():
    assert SignalConfidenceFactor().compute({"similar_trade_count": 40}) == 0.4


def test_sample_size_cap():
    assert SignalConfidenceFactor().compute({"similar_trade_count": 150}) == 1.0


def test_novelty_distance_low():
    assert SignalConfidenceFactor().compute({"novelty_distance": 0.2}) == 1.0


def test_novelty_distance_medium():
    assert SignalConfidenceFactor().compute({"novelty_distance": 0.5}) == 0.7


def test_novelty_distance_high():
    assert SignalConfidenceFactor().compute({"novelty_distance": 0.8}) == 0.4


def test_novelty_distance_very_high():
    assert SignalConfidenceFactor().compute({"novelty_distance": 1.2}) == 0.1


def test_combined_high():
    value = SignalConfidenceFactor().compute(
        {
            "factors_with_data": 10,
            "category_accuracy": 0.95,
            "similar_trade_count": 100,
            "novelty_distance": 0.2,
        }
    )

    assert value >= 0.98


def test_combined_low():
    value = SignalConfidenceFactor().compute(
        {
            "factors_with_data": 1,
            "category_accuracy": 0.2,
            "similar_trade_count": 5,
            "novelty_distance": 1.2,
        }
    )

    assert round(value, 4) == 0.1125


def test_output_bounded():
    value = SignalConfidenceFactor().compute(
        {"factors_with_data": 70, "category_accuracy": 10, "similar_trade_count": 1000}
    )

    assert 0.0 <= value <= 1.0


def test_no_more_default_missing_computers():
    assert set(TRADING_FACTOR_COMPUTERS.keys()) == set(ALL_FACTOR_NAMES)


def test_fallback_registry_uses_semantic_factor_mapping(monkeypatch):
    expected = {
        "signal_alignment": "SignalAlignmentFactor",
        "market_regime": "MarketRegimeFactor",
        "position_sizing": "PositionSizeFactor",
        "timing_quality": "TimingQualityFactor",
        "risk_reward_actual": "RiskRewardActualFactor",
        "emotional_indicator": "EmotionalIndicatorFactor",
        "signal_confidence": "SignalConfidenceFactor",
        "options_delta_exposure": "OptionsDeltaExposureFactor",
        "options_iv_percentile": "OptionsIVPercentileFactor",
        "options_gamma_risk": "OptionsGammaRiskFactor",
    }
    original_module = sys.modules.pop("app.factors.registry")
    real_import = builtins.__import__

    def force_preset_import_failure(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "copilot_sdk.scoring.presets.trading":
            raise ImportError("forced fallback")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", force_preset_import_failure)
    try:
        fallback_registry = importlib.import_module("app.factors.registry")

        assert fallback_registry.ALL_FACTOR_NAMES == tuple(expected)
        assert {
            name: type(computer).__name__
            for name, computer in fallback_registry.get_factor_registry().items()
        } == expected
    finally:
        sys.modules["app.factors.registry"] = original_module


def test_compute_factors_returns_all_10_keys():
    assert set(compute_factors({})) == set(ALL_FACTOR_NAMES)
    assert len(compute_factors({})) == 10


def test_compute_all_10_responds():
    values = compute_factors(
        {
            "tagged_signals": [{"confirmed": True}, {"confirmed": True}],
            "entry_direction": "long",
            "rsi_at_entry": 25,
            "macd_signal": "bullish",
            "price_vs_sma": 1.2,
            "position_size_pct": 2.0,
            "avg_position_size_pct": 2.0,
            "max_position_size_pct": 5.0,
            "entry_delay_minutes": 0,
            "hold_time_vs_plan_pct": 1.0,
            "planned_risk_reward": 2.0,
            "actual_risk_reward": 3.0,
            "minutes_since_last_trade": 999,
            "last_trade_was_loss": False,
            "consecutive_wins": 0,
            "entry_at_day_extreme": False,
            "vix_at_entry": 18,
            "trend_strength": 30,
            "regime_accuracy": {"trending": 0.9},
            "dk_weights_by_category": {0: [0.9, 0.8]},
            "tagged_signal_indices": [0, 1],
            "delta": 0.65,
            "iv_percentile": 72,
            "gamma": 0.04,
        }
    )

    assert all(values[name] != 0.5 for name in ALL_FACTOR_NAMES)


def test_unrelated_exception_still_defaults_factor_neutral(monkeypatch):
    class FailingFactor:
        def compute(self, event: object) -> float:
            raise RuntimeError("boom")

    monkeypatch.setitem(TRADING_FACTOR_COMPUTERS, "signal_confidence", FailingFactor())

    values = compute_factors({"factors_with_data": 10})

    assert values["signal_confidence"] == 0.5
    assert all(0.0 <= value <= 1.0 for value in values.values())


def test_signal_confidence_uses_dk_weights_for_tagged_signals():
    value = SignalConfidenceFactor().compute(
        {
            "category_index": 0,
            "dk_weights_by_category": {0: [0.2, 0.8, 1.0]},
            "tagged_signal_indices": [1, 2],
        }
    )

    assert value == 0.9
