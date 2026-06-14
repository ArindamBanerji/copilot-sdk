from __future__ import annotations

import numpy as np

from copilot_sdk.scoring import CompoundingScorer
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset


EXISTING_CATEGORIES = (
    "protein",
    "produce",
    "dairy",
    "dry_goods",
    "beverages",
)
EXISTING_ACTIONS = (
    "order_as_planned",
    "order_more",
    "order_less",
    "skip",
)
EXISTING_FACTORS = (
    "expected_demand",
    "day_of_week",
    "weather_forecast",
    "event_flag",
    "historical_waste",
    "supplier_lead_time",
)
SAMPLE_LEGACY_CELLS = {
    (0, 0): np.array(
        [
            0.585981273438,
            0.640465147547,
            0.319309769444,
            0.317610757091,
            0.378724732442,
            0.567707629480,
        ],
        dtype=np.float64,
    ),
    (1, 2): np.array(
        [
            0.371290181709,
            0.661621106052,
            0.447348694256,
            0.594123220687,
            0.526905901147,
            0.529550364412,
        ],
        dtype=np.float64,
    ),
    (4, 3): np.array(
        [
            0.419968863401,
            0.372297595422,
            0.604489111532,
            0.378233052655,
            0.490980879414,
            0.312981559967,
        ],
        dtype=np.float64,
    ),
}


def test_tensor_shape():
    assert PurchasingPreset().shape.tensor_shape == (5, 4, 7)


def test_category_count_unchanged():
    assert PurchasingPreset().shape.n_categories == 5


def test_action_count_unchanged():
    assert PurchasingPreset().shape.n_actions == 4


def test_factor_count_expanded():
    assert PurchasingPreset().shape.n_factors == 7


def test_price_memory_index_is_factor_6():
    assert PurchasingPreset().shape.factor_names[6] == "price_memory_index"


def test_existing_categories_preserved():
    assert PurchasingPreset().shape.category_names == EXISTING_CATEGORIES


def test_existing_actions_preserved():
    assert PurchasingPreset().shape.action_names == EXISTING_ACTIONS


def test_existing_factors_preserved():
    assert PurchasingPreset().shape.factor_names[:6] == EXISTING_FACTORS


def test_penalty_ratio_unchanged():
    assert PurchasingPreset().penalty_ratio == 3.0


def test_eta_confirm_unchanged():
    assert PurchasingPreset().eta_confirm == 0.05


def test_eta_override_unchanged():
    assert PurchasingPreset().eta_override == 0.01


def test_tau_unchanged():
    assert PurchasingPreset().temperature == 0.1


def test_q_window_unchanged():
    assert PurchasingPreset().q_window == 400


def test_centroids_have_20_cells_7d():
    centroids = PurchasingPreset().bootstrap_centroids

    assert centroids.shape == (5, 4, 7)
    assert centroids.shape[0] * centroids.shape[1] == 20


def test_all_centroid_values_bounded():
    centroids = PurchasingPreset().bootstrap_centroids

    assert np.all(centroids >= 0.0)
    assert np.all(centroids <= 1.0)


def test_new_factor_initialized_neutral():
    np.testing.assert_allclose(PurchasingPreset().bootstrap_centroids[:, :, 6], 0.50)


def test_existing_centroid_values_unchanged_for_sample_cells():
    centroids = PurchasingPreset().bootstrap_centroids

    for (category_index, action_index), expected in SAMPLE_LEGACY_CELLS.items():
        np.testing.assert_allclose(
            centroids[category_index, action_index, :6],
            expected,
            rtol=0.0,
            atol=1e-12,
        )


def test_scorer_can_initialize_with_purchasing_config(tmp_path):
    scorer = CompoundingScorer.from_preset("purchasing", db_path=str(tmp_path / "purchasing.db"))

    try:
        assert scorer.gae_scorer.centroids.shape == (5, 4, 7)
    finally:
        scorer.graph_store.close()


def test_iks_endpoint_or_iks_config_available(client):
    response = client.get("/api/trajectory")

    assert response.status_code == 200
    payload = response.json()
    assert "current_iks" in payload
    assert isinstance(payload["current_iks"], (int, float))
