from __future__ import annotations

import json
from pathlib import Path

from app import context_router
from copilot_sdk.scoring.presets.trading import TradingPreset


TRADING_FACTORS = {
    "conviction": 0.82,
    "research_depth": 0.88,
    "technical_signal": 0.76,
    "position_size": 0.34,
    "time_horizon": 0.67,
    "market_regime": 0.71,
    "signal_confidence": 0.50,
}
TRADING_SEED_FACTORS = tuple(name for name in TRADING_FACTORS if name != "signal_confidence")
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
REQUIRED_SEED_FIELDS = {
    "trade_id",
    "ticker",
    "direction",
    "category",
    "thesis_type",
    "timeframe",
    "research_checklist",
    "research_depth",
    "conviction",
    "technical_signal",
    "position_size",
    "time_horizon",
    "market_regime",
    "shares",
    "entry_price",
    "portfolio_value",
    "stop_loss",
    "target",
    "rr_ratio",
    "exit_price",
    "pnl_pct",
    "pnl_dollars",
    "hold_days",
    "outcome",
    "is_correct",
    "day_of_week",
    "date",
    "action_taken",
    "vix_at_entry",
}


def _score(client, category: str = "equity_long") -> dict:
    response = client.post(
        "/api/score",
        json={"category": category, "factors": TRADING_FACTORS},
    )
    assert response.status_code == 200
    return response.json()


def _learn(client, decision_id: str, actual_action: str) -> dict:
    response = client.post(
        "/api/learn",
        json={"decision_id": decision_id, "actual_action": actual_action},
    )
    assert response.status_code == 200
    return response.json()


def _load_data(filename: str, root: Path = DATA_DIR):
    return json.loads((root / filename).read_text(encoding="utf-8"))


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["domain"] == "trading"
    assert "copilot_sdk.scoring" in payload["engine"]
    assert "gae.profile_scorer" in payload["engine"]


def test_api_health_returns_phase_alpha_and_engine(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["phase"] in {"A", "B"}
    assert isinstance(payload["alpha"], (int, float))
    assert payload["engine"]["scoring"] == "copilot_sdk.scoring.CompoundingScorer"
    assert payload["engine"]["gae"] == "gae.profile_scorer.ProfileScorer"


def test_market_snapshot(client):
    response = client.get("/api/context/market-snapshot")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "cached"
    assert "spy" in payload
    assert "vix" in payload
    assert "sector" in payload


def test_ticker_known(client):
    response = client.get("/api/context/ticker/NVDA")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "NVDA"
    assert payload["price"] is not None
    assert payload["source"] == "cached"


def test_ticker_unknown(client):
    response = client.get("/api/context/ticker/ZZZZ")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "ZZZZ"
    assert payload["price"] is None
    assert payload["source"] == "unknown"


def test_ticker_enhanced_fields(client):
    response = client.get("/api/context/ticker/MSFT")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "MSFT"
    assert payload["sector"] == "Technology"
    assert isinstance(payload["rsi"], float)
    assert isinstance(payload["above_50ma"], bool)
    assert isinstance(payload["vol_rank_pctl"], int)
    assert payload["market_cap_b"] > 0


def test_trade_metadata_store_and_retrieve(client):
    payload = {
        "decision_id": "decision-1",
        "ticker": "NVDA",
        "direction": "buy",
        "thesis": "breakout with improving breadth",
        "research": "earnings and volume reviewed",
        "conviction": 0.82,
        "horizon": "swing",
    }

    created = client.post("/api/context/trade-metadata", json=payload)
    assert created.status_code == 201
    assert created.json()["decision_id"] == "decision-1"

    response = client.get("/api/context/trade-metadata")
    assert response.status_code == 200
    metadata = response.json()
    assert metadata["decision-1"]["ticker"] == "NVDA"
    assert metadata["decision-1"]["horizon"] == "swing"


def test_trade_metadata_requires_decision_id(client):
    response = client.post("/api/context/trade-metadata", json={"ticker": "NVDA"})

    assert response.status_code == 400
    assert "decision_id" in response.json()["detail"]


def test_trade_metadata_v2_fields(client):
    payload = {
        "decision_id": "decision-v2",
        "ticker": "MSFT",
        "direction": "buy",
        "thesis_type": "momentum",
        "timeframe": "position",
        "research_checklist": [True, True, True, True, False],
        "shares": 88,
        "entry_price": 412,
        "portfolio_value": 250000,
        "exposure_pct": 0.06,
        "stop_loss": 398,
        "target": 440,
        "rr_ratio": 2.0,
        "exit_price": None,
        "pnl_pct": None,
        "pnl_dollars": None,
        "hold_days": None,
        "outcome": None,
    }

    created = client.post("/api/context/trade-metadata", json=payload)
    assert created.status_code == 201
    assert created.json()["metadata"] == payload

    response = client.get("/api/context/trade-metadata")
    assert response.status_code == 200
    metadata = response.json()["decision-v2"]
    for key, value in payload.items():
        assert metadata[key] == value


def test_seed_v2_exists(client):
    seed = _load_data("trading_seed_v2.json", client.app.state.trading_data_dir)

    assert len(seed) == 40
    assert sum(1 for trade in seed if trade["exit_price"] is None) == 3
    for trade in seed:
        assert set(trade) == REQUIRED_SEED_FIELDS
        assert trade["category"] in {"equity_long", "equity_short", "crypto_spot", "options", "etf"}
        assert trade["direction"] in {"buy", "hold", "sell"}
        assert trade["action_taken"] == trade["direction"]
        assert len(trade["research_checklist"]) == 5
        assert all(isinstance(item, bool) for item in trade["research_checklist"])
        for factor in TRADING_SEED_FACTORS:
            assert 0.0 <= trade[factor] <= 1.0


def test_analytics(client):
    response = client.get("/api/context/analytics")

    assert response.status_code == 200
    payload = response.json()
    assert {
        "contrast_card",
        "counterfactual",
        "calendar_heatmap",
        "thesis_breakdown",
        "regime_analysis",
        "research_impact",
        "portfolio_concentration",
        "rolling_10",
        "risk_management",
        "portfolio_summary",
    }.issubset(payload)
    assert "aligned" in payload["contrast_card"]
    assert "misaligned" in payload["contrast_card"]
    assert payload["counterfactual"]["dollars_saved"] > 0


def test_analytics_consistent_with_seed_v2(client):
    data_dir = client.app.state.trading_data_dir
    seed = _load_data("trading_seed_v2.json", data_dir)
    analytics = _load_data("analytics_cache.json", data_dir)
    closed = [trade for trade in seed if trade["exit_price"] is not None]
    open_positions = [trade for trade in seed if trade["exit_price"] is None]
    wins = sum(1 for trade in closed if trade["outcome"] == "win")
    expected_win_rate = round(wins / len(closed), 4)

    assert len(seed) == 40
    assert analytics["open_positions"] == len(open_positions)
    assert analytics["closed_trades"] == len(closed)
    assert analytics["portfolio_summary"]["open_positions"] == len(open_positions)
    assert analytics["portfolio_summary"]["closed_trades"] == len(closed)
    assert analytics["portfolio_summary"]["win_rate"] == expected_win_rate

    calendar_total = sum(day["closed"] for day in analytics["calendar_heatmap"].values())
    assert calendar_total == len(closed)


def test_similar_trades(client):
    response = client.get(
        "/api/context/similar",
        params={
            "category": "equity_long",
            "conviction": 0.6,
            "research_depth": 0.8,
            "technical_signal": 0.7,
            "position_size": 0.5,
            "time_horizon": 0.4,
            "market_regime": 0.7,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= len(payload["similar"]) > 0
    similarities = [item["similarity"] for item in payload["similar"]]
    assert similarities == sorted(similarities, reverse=True)
    assert all(similarity > 0.85 for similarity in similarities)
    for item in payload["similar"]:
        assert "ticker" in item
        assert "pnl_pct" in item


def test_v2_context_uses_temp_data_without_default_fallback(client, monkeypatch, tmp_path):
    monkeypatch.setattr(context_router, "_DEFAULT_DATA_DIR", tmp_path / "missing-default-data")

    analytics_response = client.get("/api/context/analytics")
    assert analytics_response.status_code == 200
    assert analytics_response.json()["source"] == "computed_from_trading_seed_v2"

    similar_response = client.get(
        "/api/context/similar",
        params={
            "category": "equity_long",
            "conviction": 0.6,
            "research_depth": 0.8,
            "technical_signal": 0.7,
            "position_size": 0.5,
            "time_horizon": 0.4,
            "market_regime": 0.7,
        },
    )
    assert similar_response.status_code == 200
    assert similar_response.json()["count"] > 0


def test_portfolio_summary_matches_analytics(client):
    portfolio_response = client.get("/api/context/portfolio-summary")
    analytics_response = client.get("/api/context/analytics")

    assert portfolio_response.status_code == 200
    assert analytics_response.status_code == 200
    assert portfolio_response.json() == analytics_response.json()["portfolio_summary"]


def test_score_via_sdk_router(client):
    payload = _score(client)

    assert payload["category"] == "equity_long"
    assert payload["action"] in {"buy", "hold", "sell", "skip_recommended"}
    assert 0.0 <= payload["confidence"] <= 1.0
    assert len(payload["probabilities"]) == 4
    assert payload["engine"]["scoring"] == "copilot_sdk.scoring.CompoundingScorer"


def test_learn_returns_reward(client):
    score = _score(client)
    learn = _learn(client, score["decision_id"], score["action"])

    assert learn["decision_id"] == score["decision_id"]
    assert "reward" in learn
    assert "previous_reward" in learn
    assert "reward_multiplier" in learn
    assert learn["reward"] > 0
    assert learn["engine"]["gae"] == "gae.profile_scorer.ProfileScorer"


def test_conservation_status_returns_live_counts(client):
    before = client.get("/api/conservation/status").json()
    assert before["total_decisions"] == 0
    assert before["verified_count"] == 0
    assert before["correct_count"] == 0
    assert before["penalty_ratio"] == TradingPreset().penalty_ratio

    score = _score(client)
    after_score = client.get("/api/conservation/status").json()
    assert after_score["total_decisions"] == 1
    assert after_score["verified_count"] == 0
    assert after_score["correct_count"] == 0

    _learn(client, score["decision_id"], score["action"])
    payload = client.get("/api/conservation/status").json()
    assert payload["domain"] == "trading"
    assert payload["total_decisions"] == 1
    assert payload["verified_count"] == 1
    assert payload["correct_count"] == 1
    assert payload["penalty_ratio"] == TradingPreset().penalty_ratio


def test_self_computation_centroid_history_available(client):
    response = client.get("/api/self/centroid-history")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) >= {"checkpoints", "total"}
    assert isinstance(payload["checkpoints"], list)


def test_self_computation_accuracy_available(client):
    response = client.get("/api/self/accuracy-by-category")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) >= {"categories", "threshold", "overall_verified"}
    assert isinstance(payload["categories"], list)


def test_self_computation_decisions_available(client):
    response = client.get("/api/self/decisions")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) >= {"decisions", "total"}
    assert isinstance(payload["decisions"], list)


def test_self_computation_audit_trail_available(client):
    response = client.get("/api/self/audit-trail")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) >= {"trails", "total"}
    assert isinstance(payload["trails"], list)


def test_self_computation_mounted_at_api_self(client):
    response = client.get("/api/self/decisions?limit=1")

    assert response.status_code == 200
    assert "decisions" in response.json()


def test_graph_store_count_verified(tmp_path):
    from app.main import _graph_store
    from copilot_sdk.scoring.storage import DecisionStore

    db_path = tmp_path / "graph.sqlite"
    store = DecisionStore(db_path)
    try:
        _save_proxy_decision(store, "d-1")
        _save_proxy_decision(store, "d-2")
        store.save_outcome(
            decision_id="d-1",
            actual_action="buy",
            actual_index=0,
            is_correct=True,
        )
    finally:
        store.close()

    assert _graph_store(str(db_path)).count_verified() == 1


def test_graph_store_count_correct(tmp_path):
    from app.main import _graph_store
    from copilot_sdk.scoring.storage import DecisionStore

    db_path = tmp_path / "graph.sqlite"
    store = DecisionStore(db_path)
    try:
        _save_proxy_decision(store, "d-1")
        _save_proxy_decision(store, "d-2")
        store.save_outcome(
            decision_id="d-1",
            actual_action="buy",
            actual_index=0,
            is_correct=True,
        )
        store.save_outcome(
            decision_id="d-2",
            actual_action="hold",
            actual_index=1,
            is_correct=False,
        )
    finally:
        store.close()

    assert _graph_store(str(db_path)).count_correct() == 1


def test_fingerprint(client):
    # Strict conservation requires enough verified/correct history before
    # additional learns mutate centroids. theta_min = 23.53 / override_count;
    # at q=1, >=24 correct overrides are required. Seed 30 for margin.
    _seed_verified_history(
        Path(client.app.state.trading_data_dir).parent / "trading_test.db",
        total=50,
    )

    for _ in range(3):
        score = _score(client)
        learn = _learn(client, score["decision_id"], score["action"])
        assert learn.get("status") != "paused"

    response = client.get("/api/fingerprint")

    assert response.status_code == 200
    payload = response.json()
    assert payload["engine"]["scoring"] == "copilot_sdk.scoring.CompoundingScorer"
    assert payload["decisions_analyzed"] >= 16
    assert {factor["name"] for factor in payload["factors"]} == set(TRADING_FACTORS)


def _save_proxy_decision(store, decision_id: str) -> None:
    store.save_decision(
        decision_id=decision_id,
        domain="trading",
        category="equity_long",
        category_index=0,
        factors=TRADING_FACTORS,
        factor_vector=list(TRADING_FACTORS.values()),
        recommended_action="buy",
        recommended_index=0,
        confidence=0.8,
        probabilities=[0.8, 0.1, 0.1, 0.0],
    )


def _seed_verified_history(db_path: Path, total: int) -> None:
    from copilot_sdk.scoring.storage import DecisionStore

    override_count = 30
    alternate_actions = [("hold", 1), ("sell", 2)]
    assert total >= override_count

    store = DecisionStore(db_path)
    try:
        for index in range(total):
            decision_id = f"seed-{index}"
            _save_proxy_decision(store, decision_id)
            if index < override_count:
                actual_action, actual_index = alternate_actions[
                    index % len(alternate_actions)
                ]
            else:
                actual_action, actual_index = "buy", 0
            store.save_outcome(
                decision_id=decision_id,
                actual_action=actual_action,
                actual_index=actual_index,
                is_correct=True,
            )
    finally:
        store.close()
