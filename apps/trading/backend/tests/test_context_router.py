from __future__ import annotations

from fastapi.testclient import TestClient

from copilot_sdk.scoring.presets.trading import TradingPreset


def _seed_trade(client: TestClient) -> str:
    response = client.post(
        "/api/score",
        json={
            "category": "trend_following",
            "factors": {
                name: 0.7
                for name in TradingPreset().shape.factor_names
            },
            "metadata": {
                "ticker": "AAPL",
                "thesis": "Breakout with improving breadth",
            },
        },
    )
    assert response.status_code == 200
    return str(response.json()["decision_id"])


def test_trade_detail_valid(client: TestClient) -> None:
    trade_id = _seed_trade(client)

    response = client.get(f"/api/trading/trades/{trade_id}")

    assert response.status_code == 200
    assert response.json()["trade_id"] == trade_id
    assert response.json()["ticker"] == "AAPL"


def test_trade_detail_unknown_returns_default(client: TestClient) -> None:
    response = client.get("/api/trading/trades/fake-id")

    assert response.status_code == 200
    assert response.json()["trade_id"] == "fake-id"
    assert response.json()["metadata"] == {}


def test_trade_detail_response_shape(client: TestClient) -> None:
    trade_id = _seed_trade(client)

    payload = client.get(f"/api/trading/trades/{trade_id}").json()

    assert isinstance(payload["trade_id"], str)
    assert isinstance(payload["ticker"], str)
    assert isinstance(payload["timestamp"], str)
    assert isinstance(payload["category"], str)
    assert isinstance(payload["action"], str)
    assert isinstance(payload["thesis"], str)
    assert isinstance(payload["factors"], dict)
    assert set(payload["factors"]) == set(TradingPreset().shape.factor_names)
    assert isinstance(payload["composite_score"], float)
    assert payload["outcome"] in {"verified", "pending", "overridden"}
    assert isinstance(payload["confidence"], float)
    assert isinstance(payload["metadata"], dict)


def test_trade_evidence_valid(client: TestClient) -> None:
    trade_id = _seed_trade(client)

    response = client.get(f"/api/trading/evidence/{trade_id}")

    assert response.status_code == 200
    assert response.json()["trade_id"] == trade_id
    assert isinstance(response.json()["similar_trades"], list)


def test_trade_evidence_unknown_returns_default(client: TestClient) -> None:
    response = client.get("/api/trading/evidence/fake-id")

    assert response.status_code == 200
    assert response.json()["trade_id"] == "fake-id"
    assert response.json()["factors"] == []


def test_trade_evidence_has_factors(client: TestClient) -> None:
    trade_id = _seed_trade(client)

    factors = client.get(f"/api/trading/evidence/{trade_id}").json()["factors"]

    assert factors
    assert all(set(factor) == {"name", "score", "weight"} for factor in factors)


def test_trade_evidence_has_counterfactual(client: TestClient) -> None:
    trade_id = _seed_trade(client)

    counterfactual = client.get(f"/api/trading/evidence/{trade_id}").json()["counterfactual"]

    assert set(counterfactual) == {"alternate_action", "projected_score", "delta"}
    assert counterfactual["alternate_action"] in TradingPreset().shape.action_names
    assert isinstance(counterfactual["projected_score"], float)
    assert isinstance(counterfactual["delta"], float)
