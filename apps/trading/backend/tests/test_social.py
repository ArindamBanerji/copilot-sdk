from __future__ import annotations

import math
from typing import Any


TRADING_FACTORS = {
    "signal_alignment": 0.82,
    "market_regime": 0.88,
    "position_sizing": 0.76,
    "timing_quality": 0.64,
    "risk_reward_actual": 0.67,
    "emotional_indicator": 0.71,
    "signal_confidence": 0.50,
    "options_delta_exposure": 0.50,
    "options_iv_percentile": 0.50,
    "options_gamma_risk": 0.50,
}
VALID_CATEGORIES = {"trend_following", "mean_reversion", "event_driven", "income_strategy", "scalp_intraday"}
VALID_ACTIONS = {"strong_execution", "partial_execution", "poor_execution", "skip_recommended"}
VALID_FACTORS = set(TRADING_FACTORS)
FORBIDDEN_TERMS = ("buy", "sell", "hold", "SOC", "SC-")


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


def assert_no_forbidden_terms(value: Any) -> None:
    text = str(value)
    for term in FORBIDDEN_TERMS:
        assert term.lower() not in text.lower()


def _score_as(client, trader_id: str | None = "alice", category: str = "trend_following") -> dict[str, Any]:
    payload: dict[str, Any] = {
        "category": category,
        "factors": TRADING_FACTORS,
    }
    if trader_id is not None:
        payload["trader_id"] = trader_id
    response = client.post("/api/trading/score-as", json=payload)
    assert response.status_code == 200
    return response.json()


def _learn(client, decision_id: str, actual_action: str) -> dict[str, Any]:
    response = client.post("/api/learn", json={"decision_id": decision_id, "actual_action": actual_action})
    assert response.status_code == 200
    return response.json()


def _verified_score(client, trader_id: str, category: str = "trend_following") -> dict[str, Any]:
    scored = _score_as(client, trader_id=trader_id, category=category)
    _learn(client, scored["decision_id"], scored["action"])
    return scored


def test_traders_empty_store_returns_200_and_empty_list(client):
    response = client.get("/api/trading/traders")

    assert response.status_code == 200
    payload = response.json()
    assert payload["traders"] == []
    assert payload["count"] == 0
    assert_json_safe(payload)


def test_score_as_persists_trader_entity_id(client):
    scored = _verified_score(client, "alice")
    store = client.app.state if hasattr(client, "app") else None

    response = client.get("/api/trading/traders/alice/profile")
    profile = response.json()

    assert response.status_code == 200
    assert profile["trader_id"] == "alice"
    assert profile["verified_count"] == 1
    assert scored["trader_id"] == "alice"
    assert_json_safe(profile)
    assert store is not None


def test_score_as_defaults_trader_to_default(client):
    scored = _score_as(client, trader_id=None)
    _learn(client, scored["decision_id"], scored["action"])

    traders = client.get("/api/trading/traders").json()["traders"]

    assert any(row["trader_id"] == "default" for row in traders)


def test_alice_verified_count_reaches_five(client):
    for category in ("trend_following", "mean_reversion", "event_driven", "income_strategy", "scalp_intraday"):
        _verified_score(client, "alice", category=category)

    traders = client.get("/api/trading/traders").json()["traders"]
    alice = next(row for row in traders if row["trader_id"] == "alice")

    assert alice["verified_count"] == 5
    assert 0.0 <= alice["accuracy"] <= 1.0


def test_alice_and_bob_are_listed(client):
    _verified_score(client, "alice", category="trend_following")
    _verified_score(client, "bob", category="mean_reversion")

    traders = client.get("/api/trading/traders").json()["traders"]

    assert {row["trader_id"] for row in traders} >= {"alice", "bob"}


def test_trader_profile_returns_category_and_accuracy(client):
    _verified_score(client, "alice", category="trend_following")

    response = client.get("/api/trading/traders/alice/profile")
    profile = response.json()

    assert response.status_code == 200
    assert profile["trader_id"] == "alice"
    assert profile["verified_count"] == 1
    assert "by_category" in profile
    assert set(profile["by_category"]).issubset(VALID_CATEGORIES)
    assert 0.0 <= profile["accuracy"] <= 1.0
    assert_json_safe(profile)


def test_trader_edge_returns_factor_strengths_and_summary(client):
    _verified_score(client, "alice", category="trend_following")

    response = client.get("/api/trading/traders/alice/edge")
    payload = response.json()

    assert response.status_code == 200
    assert "factor_strengths" in payload
    assert "edge_summary" in payload
    for row in payload["factor_strengths"]:
        assert row["factor"] in VALID_FACTORS
    assert_no_forbidden_terms(payload)
    assert_json_safe(payload)


def test_trader_compare_requires_two_ids(client):
    response = client.get("/api/trading/traders/compare", params={"ids": "alice"})

    assert response.status_code == 400


def test_trader_compare_returns_comparison(client):
    _verified_score(client, "alice", category="trend_following")
    _verified_score(client, "bob", category="mean_reversion")

    response = client.get("/api/trading/traders/compare", params={"ids": "alice,bob"})
    payload = response.json()

    assert response.status_code == 200
    assert [row["trader_id"] for row in payload["traders"]] == ["alice", "bob"]
    assert "complementary_edges" in payload
    assert_no_forbidden_terms(payload)
    assert_json_safe(payload)


def test_leaderboard_returns_sorted_ranking(client):
    _verified_score(client, "alice", category="trend_following")
    _verified_score(client, "bob", category="mean_reversion")

    response = client.get("/api/trading/social/leaderboard")
    payload = response.json()

    assert response.status_code == 200
    assert payload["metric"] == "accuracy"
    assert len(payload["ranking"]) == 2
    accuracies = [row["accuracy"] for row in payload["ranking"]]
    assert accuracies == sorted(accuracies, reverse=True)
    assert_json_safe(payload)


def test_nonexistent_trader_profile_returns_defaults(client):
    response = client.get("/api/trading/traders/missing/profile")
    profile = response.json()

    assert response.status_code == 200
    assert profile["trader_id"] == "missing"
    assert profile["verified_count"] == 0
    assert profile["accuracy"] == 0.0
    assert_json_safe(profile)
