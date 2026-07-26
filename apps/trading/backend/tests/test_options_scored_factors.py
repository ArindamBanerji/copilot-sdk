from __future__ import annotations

import numpy as np

from app.factors.options_scored import (
    OptionsDeltaExposureFactor,
    OptionsGammaRiskFactor,
    OptionsIVPercentileFactor,
)
from app.factors.registry import ALL_FACTOR_NAMES, compute_factors
from copilot_sdk.scoring import CompoundingScorer
from copilot_sdk.scoring.presets.dataops import DataOpsPreset
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset
from copilot_sdk.scoring.presets.trading import TradingPreset


OPTIONS_FACTOR_NAMES = (
    "options_delta_exposure",
    "options_iv_percentile",
    "options_gamma_risk",
)


def test_scored_options_factor_metadata():
    assert OptionsDeltaExposureFactor.factor_name == "options_delta_exposure"
    assert OptionsDeltaExposureFactor.factor_index == 7
    assert OptionsIVPercentileFactor.factor_name == "options_iv_percentile"
    assert OptionsIVPercentileFactor.factor_index == 8
    assert OptionsGammaRiskFactor.factor_name == "options_gamma_risk"
    assert OptionsGammaRiskFactor.factor_index == 9


def test_delta_exposure_handles_zero_positive_negative_clamp_and_missing():
    factor = OptionsDeltaExposureFactor()

    assert factor.compute({"delta": 0}) == 0.0
    assert factor.compute({"delta": 0.4}) == 0.4
    assert factor.compute({"delta": -0.4}) == 0.4
    assert factor.compute({"delta": 2.0}) == 1.0
    assert factor.compute({}) == 0.5


def test_delta_exposure_reads_metadata_and_options_context():
    factor = OptionsDeltaExposureFactor()

    assert factor.compute({"metadata": {"options_delta": 0.25}}) == 0.25
    assert factor.compute({"options": {"net_delta": -0.75}}) == 0.75


def test_iv_percentile_handles_fraction_percent_clamp_and_missing():
    factor = OptionsIVPercentileFactor()

    assert factor.compute({"iv_percentile": 0}) == 0.0
    assert factor.compute({"iv_percentile": 0.73}) == 0.73
    assert factor.compute({"iv_percentile": 73}) == 0.73
    assert factor.compute({"iv_percentile": 150}) == 1.0
    assert factor.compute({}) == 0.5


def test_iv_percentile_reads_rank_aliases():
    factor = OptionsIVPercentileFactor()

    assert factor.compute({"metadata": {"iv_rank": 55}}) == 0.55
    assert factor.compute({"options": {"implied_volatility_percentile": 0.45}}) == 0.45


def test_gamma_risk_handles_positive_negative_clamp_and_missing():
    factor = OptionsGammaRiskFactor()

    assert factor.compute({"gamma": 0}) == 0.0
    assert factor.compute({"gamma": 0.04}) == 0.4
    assert factor.compute({"gamma": -0.04}) == 0.4
    assert factor.compute({"gamma": 0.2}) == 1.0
    assert factor.compute({}) == 0.5


def test_gamma_risk_reads_metadata_and_options_context():
    factor = OptionsGammaRiskFactor()

    assert factor.compute({"metadata": {"options_gamma": 0.03}}) == 0.3
    assert factor.compute({"options": {"net_gamma": -0.08}}) == 0.8


def test_scored_options_outputs_are_bounded_floats():
    factors = (
        OptionsDeltaExposureFactor(),
        OptionsIVPercentileFactor(),
        OptionsGammaRiskFactor(),
    )
    context = {"delta": 10, "iv_percentile": 999, "gamma": 10}

    for factor in factors:
        value = factor.compute(context)
        assert isinstance(value, float)
        assert 0.0 <= value <= 1.0


def test_registry_has_10_factors_and_new_names_present():
    assert len(ALL_FACTOR_NAMES) == 10
    assert ALL_FACTOR_NAMES[:7] == (
        "signal_alignment",
        "market_regime",
        "position_sizing",
        "timing_quality",
        "risk_reward_actual",
        "emotional_indicator",
        "signal_confidence",
    )
    assert ALL_FACTOR_NAMES[7:10] == OPTIONS_FACTOR_NAMES


def test_compute_factors_returns_10_values_with_scored_options():
    values = compute_factors({"delta": -0.6, "iv_percentile": 80, "gamma": 0.05})

    assert set(values) == set(ALL_FACTOR_NAMES)
    assert len(values) == 10
    assert values["options_delta_exposure"] == 0.6
    assert values["options_iv_percentile"] == 0.8
    assert values["options_gamma_risk"] == 0.5


def test_trading_preset_shape_and_factor_order():
    preset = TradingPreset()

    assert preset.shape.tensor_shape == (5, 4, 10)
    assert len(preset.shape.factor_names) == 10
    assert preset.shape.factor_names[7:10] == OPTIONS_FACTOR_NAMES


def test_bootstrap_shape_and_neutral_options_columns():
    centroids = TradingPreset().bootstrap_centroids

    assert centroids.shape == (5, 4, 10)
    np.testing.assert_allclose(centroids[:, :, 7:], 0.5)


def test_non_trading_shapes_unchanged():
    purchasing = PurchasingPreset().shape
    dataops = DataOpsPreset().shape

    assert (purchasing.n_categories, purchasing.n_actions, purchasing.n_factors) == (5, 4, 7)
    assert (dataops.n_categories, dataops.n_actions, dataops.n_factors) == (6, 5, 6)


def test_scorer_accepts_10_factor_dict(tmp_path):
    scorer = CompoundingScorer.from_preset("trading", db_path=str(tmp_path / "trading.db"), profile="test")
    try:
        result = scorer.score(
            {name: 0.5 for name in TradingPreset().shape.factor_names},
            "trend_following",
        )
    finally:
        scorer.graph_store.close()

    assert result.category == "trend_following"


def test_legacy_7_factor_dict_is_padded_by_scorer(tmp_path):
    preset = TradingPreset()
    old_factor_names = preset.shape.factor_names[:7]
    scorer = CompoundingScorer.from_preset("trading", db_path=str(tmp_path / "trading.db"), profile="test")
    try:
        result = scorer.score({name: 0.5 for name in old_factor_names}, "trend_following")
    finally:
        scorer.graph_store.close()

    assert set(result.factors) == set(preset.shape.factor_names)
    assert result.factors["options_delta_exposure"] == 0.5
    assert result.factors["options_iv_percentile"] == 0.5
    assert result.factors["options_gamma_risk"] == 0.5
