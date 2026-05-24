from __future__ import annotations

import pytest

from app.routers.data_import import _trade_store_ref


def _trade(
    trade_id: str,
    *,
    ticker: str = "MSFT",
    category: str = "trend_following",
    strategy_tag: str = "momentum",
    regime: str = "bull",
    pnl: float | None = 100.0,
    confidence: float = 0.8,
    entry_time: str = "2026-01-01T09:30:00",
) -> dict:
    return {
        "trade_id": trade_id,
        "ticker": ticker,
        "direction": "long",
        "entry_price": 100.0,
        "exit_price": 110.0 if pnl is not None else None,
        "size": 1.0,
        "entry_time": entry_time,
        "exit_time": "2026-01-02T16:00:00",
        "strategy_tag": strategy_tag,
        "category": category,
        "regime": regime,
        "pnl": pnl,
        "factors": {"signal_alignment": 0.8},
        "action": "strong_execution",
        "confidence": confidence,
        "metadata": {"source": "test"},
    }


@pytest.fixture(autouse=True)
def reset_trade_store():
    _trade_store_ref.clear()
    yield
    _trade_store_ref.clear()


def _seed_trades() -> None:
    _trade_store_ref.extend(
        [
            _trade("t-1", ticker="MSFT", category="trend_following", strategy_tag="momentum", regime="bull", pnl=120.0, confidence=0.9, entry_time="2026-01-05T09:30:00"),
            _trade("t-2", ticker="SPY", category="mean_reversion", strategy_tag="hedge", regime="bear", pnl=-40.0, confidence=0.7, entry_time="2026-01-20T09:30:00"),
            _trade("t-3", ticker="MSFT", category="trend_following", strategy_tag="swing", regime="bull", pnl=0.0, confidence=0.5, entry_time="2026-02-03T09:30:00"),
        ]
    )


def test_trades_returns_list(client):
    _seed_trades()

    response = client.get("/api/trading/trades")

    assert response.status_code == 200
    assert len(response.json()["trades"]) == 3
    assert response.json()["total"] == 3


def test_trades_filter_by_ticker(client):
    _seed_trades()

    response = client.get("/api/trading/trades?ticker=msft")

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert {trade["ticker"] for trade in response.json()["trades"]} == {"MSFT"}


def test_trades_filter_by_category(client):
    _seed_trades()

    response = client.get("/api/trading/trades?category=mean_reversion")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["trades"][0]["trade_id"] == "t-2"


def test_trades_filter_by_strategy_tag(client):
    _seed_trades()

    response = client.get("/api/trading/trades?strategy_tag=swing")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["trades"][0]["trade_id"] == "t-3"


def test_trades_filter_by_outcome_win(client):
    _seed_trades()

    response = client.get("/api/trading/trades?outcome=win")

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["trades"][0]["trade_id"] == "t-1"


def test_trades_filter_by_outcome_loss(client):
    _seed_trades()

    response = client.get("/api/trading/trades?outcome=loss")

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert {trade["trade_id"] for trade in response.json()["trades"]} == {"t-2", "t-3"}


def test_trades_limit_and_offset(client):
    _seed_trades()

    response = client.get("/api/trading/trades?limit=1&offset=1")

    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert [trade["trade_id"] for trade in response.json()["trades"]] == ["t-2"]


def test_trades_aggregate_stats_computed(client):
    _seed_trades()

    response = client.get("/api/trading/trades")

    aggregate = response.json()["aggregate"]
    assert aggregate["total_trades"] == 3
    assert aggregate["total_pnl"] == 80.0
    assert round(aggregate["avg_confidence"], 4) == 0.7


def test_trades_empty_returns_empty_list(client):
    response = client.get("/api/trading/trades?limit=50")

    assert response.status_code == 200
    assert response.json()["trades"] == []
    assert response.json()["total"] == 0


def test_trades_aggregate_win_rate_is_wins_over_total(client):
    _seed_trades()

    response = client.get("/api/trading/trades")

    assert response.json()["aggregate"]["win_rate"] == 1 / 3


def test_trade_detail_found(client):
    _seed_trades()

    response = client.get("/api/trading/trades/t-1")

    assert response.status_code == 200
    assert response.json()["trade_id"] == "t-1"
    assert response.json()["ticker"] == "MSFT"


def test_trade_detail_not_found_404(client):
    response = client.get("/api/trading/trades/missing")

    assert response.status_code == 404
    assert response.json() == {"error": "Trade not found"}


def test_trade_detail_includes_factors(client):
    _seed_trades()

    response = client.get("/api/trading/trades/t-1")

    assert response.status_code == 200
    assert response.json()["factors"]["signal_alignment"] == 0.8


def test_analytics_group_by_category(client):
    _seed_trades()

    response = client.get("/api/trading/analytics?group_by=category")

    assert response.status_code == 200
    groups = {group["key"]: group for group in response.json()["groups"]}
    assert groups["trend_following"]["count"] == 2
    assert groups["mean_reversion"]["count"] == 1


def test_analytics_group_by_ticker(client):
    _seed_trades()

    response = client.get("/api/trading/analytics?group_by=ticker")

    groups = {group["key"]: group for group in response.json()["groups"]}
    assert groups["MSFT"]["count"] == 2
    assert groups["SPY"]["count"] == 1


def test_analytics_group_by_strategy(client):
    _seed_trades()

    response = client.get("/api/trading/analytics?group_by=strategy_tag")

    groups = {group["key"]: group for group in response.json()["groups"]}
    assert groups["momentum"]["count"] == 1
    assert groups["hedge"]["count"] == 1


def test_analytics_group_by_month(client):
    _seed_trades()

    response = client.get("/api/trading/analytics?group_by=month")

    groups = {group["key"]: group for group in response.json()["groups"]}
    assert groups["2026-01"]["count"] == 2
    assert groups["2026-02"]["count"] == 1


def test_analytics_with_filters(client):
    _seed_trades()

    response = client.get("/api/trading/analytics?group_by=ticker&category=trend_following")

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert {group["key"] for group in response.json()["groups"]} == {"MSFT"}


def test_analytics_win_rate_correct(client):
    _seed_trades()

    response = client.get("/api/trading/analytics?group_by=regime")

    groups = {group["key"]: group for group in response.json()["groups"]}
    assert groups["bull"]["win_rate"] == 0.5
    assert groups["bear"]["win_rate"] == 0.0


def test_analytics_empty_group(client):
    response = client.get("/api/trading/analytics?group_by=category")

    assert response.status_code == 200
    assert response.json() == {"group_by": "category", "groups": [], "total": 0}
