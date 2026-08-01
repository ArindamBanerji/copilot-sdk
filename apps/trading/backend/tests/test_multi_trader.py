from __future__ import annotations

import pytest

from app.connectors.csv_connector import CSVConnector
from app.models.trade import NormalizedTrade
from app.routers import data_import
from app.services.trader_profiles import _decision_trader


TRADING_FACTORS = {
    "signal_alignment": 0.7,
    "market_regime": 0.5,
    "position_sizing": 0.6,
    "timing_quality": 0.8,
    "risk_reward_actual": 0.7,
    "emotional_indicator": 0.3,
    "signal_confidence": 0.9,
    "options_delta_exposure": 0.5,
    "options_iv_percentile": 0.5,
    "options_gamma_risk": 0.5,
}


def test_normalized_trade_defaults_trader_id_to_default() -> None:
    trade = NormalizedTrade(
        trade_id="t-default",
        broker="csv",
        ticker="AAPL",
        direction="long",
        entry_price=150,
    )

    assert trade.trader_id == "default"
    assert trade.to_dict()["trader_id"] == "default"


@pytest.mark.parametrize("raw", [None, "", "   "])
def test_normalized_trade_blank_trader_id_normalizes_to_default(raw: object) -> None:
    trade = NormalizedTrade(
        trade_id="t-blank",
        broker="csv",
        ticker="AAPL",
        direction="long",
        entry_price=150,
        trader_id=raw,  # type: ignore[arg-type]
    )

    assert trade.trader_id == "default"


def test_normalized_trade_explicit_trader_id_is_stripped() -> None:
    trade = NormalizedTrade(
        trade_id="t-alice",
        broker="csv",
        ticker="AAPL",
        direction="long",
        entry_price=150,
        trader_id=" alice ",
    )

    assert trade.trader_id == "alice"
    assert trade.to_dict()["trader_id"] == "alice"


@pytest.mark.parametrize(
    ("header", "value"),
    [
        ("trader_id", "alice"),
        ("trader", "bob"),
        ("user_id", "carol"),
        ("account", "acct-1"),
        ("account_id", "acct-2"),
    ],
)
def test_csv_connector_extracts_trader_id_aliases(header: str, value: str) -> None:
    csv_body = (
        f"ticker,direction,entry_price,size,entry_time,{header}\n"
        f"MSFT,buy,400,2,2026-01-01,{value}\n"
    )

    trades = CSVConnector().import_from_string(csv_body)

    assert len(trades) == 1
    assert trades[0].trader_id == value


def test_csv_connector_defaults_missing_or_blank_trader_id_to_default() -> None:
    trades = CSVConnector().import_from_string(
        "ticker,direction,entry_price,size,entry_time,trader_id\n"
        "MSFT,buy,400,2,2026-01-01,\n"
        "SPY,buy,450,1,2026-01-02,   \n"
    )
    missing = CSVConnector().import_from_string(
        "ticker,direction,entry_price,size,entry_time\n"
        "QQQ,buy,380,1,2026-01-03\n"
    )

    assert [trade.trader_id for trade in trades] == ["default", "default"]
    assert missing[0].trader_id == "default"


def test_csv_connector_preserves_multiple_traders() -> None:
    trades = CSVConnector().import_from_string(
        "ticker,direction,entry_price,size,entry_time,trader_id\n"
        "MSFT,buy,400,2,2026-01-01,alice\n"
        "SPY,buy,450,1,2026-01-02,bob\n"
    )

    assert [trade.trader_id for trade in trades] == ["alice", "bob"]


def test_import_csv_response_serializes_trader_id(client) -> None:
    data_import._trade_store_ref.clear()

    response = client.post(
        "/api/trading/import/csv",
        content=(
            "ticker,direction,entry_price,size,entry_time,trader_id\n"
            "MSFT,buy,400,2,2026-01-01,alice\n"
        ),
        headers={"content-type": "text/csv"},
    )

    assert response.status_code == 200
    assert response.json()["trades"][0]["trader_id"] == "alice"


def test_decision_trader_reads_metadata_trader_id_and_defaults() -> None:
    assert _decision_trader({"metadata": {"trader_id": "alice"}}) == "alice"
    assert _decision_trader({"metadata": {"trader_id": "  "}}) == "default"
    assert _decision_trader({"metadata": {}}) == "default"


def test_score_endpoint_accepts_optional_metadata_trader_id(client) -> None:
    response = client.post(
        "/api/score",
        json={
            "category": "trend_following",
            "factors": TRADING_FACTORS,
            "metadata": {"trader_id": "probe_trader"},
        },
    )

    assert response.status_code == 200
    decision_id = response.json()["decision_id"]
    assert decision_id.startswith("TRD-")
    decision = client.app.state.trading_selected_graph_store.get_decision(decision_id, domain="trading")
    assert decision is not None
    assert decision["metadata"]["trader_id"] == "probe_trader"


def test_score_endpoint_without_metadata_remains_backward_compatible(client) -> None:
    response = client.post(
        "/api/score",
        json={
            "category": "trend_following",
            "factors": TRADING_FACTORS,
        },
    )

    assert response.status_code == 200
    decision = client.app.state.trading_selected_graph_store.get_decision(
        response.json()["decision_id"], domain="trading"
    )
    assert decision is not None
    assert "trader_id" not in decision["metadata"]


def test_social_score_as_persists_trader_id_metadata(client) -> None:
    score = client.post(
        "/api/trading/score-as",
        json={
            "category": "trend_following",
            "factors": TRADING_FACTORS,
            "trader_id": "alice",
        },
    )
    assert score.status_code == 200
    payload = score.json()

    learn = client.post(
        "/api/learn",
        json={"decision_id": payload["decision_id"], "actual_action": payload["action"]},
    )
    assert learn.status_code == 200

    profile = client.get("/api/trading/traders/alice/profile")
    assert profile.status_code == 200
    assert profile.json()["trader_id"] == "alice"
    assert profile.json()["verified_count"] == 1
