from __future__ import annotations

from datetime import datetime, timedelta

from app.models.trade import NormalizedTrade


def test_create_basic_trade():
    trade = NormalizedTrade(
        trade_id="t-1",
        broker="csv",
        ticker="msft",
        direction="long",
        entry_price=100.0,
    )

    assert trade.ticker == "MSFT"
    assert trade.direction == "long"
    assert trade.entry_price == 100.0


def test_closed_trade():
    trade = NormalizedTrade(
        trade_id="t-1",
        broker="csv",
        ticker="SPY",
        direction="long",
        entry_price=100.0,
        exit_price=104.0,
    )

    assert trade.is_closed is True


def test_computed_pnl_long():
    trade = NormalizedTrade(
        trade_id="t-1",
        broker="csv",
        ticker="SPY",
        direction="long",
        entry_price=100.0,
        exit_price=104.0,
        size=10,
        fees=1.0,
    )

    assert trade.computed_pnl == 39.0


def test_computed_pnl_short():
    trade = NormalizedTrade(
        trade_id="t-1",
        broker="csv",
        ticker="SPY",
        direction="short",
        entry_price=104.0,
        exit_price=100.0,
        size=10,
        fees=1.0,
    )

    assert trade.computed_pnl == 39.0


def test_to_dict_roundtrip():
    entry_time = datetime(2026, 1, 1, 9, 30)
    exit_time = entry_time + timedelta(minutes=90)
    trade = NormalizedTrade(
        trade_id="t-1",
        broker="csv",
        ticker="SPY",
        direction="long",
        entry_price=100.0,
        exit_price=101.0,
        size=2,
        entry_time=entry_time,
        exit_time=exit_time,
        strategy_tag="breakout",
        notes="clean test",
    )

    payload = trade.to_dict()
    assert payload["trade_id"] == "t-1"
    assert payload["ticker"] == "SPY"
    assert payload["entry_time"] == "2026-01-01T09:30:00"
    assert payload["hold_minutes"] == 90.0
    assert payload["strategy_tag"] == "breakout"
    assert payload["notes"] == "clean test"


def test_open_trade_no_pnl():
    trade = NormalizedTrade(
        trade_id="t-1",
        broker="csv",
        ticker="SPY",
        direction="long",
        entry_price=100.0,
        size=1,
    )

    assert trade.is_closed is False
    assert trade.computed_pnl is None
    assert trade.to_dict()["pnl"] is None


def test_pnl_field_overrides_computed():
    trade = NormalizedTrade(
        trade_id="t-1",
        broker="csv",
        ticker="SPY",
        direction="long",
        entry_price=100.0,
        exit_price=101.0,
        size=10,
        pnl=123.0,
    )

    assert trade.computed_pnl == 10.0
    assert trade.to_dict()["pnl"] == 123.0
