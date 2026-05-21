from __future__ import annotations

import numpy as np

from copilot_sdk.scoring import CompoundingScorer
from copilot_sdk.scoring.presets.trading import TradingPreset


EXISTING_CATEGORIES = (
    "equity_long",
    "equity_short",
    "crypto_spot",
    "options",
    "etf",
)
EXISTING_ACTIONS = ("buy", "hold", "sell")
EXISTING_FACTORS = (
    "conviction",
    "research_depth",
    "technical_signal",
    "position_size",
    "time_horizon",
    "market_regime",
)


def test_tensor_shape():
    assert TradingPreset().shape.tensor_shape == (5, 4, 7)


def test_category_count():
    assert TradingPreset().shape.n_categories == 5


def test_action_count():
    assert TradingPreset().shape.n_actions == 4


def test_factor_count():
    assert TradingPreset().shape.n_factors == 7


def test_skip_recommended_is_action_3():
    assert TradingPreset().shape.action_names[3] == "skip_recommended"


def test_signal_confidence_is_factor_6():
    assert TradingPreset().shape.factor_names[6] == "signal_confidence"


def test_existing_categories_preserved():
    assert TradingPreset().shape.category_names[:5] == EXISTING_CATEGORIES


def test_existing_actions_preserved():
    assert TradingPreset().shape.action_names[:3] == EXISTING_ACTIONS


def test_existing_factors_preserved():
    assert TradingPreset().shape.factor_names[:6] == EXISTING_FACTORS


def test_penalty_ratio():
    assert TradingPreset().penalty_ratio == 3.0


def test_eta_confirm():
    assert TradingPreset().eta_confirm == 0.05


def test_eta_override():
    assert TradingPreset().eta_override == 0.01


def test_tau():
    assert TradingPreset().temperature == 0.1


def test_q_window():
    assert TradingPreset().q_window == 400


def test_centroids_have_20_cells():
    centroids = TradingPreset().bootstrap_centroids

    assert centroids.shape[:2] == (5, 4)
    assert centroids.shape[0] * centroids.shape[1] == 20


def test_all_centroids_are_7_dimensional():
    assert TradingPreset().bootstrap_centroids.shape[2] == 7


def test_all_centroid_values_bounded():
    centroids = TradingPreset().bootstrap_centroids

    assert np.all(centroids >= 0.0)
    assert np.all(centroids <= 1.0)


def test_skip_centroids_have_low_emotional():
    skip_centroids = TradingPreset().bootstrap_centroids[:, 3, :]

    assert np.all(skip_centroids[:, 0] <= 0.30)
    assert np.all(skip_centroids[:, 5] <= 0.25)
    assert np.all(skip_centroids[:, 6] <= 0.40)


def test_new_factor_initialized_in_existing_cells():
    centroids = TradingPreset().bootstrap_centroids

    np.testing.assert_allclose(centroids[:, 0, 6], 0.65)
    np.testing.assert_allclose(centroids[:, 1, 6], 0.55)
    np.testing.assert_allclose(centroids[:, 2, 6], 0.50)


def test_scorer_can_initialize_with_trading_config(tmp_path):
    scorer = CompoundingScorer.from_preset("trading", db_path=str(tmp_path / "trading.db"))

    try:
        assert scorer.gae_scorer.centroids.shape == (5, 4, 7)
    finally:
        scorer._store.close()


def test_iks_endpoint_or_iks_config_available(client):
    response = client.get("/api/trajectory")

    assert response.status_code == 200
    payload = response.json()
    assert "current_iks" in payload
    assert isinstance(payload["current_iks"], (int, float))
