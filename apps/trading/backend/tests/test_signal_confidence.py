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
    assert round(SignalConfidenceFactor().compute({"factors_with_data": 4}), 4) == 0.5714


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
            "factors_with_data": 7,
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

    assert round(value, 4) == 0.1232


def test_output_bounded():
    value = SignalConfidenceFactor().compute(
        {"factors_with_data": 70, "category_accuracy": 10, "similar_trade_count": 1000}
    )

    assert 0.0 <= value <= 1.0


def test_no_more_default_missing_computers():
    assert set(TRADING_FACTOR_COMPUTERS.keys()) == set(ALL_FACTOR_NAMES)


def test_fallback_registry_uses_semantic_factor_mapping(monkeypatch):
    expected = {
        "signal_alignment": "ConvictionFactor",
        "market_regime": "MarketRegimeFactor",
        "position_sizing": "PositionSizeFactor",
        "timing_quality": "TechnicalSignalFactor",
        "risk_reward_actual": "TimeHorizonFactor",
        "emotional_indicator": "ResearchDepthFactor",
        "signal_confidence": "SignalConfidenceFactor",
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


def test_compute_factors_returns_all_7_keys():
    assert set(compute_factors({})) == set(ALL_FACTOR_NAMES)
    assert len(compute_factors({})) == 7


def test_compute_all_7_responds():
    values = compute_factors(
        {
            "tagged_signals": [{"confirmed": True}, {"confirmed": True}],
            "has_trade_plan": True,
            "position_conviction": 0.9,
            "sources_consulted": 5,
            "analysis_minutes": 30,
            "has_thesis": True,
            "checklist_completed": 6,
            "checklist_total": 6,
            "entry_direction": "long",
            "rsi_at_entry": 25,
            "macd_signal": "bullish",
            "price_vs_sma": 1.2,
            "position_pct_of_max": 0.8,
            "portfolio_concentration": 0.05,
            "correlated_exposure": 0.05,
            "kelly_ratio": 1.0,
            "planned_hold_hours": 10,
            "actual_hold_hours": 10,
            "exit_reason": "target",
            "entry_hour": 11,
            "preferred_session": "morning",
            "vix_at_entry": 18,
            "trend_strength": 30,
            "regime_accuracy": {"trending": 0.9},
            "factors_with_data": 7,
            "category_accuracy": 0.95,
            "similar_trade_count": 100,
            "novelty_distance": 0.2,
        }
    )

    assert all(values[name] != 0.5 for name in ALL_FACTOR_NAMES)


def test_unrelated_exception_still_defaults_factor_neutral(monkeypatch):
    class FailingFactor:
        def compute(self, event: object) -> float:
            raise RuntimeError("boom")

    monkeypatch.setitem(TRADING_FACTOR_COMPUTERS, "signal_confidence", FailingFactor())

    values = compute_factors({"factors_with_data": 7})

    assert values["signal_confidence"] == 0.5
    assert all(0.0 <= value <= 1.0 for value in values.values())
