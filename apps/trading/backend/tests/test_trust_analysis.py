from __future__ import annotations

import pytest

from app.factors.registry import ALL_FACTOR_NAMES, TRADING_FACTOR_COMPUTERS
from app.routers.data_import import _trade_store_ref


@pytest.fixture(autouse=True)
def reset_trade_store():
    _trade_store_ref.clear()
    yield
    _trade_store_ref.clear()


def _trade(**overrides):
    payload = {
        "trade_id": "t-1",
        "ticker": "MSFT",
        "direction": "long",
        "entry_price": 100.0,
        "size": 1.0,
        "tagged_signals": [{"name": "breakout", "confirmed": True}],
        "has_trade_plan": True,
        "position_conviction": 0.8,
        "size_vs_rolling_avg": 1.0,
        "rsi_at_entry": 42,
        "macd_signal": "bullish",
        "price_vs_sma": 1.05,
        "entry_direction": "long",
        "current_regime": "trending",
        "regime_accuracy": {"trending": 0.8},
    }
    payload.update(overrides)
    return payload


def test_trust_endpoint_200_empty(client):
    response = client.get("/api/context/trust-analysis")

    assert response.status_code == 200


def test_trust_empty_has_all_7_factors(client):
    payload = client.get("/api/context/trust-analysis").json()

    assert payload["factors"] == list(ALL_FACTOR_NAMES)
    assert len(payload["factors"]) == 7
    assert set(payload["trust_scores"]) == set(ALL_FACTOR_NAMES)


def test_trust_empty_total_trades_zero(client):
    payload = client.get("/api/context/trust-analysis").json()

    assert payload["total_trades"] == 0
    assert payload["hero_insight"] is None
    for factor, score in payload["trust_scores"].items():
        assert score["variance"] == 0.0
        assert score["mean"] == 0.5
        assert score["n_samples"] == 0
        expected = "not_computed" if factor not in TRADING_FACTOR_COMPUTERS else "insufficient_data"
        assert score["trust_label"] == expected
        assert score["sigma"] == 0.0


def test_trust_with_trades(client):
    _trade_store_ref.extend(
        [
            _trade(trade_id="t-1", position_conviction=0.9, rsi_at_entry=35),
            _trade(trade_id="t-2", position_conviction=0.6, rsi_at_entry=62, current_regime="ranging"),
            _trade(trade_id="t-3", position_conviction=0.3, rsi_at_entry=76, macd_signal="bearish"),
        ]
    )

    payload = client.get("/api/context/trust-analysis").json()

    assert payload["total_trades"] == 3
    assert payload["trust_scores"]["conviction"]["n_samples"] == 3
    assert payload["trust_scores"]["conviction"]["variance"] > 0.0


def test_trust_scores_have_required_fields(client):
    _trade_store_ref.append(_trade())

    payload = client.get("/api/context/trust-analysis").json()

    for score in payload["trust_scores"].values():
        assert {"variance", "mean", "n_samples", "trust_label", "sigma"} <= set(score)
        assert isinstance(score["variance"], (int, float))
        assert isinstance(score["mean"], (int, float))
        assert isinstance(score["n_samples"], int)
        assert isinstance(score["sigma"], (int, float))


def test_trust_route_mounted(client):
    paths = {route.path for route in client.app.routes}

    assert "/api/context/trust-analysis" in paths


def test_implemented_factors_match_registry(client):
    payload = client.get("/api/context/trust-analysis").json()

    assert set(payload["implemented"]) == set(TRADING_FACTOR_COMPUTERS)


def test_unimplemented_factors_marked_not_computed_or_insufficient(client):
    _trade_store_ref.append(_trade())

    payload = client.get("/api/context/trust-analysis").json()

    for factor in ALL_FACTOR_NAMES:
        label = payload["trust_scores"][factor]["trust_label"]
        if factor in TRADING_FACTOR_COMPUTERS:
            assert label != "not_computed"
        else:
            assert label == "not_computed"


def test_hero_insight_shape_when_available(client):
    _trade_store_ref.extend(
        [
            _trade(trade_id="t-1", position_conviction=0.95, rsi_at_entry=32, current_regime="trending"),
            _trade(trade_id="t-2", position_conviction=0.45, rsi_at_entry=66, current_regime="trending"),
            _trade(trade_id="t-3", position_conviction=0.15, rsi_at_entry=78, current_regime="trending"),
        ]
    )

    payload = client.get("/api/context/trust-analysis").json()
    insight = payload["hero_insight"]

    assert insight is not None
    assert {
        "overused_factor",
        "overused_sigma",
        "underused_factor",
        "underused_sigma",
        "message",
    } <= set(insight)
    assert insight["overused_factor"] in TRADING_FACTOR_COMPUTERS
    assert insight["underused_factor"] in TRADING_FACTOR_COMPUTERS
