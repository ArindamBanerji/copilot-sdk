from __future__ import annotations

from app.factors import registry as registry_module
from app.factors.emotional_indicator import EmotionalIndicatorFactor
from app.factors.market_regime import MarketRegimeFactor, classify_regime
from app.factors.options_scored import (
    OptionsDeltaExposureFactor,
    OptionsGammaRiskFactor,
    OptionsIVPercentileFactor,
)
from app.factors.position_size import PositionSizeFactor
from app.factors.registry import (
    ALL_FACTOR_NAMES,
    TRADING_FACTOR_COMPUTERS,
    compute_factors,
)
from app.factors.risk_reward import RiskRewardActualFactor
from app.factors.signal_alignment import SignalAlignmentFactor
from app.factors.signal_confidence import SignalConfidenceFactor
from app.factors.timing_quality import TimingQualityFactor
from copilot_sdk.scoring.presets.trading import TradingPreset


def test_classify_high_vix_volatile():
    assert classify_regime(31) == "volatile"


def test_classify_medium_vix_ranging():
    assert classify_regime(25, trend_strength=40) == "ranging"


def test_classify_low_vix_strong_trend_trending():
    assert classify_regime(18, trend_strength=26) == "trending"


def test_classify_low_vix_weak_trend_ranging():
    assert classify_regime(18, trend_strength=20) == "ranging"


def test_boundary_cases():
    assert classify_regime(30, trend_strength=40) == "ranging"
    assert classify_regime(20, trend_strength=26) == "trending"
    assert classify_regime(20, trend_strength=25) == "ranging"


def test_no_context_neutral():
    assert MarketRegimeFactor().compute({}) == 0.5


def test_non_dict_neutral():
    assert MarketRegimeFactor().compute(object()) == 0.5


def test_current_regime_lookup():
    value = MarketRegimeFactor().compute(
        {"current_regime": "trending", "regime_accuracy": {"trending": 0.82}}
    )

    assert value == 0.82


def test_auto_classify():
    value = MarketRegimeFactor().compute(
        {
            "vix_at_entry": 18,
            "trend_strength": 30,
            "regime_accuracy": {"trending": 0.88},
        }
    )

    assert value == 0.88


def test_unknown_regime_neutral():
    value = MarketRegimeFactor().compute(
        {"current_regime": "unknown", "regime_accuracy": {"trending": 0.9}}
    )

    assert value == 0.5


def test_clamping():
    value = MarketRegimeFactor().compute(
        {"current_regime": "trending", "regime_accuracy": {"trending": 2.0}}
    )

    assert value == 1.0


def test_registry_compute_factors_returns_10_keys():
    assert len(compute_factors({})) == 10


def test_registry_all_preset_names_present():
    assert set(compute_factors({})) == set(TradingPreset().shape.factor_names)


def test_registry_factor_names_sourced_from_preset():
    assert ALL_FACTOR_NAMES == tuple(TradingPreset().shape.factor_names)


def test_fallback_factor_registry_mapping_is_semantic():
    expected = {
        "signal_alignment": SignalAlignmentFactor,
        "market_regime": MarketRegimeFactor,
        "position_sizing": PositionSizeFactor,
        "timing_quality": TimingQualityFactor,
        "risk_reward_actual": RiskRewardActualFactor,
        "emotional_indicator": EmotionalIndicatorFactor,
        "signal_confidence": SignalConfidenceFactor,
        "options_delta_exposure": OptionsDeltaExposureFactor,
        "options_iv_percentile": OptionsIVPercentileFactor,
        "options_gamma_risk": OptionsGammaRiskFactor,
    }

    assert {
        name: type(computer)
        for name, computer in registry_module._FALLBACK_FACTOR_COMPUTERS.items()
    } == expected


def test_registry_unimplemented_factors_neutral():
    values = compute_factors({})

    assert values["market_regime"] == 0.5
    assert values["timing_quality"] == 0.5
    assert values["risk_reward_actual"] == 0.5
    assert values["signal_confidence"] == 0.5


def test_registry_implemented_factors_respond_to_context():
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
        }
    )

    assert values["signal_alignment"] > 0.8
    assert values["market_regime"] == 0.9
    assert values["position_sizing"] > 0.8
    assert values["timing_quality"] > 0.8
    assert values["risk_reward_actual"] > 0.8
    assert values["emotional_indicator"] > 0.8
    assert values["signal_confidence"] > 0.8


def test_registry_all_values_bounded():
    values = compute_factors({"position_conviction": 50.0})

    assert all(0.0 <= value <= 1.0 for value in values.values())


def test_registry_result_usable_as_score_payload():
    values = compute_factors({})

    assert isinstance(values, dict)
    assert set(values) == set(TradingPreset().shape.factor_names)


def test_registry_exception_in_factor_defaults_neutral(monkeypatch):
    class FailingFactor:
        def compute(self, event: object) -> float:
            raise RuntimeError("boom")

    monkeypatch.setitem(TRADING_FACTOR_COMPUTERS, "signal_alignment", FailingFactor())

    assert compute_factors({"position_conviction": 0.9})["signal_alignment"] == 0.5
