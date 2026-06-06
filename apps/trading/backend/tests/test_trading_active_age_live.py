from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


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


pytestmark = pytest.mark.skipif(
    os.environ.get("TRADING_ACTIVE_LIVE_AGE_TEST") != "1",
    reason="set TRADING_ACTIVE_LIVE_AGE_TEST=1 to run guarded live Trading AGE tests",
)


def test_live_active_age_score_learn_route_surface_and_read_safety(tmp_path: Path):
    _require_live_env()
    client = TestClient(create_app(db_path=tmp_path / "unused.sqlite", demo_bundle_path=False))
    store = client.app.state.trading_selected_graph_store

    status = client.get("/api/trading/graph/status").json()
    assert status["active_backend"] == "age"
    assert status["age_active"] is True
    assert status["graph_kind"] == "test"
    assert status["active_domain"] == "trading"
    assert status["active_test_mode"] is True
    assert status["active_graph_name"] != "soc_graph"
    assert "postgres" not in str(status).lower()

    before = int(store.count_decisions("trading"))
    score = client.post(
        "/api/score",
        json={"category": "trend_following", "factors": TRADING_FACTORS},
    )
    assert score.status_code == 200
    score_payload = score.json()
    decision_id = score_payload["decision_id"]
    decision = store.get_decision(decision_id)
    assert decision is not None
    assert decision["decision_id"] == decision_id
    assert str(decision.get("status") or "").lower() == "pending"

    social = client.post(
        "/api/trading/score-as",
        json={"category": "mean_reversion", "factors": TRADING_FACTORS, "trader_id": "live-age"},
    )
    assert social.status_code == 200
    social_payload = social.json()
    assert store.get_decision(social_payload["decision_id"]) is not None

    webhook = client.post(
        "/api/trading/webhook/tradingview",
        json={
            "ticker": "AAPL",
            "action": "buy",
            "price": 150.25,
            "strategy": "RSI_Oversold",
            "category": "mean_reversion",
            "auto_score": True,
            "indicators": {"rsi": 28.5, "macd": -0.3, "atr": 2.1, "volume": 1_500_000},
        },
    )
    assert webhook.status_code == 200
    assert store.get_decision(webhook.json()["decision_id"]) is not None

    prescore = client.post(
        "/api/trading/prescore",
        json={"ticker": "MSFT", "category": "trend_following"},
    )
    assert prescore.status_code == 200
    assert int(store.count_decisions("trading")) == before + 3

    learn = client.post(
        "/api/learn",
        json={"decision_id": decision_id, "actual_action": score_payload["action"]},
    )
    assert learn.status_code == 200
    learned = store.get_decision(decision_id)
    assert learned is not None
    assert str(learned.get("status") or learned.get("outcome") or "").lower() == "confirmed"
    assert _has_outcome(learned)

    duplicate = client.post(
        "/api/learn",
        json={"decision_id": decision_id, "actual_action": score_payload["action"]},
    )
    assert duplicate.status_code == 400


def _require_live_env() -> None:
    required = {
        "TRADING_ACTIVE_GRAPH_BACKEND": "age",
        "TRADING_ACTIVE_AGE_TEST_MODE": "1",
        "TRADING_ACTIVE_AGE_GRAPH": "protocol_v2_test",
        "TRADING_ACTIVE_AGE_DOMAIN": "trading",
    }
    for key, expected in required.items():
        assert os.environ.get(key) == expected
    assert os.environ.get("TRADING_ACTIVE_AGE_DSN")
    assert os.environ.get("TRADING_ACTIVE_AGE_GRAPH") != "soc_graph"


def _has_outcome(decision: dict[str, Any]) -> bool:
    if str(decision.get("status") or decision.get("outcome") or "").lower() in {
        "confirmed",
        "overridden",
    }:
        return True
    if decision.get("outcome") is not None or decision.get("is_correct") is not None:
        return True
    outcomes = decision.get("outcomes")
    return isinstance(outcomes, list) and len(outcomes) == 1
