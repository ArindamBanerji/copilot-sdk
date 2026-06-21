from __future__ import annotations

import json

from copilot_sdk.scoring.presets.trading import TradingPreset
from generators.trading_synthetic import DEFAULT_OUTPUT_PATH, PATTERNS, generate_trades, main


def test_generate_trades_count():
    assert len(generate_trades()) == 2000


def test_generate_trades_is_deterministic_for_same_seed():
    assert generate_trades(seed=7) == generate_trades(seed=7)


def test_generate_trades_covers_categories_actions_and_patterns():
    trades = generate_trades()
    preset = TradingPreset()

    assert {trade["category"] for trade in trades} == set(preset.shape.category_names)
    assert {trade["action"] for trade in trades} == set(preset.shape.action_names)
    assert {trade["pattern"] for trade in trades} == set(PATTERNS)


def test_generated_trades_include_verification_metrics():
    trade = generate_trades(n=1)[0]

    assert isinstance(trade["r_multiple"], float)
    assert isinstance(trade["execution_quality"], float)
    assert 0.0 <= trade["execution_quality"] <= 1.0
    assert 0.0 <= trade["verification_score"] <= 1.0


def test_generated_factors_match_trading_preset_exactly():
    preset = TradingPreset()

    for trade in generate_trades(n=25):
        assert tuple(trade["factors"]) == preset.shape.factor_names
        assert all(0.0 <= value <= 1.0 for value in trade["factors"].values())


def test_generated_trades_include_preseed_compatible_fields():
    trade = generate_trades(n=1)[0]

    for field in (
        "trade_id",
        "category",
        "direction",
        "action_taken",
        "is_correct",
        "provenance",
        "factors",
        "metadata",
    ):
        assert field in trade
    assert trade["provenance"] == "sample"


def test_main_writes_valid_generated_file():
    main()

    trades = json.loads(DEFAULT_OUTPUT_PATH.read_text(encoding="utf-8"))
    assert len(trades) == 2000
    assert all("r_multiple" in trade for trade in trades)
    assert all("execution_quality" in trade for trade in trades)
    assert all(trade.get("provenance") == "sample" for trade in trades)
