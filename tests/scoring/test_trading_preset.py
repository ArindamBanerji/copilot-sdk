import json
import os
import sys
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
from copilot_sdk.scoring.presets.trading import TradingPreset
from copilot_sdk.scoring.verification.price import verify_trade


PRESET_DIR = Path(__file__).resolve().parents[2] / "copilot_sdk" / "scoring" / "presets"
SEED_PATH = PRESET_DIR / "trading_seed.json"
BOOTSTRAP_PATH = PRESET_DIR / "trading_bootstrap.json"


def load_seed_trades() -> list[dict]:
    raw = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    return raw["trades"] if isinstance(raw, dict) else raw


def build_verified_decisions(trades: list[dict], preset: TradingPreset) -> list[dict]:
    return [
        {
            "category": trade["category"],
            "factor_vector": [
                float(trade["factors"][factor])
                for factor in preset.shape.factor_names
            ],
            "is_correct": bool(trade["is_correct"]),
        }
        for trade in trades
    ]


def correct_rate(trades: list[dict]) -> float:
    assert trades
    return sum(1 for trade in trades if trade["is_correct"]) / len(trades)


def test_preset_loads():
    preset = TradingPreset()

    assert preset.name == "trading"
    assert preset.shape.n_categories == 5
    assert preset.shape.n_actions == 3
    assert preset.shape.n_factors == 6
    assert len(preset.shape.category_names) == 5
    assert len(preset.shape.action_names) == 3
    assert len(preset.shape.factor_names) == 6
    assert preset.penalty_ratio == 2.0
    assert preset.eta_confirm == 0.05
    assert preset.eta_override == 0.01
    assert preset.temperature == 0.1


def test_preset_in_registry():
    assert "trading" in PRESET_REGISTRY
    assert PRESET_REGISTRY["trading"] is TradingPreset
    assert PRESET_REGISTRY["trading"]().name == "trading"


def test_from_preset_trading_works(tmp_path):
    db_path = tmp_path / "trading.db"

    scorer = CompoundingScorer.from_preset("trading", db_path=str(db_path))

    assert scorer is not None
    scorer._store.close()


def test_seed_data_loads():
    trades = load_seed_trades()

    assert len(trades) == 20
    assert sum(1 for trade in trades if trade["is_correct"]) == 11
    assert sum(1 for trade in trades if not trade["is_correct"]) == 9


def test_seed_covers_expected_categories():
    preset = TradingPreset()
    trades = load_seed_trades()
    observed = {trade["category"] for trade in trades}

    assert set(preset.shape.category_names) == {
        "equity_long",
        "equity_short",
        "crypto_spot",
        "options",
        "etf",
    }
    assert {"equity_long", "crypto_spot", "options", "etf"}.issubset(observed)
    assert len(observed) >= 4
    assert "equity_short" not in observed


def test_seed_factors_match_preset():
    preset = TradingPreset()
    trades = load_seed_trades()
    factor_names = set(preset.shape.factor_names)

    assert any(trade["trade_id"] == "T020" for trade in trades)
    assert all(trade["trade_id"] != "T020-original" for trade in trades)

    for trade in trades:
        assert trade["category"] in preset.shape.category_names
        assert trade["direction"] in preset.shape.action_names
        assert set(trade["factors"]) == factor_names
        assert all(0.0 <= float(value) <= 1.0 for value in trade["factors"].values())


def test_bootstrap_centroids_shape():
    assert TradingPreset().bootstrap_centroids.shape == (5, 3, 6)


def test_bootstrap_produces_target_correct_action_probability():
    preset = TradingPreset()
    trades = load_seed_trades()
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

    for trade in trades:
        factors = np.array(
            [float(trade["factors"][factor]) for factor in preset.shape.factor_names],
            dtype=float,
        )
        result = scorer.score(factors, category_index[trade["category"]])
        correct_action_probabilities.append(
            float(result.probabilities[action_index[trade["direction"]]])
        )

    mean_probability = sum(correct_action_probabilities) / len(
        correct_action_probabilities
    )
    assert 0.45 <= mean_probability <= 0.60

    metadata = json.loads(BOOTSTRAP_PATH.read_text(encoding="utf-8"))
    if "mean_confidence" in metadata:
        assert 0.45 <= float(metadata["mean_confidence"]) <= 0.60


def test_research_depth_more_predictive_than_conviction_in_seed():
    trades = load_seed_trades()
    high_research = [
        trade for trade in trades if trade["factors"]["research_depth"] >= 0.7
    ]
    low_research = [
        trade for trade in trades if trade["factors"]["research_depth"] < 0.4
    ]
    high_conviction = [
        trade for trade in trades if trade["factors"]["conviction"] >= 0.7
    ]
    low_conviction = [
        trade for trade in trades if trade["factors"]["conviction"] < 0.4
    ]

    research_separation = correct_rate(high_research) - correct_rate(low_research)
    conviction_separation = correct_rate(high_conviction) - correct_rate(
        low_conviction
    )

    assert research_separation > 0.40
    assert research_separation > conviction_separation


def test_fingerprint_shows_research_depth_signal_if_stable():
    preset = TradingPreset()
    trades = load_seed_trades()
    result = compute_fingerprint(
        build_verified_decisions(trades, preset),
        list(preset.shape.factor_names),
    )
    factors = {factor.name: factor for factor in result.factors}

    assert set(factors) == set(preset.shape.factor_names)
    assert factors["research_depth"].weight >= factors["conviction"].weight
    assert factors["research_depth"].sigma <= factors["conviction"].sigma


def test_price_verification_cached():
    result = verify_trade("NVDA", 142.0, "buy", use_live=False)

    assert result.is_correct is True
    assert result.source == "cached_seed"


def test_price_verification_sell_incorrect():
    result = verify_trade("SPY", 510.0, "sell", use_live=False)

    assert result.is_correct is False
    assert result.source == "cached_seed"


def test_price_verification_unknown_ticker():
    result = verify_trade("ZZZZ", 100.0, "buy", use_live=False)

    assert result.source == "unknown_ticker"
    assert result.is_correct is False
    assert result.current_price == result.entry_price


def test_end_to_end_score_learn_fingerprint_smoke(tmp_path):
    db_path = tmp_path / "trading_smoke.db"
    scorer = CompoundingScorer.from_preset("trading", db_path=str(db_path))
    trade = load_seed_trades()[0]

    score = scorer.score(trade["factors"], trade["category"])
    learn = scorer.learn(score.decision_id, score.action, "confirmed")
    fingerprint = scorer.fingerprint()
    trajectory = scorer.trajectory()

    assert learn.decisions_total == 1
    assert fingerprint.decisions_analyzed == 1
    assert trajectory.decisions_total == 1
    scorer._store.close()
    if db_path.exists():
        os.remove(db_path)
