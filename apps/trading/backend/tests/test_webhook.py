from __future__ import annotations

import math
from typing import Any


VALID_FACTORS = {
    "signal_alignment",
    "market_regime",
    "position_sizing",
    "timing_quality",
    "risk_reward_actual",
    "emotional_indicator",
    "signal_confidence",
}
VALID_ACTIONS = {
    "strong_execution",
    "partial_execution",
    "poor_execution",
    "skip_recommended",
}
VALID_CATEGORIES = {
    "trend_following",
    "mean_reversion",
    "event_driven",
    "income_strategy",
    "scalp_intraday",
}
FORBIDDEN_TERMS = ("SOC", "SC-")


def valid_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ticker": "AAPL",
        "action": "buy",
        "price": 150.25,
        "time": "2026-05-27T10:30:00Z",
        "interval": "1h",
        "exchange": "NASDAQ",
        "strategy": "RSI_Oversold",
        "category": "mean_reversion",
        "auto_score": False,
        "indicators": {
            "rsi": 28.5,
            "macd": -0.3,
            "atr": 2.1,
            "volume": 1_500_000,
            "vix": 18.2,
        },
    }
    payload.update(overrides)
    return payload


def assert_json_safe(value: Any) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_json_safe(item)
    elif isinstance(value, list):
        for item in value:
            assert_json_safe(item)
    elif isinstance(value, float):
        assert math.isfinite(value)
    else:
        assert value is None or isinstance(value, (str, int, bool))


def assert_no_soc_vocabulary(value: Any) -> None:
    text = str(value)
    for term in FORBIDDEN_TERMS:
        assert term.lower() not in text.lower()


def test_tradingview_webhook_valid_payload_returns_received(client):
    response = client.post("/api/trading/webhook/tradingview", json=valid_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["received"] is True
    assert payload["scored"] is False
    assert payload["ticker"] == "AAPL"
    assert payload["event_id"].startswith("tv-")
    assert set(payload["mapped_factors"]) == VALID_FACTORS
    assert_json_safe(payload)


def test_tradingview_webhook_requires_ticker(client):
    response = client.post("/api/trading/webhook/tradingview", json=valid_payload(ticker=""))

    assert response.status_code in {400, 422}


def test_indicators_map_to_all_trading_factors(client):
    response = client.post("/api/trading/webhook/tradingview", json=valid_payload())
    factors = response.json()["mapped_factors"]

    assert set(factors) == VALID_FACTORS
    for value in factors.values():
        assert isinstance(value, float)
        assert math.isfinite(value)
        assert 0.0 <= value <= 1.0


def test_missing_indicators_default_to_neutral_factors(client):
    response = client.post(
        "/api/trading/webhook/tradingview",
        json=valid_payload(indicators={}),
    )

    assert response.status_code == 200
    assert response.json()["mapped_factors"] == {factor: 0.5 for factor in VALID_FACTORS}


def test_history_returns_received_event_after_post(client):
    posted = client.post("/api/trading/webhook/tradingview", json=valid_payload()).json()

    response = client.get("/api/trading/webhook/history")
    payload = response.json()

    assert response.status_code == 200
    assert isinstance(payload, list)
    assert payload[0]["event_id"] == posted["event_id"]
    assert payload[0]["ticker"] == "AAPL"
    assert_json_safe(payload)


def test_config_returns_factor_mapping_and_default_category(client):
    response = client.get("/api/trading/webhook/config")
    payload = response.json()

    assert response.status_code == 200
    assert payload["auto_score"] is False
    assert payload["default_category"] in VALID_CATEGORIES
    assert set(payload["valid_factors"]) == VALID_FACTORS
    assert set(payload["valid_actions"]) == VALID_ACTIONS
    assert payload["history_limit"] == 100
    assert "factor_mapping" in payload
    assert_json_safe(payload)


def test_webhook_test_endpoint_exercises_same_path(client):
    response = client.post("/api/trading/webhook/test", json={})
    payload = response.json()

    assert response.status_code == 200
    assert payload["received"] is True
    assert payload["event_id"].startswith("tv-")
    assert set(payload["mapped_factors"]) == VALID_FACTORS
    assert_json_safe(payload)


def test_auto_score_returns_execution_quality_recommendation(client):
    response = client.post(
        "/api/trading/webhook/tradingview",
        json=valid_payload(auto_score=True),
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["received"] is True
    assert payload["scored"] is True
    assert payload["decision_id"]
    assert payload["recommendation"] in VALID_ACTIONS
    assert isinstance(payload["confidence"], float)
    assert math.isfinite(payload["confidence"])
    assert 0.0 <= payload["confidence"] <= 1.0
    assert payload["recommendation"] not in {"buy", "sell", "hold"}
    assert_json_safe(payload)


def test_history_records_auto_score_result(client):
    scored = client.post(
        "/api/trading/webhook/tradingview",
        json=valid_payload(auto_score=True),
    ).json()

    event = client.get("/api/trading/webhook/history").json()[0]

    assert event["event_id"] == scored["event_id"]
    assert event["scored"] is True
    assert event["decision_id"] == scored["decision_id"]
    assert event["recommendation"] in VALID_ACTIONS


def test_webhook_responses_do_not_use_soc_vocabulary(client):
    response = client.post("/api/trading/webhook/tradingview", json=valid_payload())

    assert_no_soc_vocabulary(response.json())
