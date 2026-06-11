import json
import os
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pytest


GAE_PATH = Path(__file__).resolve().parents[2] / "graph-attention-engine-v50"
if GAE_PATH.exists() and str(GAE_PATH) not in sys.path:
    sys.path.insert(0, str(GAE_PATH))

pytest.importorskip("gae.profile_scorer")
from gae.profile_scorer import ProfileScorer

from copilot_sdk.scoring import CompoundingScorer
from copilot_sdk.scoring.fingerprint import compute_fingerprint
from copilot_sdk.scoring.presets import PRESET_REGISTRY
from copilot_sdk.scoring.presets.purchasing import PurchasingPreset
from copilot_sdk.scoring.verification.waste import verify_order
from copilot_sdk.scoring.verification.weather import _WEATHER_CACHE, get_weather_factor


PRESET_DIR = Path(__file__).resolve().parents[2] / "copilot_sdk" / "scoring" / "presets"
SEED_PATH = PRESET_DIR / "purchasing_seed.json"
BOOTSTRAP_PATH = PRESET_DIR / "purchasing_bootstrap.json"
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


def load_seed_orders() -> list[dict]:
    raw = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    return raw["orders"] if isinstance(raw, dict) else raw


def build_verified_decisions(orders: list[dict], preset: PurchasingPreset) -> list[dict]:
    return [
        {
            "category": order["category"],
            "factor_vector": [
                float(order["factors"].get(factor, 0.5))
                for factor in preset.shape.factor_names
            ],
            "is_correct": bool(order["is_correct"]),
        }
        for order in orders
    ]


def correct_rate(orders: list[dict]) -> float:
    assert orders
    return sum(1 for order in orders if order["is_correct"]) / len(orders)


def test_preset_loads():
    preset = PurchasingPreset()

    assert preset.name == "purchasing"
    assert preset.shape.n_categories == 5
    assert preset.shape.n_actions == 4
    assert preset.shape.n_factors == 7
    assert len(preset.shape.category_names) == 5
    assert len(preset.shape.action_names) == 4
    assert len(preset.shape.factor_names) == 7
    assert preset.shape.category_names == EXISTING_CATEGORIES
    assert preset.shape.action_names == EXISTING_ACTIONS
    assert preset.shape.factor_names[:6] == EXISTING_FACTORS
    assert preset.shape.factor_names[6] == "price_memory_index"
    assert preset.penalty_ratio == 3.0
    assert preset.eta_confirm == 0.05
    assert preset.eta_override == 0.01
    assert preset.temperature == 0.1
    assert preset.q_window == 400


def test_preset_in_registry():
    assert "purchasing" in PRESET_REGISTRY
    assert PRESET_REGISTRY["purchasing"] is PurchasingPreset
    assert PRESET_REGISTRY["purchasing"]().name == "purchasing"
    assert "trading" in PRESET_REGISTRY


def test_from_preset_purchasing_works(tmp_path):
    db_path = tmp_path / "purchasing.db"

    scorer = CompoundingScorer.from_preset("purchasing", db_path=str(db_path))

    assert scorer is not None
    scorer.graph_store.close()


def test_seed_data_loads():
    orders = load_seed_orders()

    assert len(orders) == 20
    assert sum(1 for order in orders if order["is_correct"]) == 13
    assert sum(1 for order in orders if not order["is_correct"]) == 7


def test_seed_covers_all_categories():
    preset = PurchasingPreset()
    orders = load_seed_orders()

    assert {order["category"] for order in orders} == set(preset.shape.category_names)


def test_seed_action_counts_are_as_expected():
    orders = load_seed_orders()

    assert Counter(order["action_taken"] for order in orders) == {
        "order_as_planned": 17,
        "order_more": 1,
        "order_less": 1,
        "skip": 1,
    }


def test_seed_factors_match_preset():
    preset = PurchasingPreset()
    orders = load_seed_orders()
    factor_names = set(preset.shape.factor_names)

    for order in orders:
        assert order["category"] in preset.shape.category_names
        assert order["action_taken"] in preset.shape.action_names
        assert set(order["factors"]) == factor_names - {"price_memory_index"}
        assert all(0.0 <= float(value) <= 1.0 for value in order["factors"].values())


def test_bootstrap_centroids_shape():
    assert PurchasingPreset().bootstrap_centroids.shape == (5, 4, 7)


def test_bootstrap_produces_target_correct_action_probability():
    preset = PurchasingPreset()
    orders = load_seed_orders()
    scorer = ProfileScorer(
        mu=preset.bootstrap_centroids,
        actions=list(preset.shape.action_names),
        categories=list(preset.shape.category_names),
    )
    action_index = {
        action: index for index, action in enumerate(preset.shape.action_names)
    }
    category_index = {
        category: index for index, category in enumerate(preset.shape.category_names)
    }
    correct_action_probabilities = []

    for order in orders:
        factors = np.array(
            [float(order["factors"].get(factor, 0.5)) for factor in preset.shape.factor_names],
            dtype=float,
        )
        result = scorer.score(factors, category_index[order["category"]])
        correct_action_probabilities.append(
            float(result.probabilities[action_index[order["action_taken"]]])
        )

    mean_probability = sum(correct_action_probabilities) / len(
        correct_action_probabilities
    )
    assert 0.45 <= mean_probability <= 0.60

    metadata = json.loads(BOOTSTRAP_PATH.read_text(encoding="utf-8"))
    if "mean_confidence" in metadata:
        assert 0.45 <= float(metadata["mean_confidence"]) <= 0.60


def test_weekday_protein_is_reliably_correct():
    orders = load_seed_orders()
    subset = [
        order
        for order in orders
        if order["category"] == "protein" and order["day_type"] == "weekday"
    ]

    assert len(subset) == 6
    assert sum(1 for order in subset if order["is_correct"]) == 6


def test_friday_produce_is_blind_spot():
    orders = load_seed_orders()
    subset = [
        order
        for order in orders
        if order["category"] == "produce" and order["day_type"] == "friday"
    ]

    assert len(subset) == 5
    assert sum(1 for order in subset if order["is_correct"]) == 1
    assert sum(1 for order in subset if not order["is_correct"]) == 4


def test_event_days_are_blind_spot():
    orders = load_seed_orders()
    # Values below 0.6, including 0.3, are ordinary local demand signals, not event days.
    subset = [order for order in orders if order["factors"]["event_flag"] >= 0.6]

    assert len(subset) == 3
    assert all(not order["is_correct"] for order in subset)
    assert all(order["stockout"] is True for order in subset)


def test_historical_waste_more_predictive_than_weather_or_event():
    orders = load_seed_orders()

    high_waste = [order for order in orders if order["factors"]["historical_waste"] >= 0.6]
    low_waste = [order for order in orders if order["factors"]["historical_waste"] < 0.4]
    high_weather = [order for order in orders if order["factors"]["weather_forecast"] >= 0.6]
    low_weather = [order for order in orders if order["factors"]["weather_forecast"] < 0.4]
    high_event = [order for order in orders if order["factors"]["event_flag"] >= 0.6]
    low_event = [order for order in orders if order["factors"]["event_flag"] < 0.4]

    waste_separation = abs(correct_rate(high_waste) - correct_rate(low_waste))
    weather_separation = abs(correct_rate(high_weather) - correct_rate(low_weather))
    event_separation = abs(correct_rate(high_event) - correct_rate(low_event))

    assert waste_separation > weather_separation
    assert waste_separation >= event_separation


def test_fingerprint_shows_historical_waste_signal_if_stable():
    preset = PurchasingPreset()
    orders = load_seed_orders()
    result = compute_fingerprint(
        build_verified_decisions(orders, preset),
        list(preset.shape.factor_names),
    )
    factors = {factor.name: factor for factor in result.factors}

    assert set(factors) == set(preset.shape.factor_names)
    assert factors["historical_waste"].weight >= factors["weather_forecast"].weight
    assert factors["historical_waste"].weight >= factors["event_flag"].weight
    assert factors["historical_waste"].sigma <= factors["weather_forecast"].sigma
    assert factors["historical_waste"].sigma <= factors["event_flag"].sigma


def test_waste_verification_over_order():
    result = verify_order(
        item="Lettuce",
        quantity_ordered=25,
        quantity_remaining=6,
        stockout=False,
        action_taken="order_as_planned",
    )

    assert result.is_correct is False
    assert "over-ordered" in result.explanation.lower()


def test_waste_verification_stockout():
    result = verify_order(
        item="Wings",
        quantity_ordered=30,
        quantity_remaining=0,
        stockout=True,
        action_taken="order_as_planned",
    )

    assert result.is_correct is False
    assert "should have ordered more" in result.explanation.lower()


def test_waste_verification_correct():
    result = verify_order(
        item="Wings",
        quantity_ordered=35,
        quantity_remaining=1.5,
        stockout=False,
        action_taken="order_as_planned",
    )

    assert result.is_correct is True


def test_weather_cached_returns_value():
    result = get_weather_factor(use_live=False)

    assert 0.0 <= result.weather_factor <= 1.0
    assert result.source == "cached"


def test_weather_factor_in_range():
    for forecast in _WEATHER_CACHE.values():
        assert 0.0 <= forecast.weather_factor <= 1.0


def test_end_to_end_score_learn_fingerprint_smoke(tmp_path):
    db_path = tmp_path / "purchasing_smoke.db"
    scorer = CompoundingScorer.from_preset("purchasing", db_path=str(db_path))
    order = next(order for order in load_seed_orders() if order["category"] == "produce")

    score = scorer.score(order["factors"], order["category"])
    learn = scorer.learn(score.decision_id, order["action_taken"], "confirmed")
    fingerprint = scorer.fingerprint()
    trajectory = scorer.trajectory()

    assert learn.decisions_total == 1
    assert fingerprint.decisions_analyzed == 1
    assert trajectory.decisions_total == 1
    scorer.graph_store.close()
    if db_path.exists():
        os.remove(db_path)
