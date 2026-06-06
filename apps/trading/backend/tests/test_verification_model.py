from __future__ import annotations

from app.models.trade import NormalizedTrade
from app.services.verification import (
    compute_execution_quality,
    compute_r_multiple,
    compute_verification_score,
)


def test_profitable_long_r_multiple():
    assert compute_r_multiple(100.0, 110.0, 95.0, "long") == 2.0


def test_losing_long_r_multiple():
    assert compute_r_multiple(100.0, 96.0, 95.0, "long") == -0.8


def test_no_stop_loss_uses_simple_long_return():
    assert compute_r_multiple(100.0, 105.0, side="long") == 0.05


def test_profitable_short_r_multiple():
    assert compute_r_multiple(100.0, 90.0, 105.0, "short") == 2.0


def test_zero_entry_returns_zero():
    assert compute_r_multiple(0.0, 110.0, 95.0, "long") == 0.0


def test_invalid_stop_risk_returns_zero():
    assert compute_r_multiple(100.0, 110.0, 101.0, "long") == 0.0
    assert compute_r_multiple(100.0, 90.0, 99.0, "short") == 0.0


def test_perfect_execution_quality():
    assert compute_execution_quality(100.0, 100.0, 110.0, 110.0, 1.0) == 1.0


def test_slippage_reduces_execution_quality():
    assert compute_execution_quality(100.0, 103.0, 110.0, 107.0, 1.0) < 1.0


def test_partial_fill_reduces_execution_quality():
    assert compute_execution_quality(100.0, 100.0, 110.0, 110.0, 0.5) == 0.85


def test_perfect_trade_score_high():
    result = compute_verification_score(3.0, 1.0, True)

    assert result.verification_score == 1.0
    assert result.components == {
        "r_multiple": 0.4,
        "execution_quality": 0.3,
        "outcome": 0.3,
    }


def test_losing_trade_bad_execution_low():
    result = compute_verification_score(-2.0, 0.0, False)

    assert result.verification_score == 0.0


def test_components_present():
    result = compute_verification_score(0.5, 0.75, True)

    assert set(result.components) == {
        "r_multiple",
        "execution_quality",
        "outcome",
    }


def test_normalized_trade_verification_fields_are_optional_and_serialized():
    trade = NormalizedTrade(
        trade_id="t-verify",
        broker="csv",
        ticker="spy",
        direction="long",
        entry_price=100,
        stop_loss=95,
        expected_entry_price=99,
        expected_exit_price=110,
        fill_rate=0.8,
        r_multiple=2,
        execution_quality=0.9,
        verification_score=0.92,
    )

    payload = trade.to_dict()
    assert trade.ticker == "SPY"
    assert payload["stop_loss"] == 95.0
    assert payload["expected_entry_price"] == 99.0
    assert payload["expected_exit_price"] == 110.0
    assert payload["fill_rate"] == 0.8
    assert payload["r_multiple"] == 2.0
    assert payload["execution_quality"] == 0.9
    assert payload["verification_score"] == 0.92
