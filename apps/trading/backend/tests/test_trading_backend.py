from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app import context_router
from app.main import _build_seed_context
from copilot_sdk.evidence.provenance import Provenanced
from copilot_sdk.scoring.presets.trading import TradingPreset


TRADING_FACTORS = {
    "signal_alignment": 0.82,
    "market_regime": 0.88,
    "position_sizing": 0.76,
    "timing_quality": 0.34,
    "risk_reward_actual": 0.67,
    "emotional_indicator": 0.71,
    "signal_confidence": 0.50,
    "options_delta_exposure": 0.50,
    "options_iv_percentile": 0.50,
    "options_gamma_risk": 0.50,
}
TRADING_SEED_FACTORS = tuple(
    name
    for name in TRADING_FACTORS
    if name
    not in {
        "signal_confidence",
        "options_delta_exposure",
        "options_iv_percentile",
        "options_gamma_risk",
    }
)


class _FakeContextProvider:
    def __init__(
        self,
        *,
        market_snapshot: dict | None = None,
        tickers: dict[str, dict] | None = None,
    ):
        self._market_snapshot = market_snapshot
        self._tickers = tickers or {}

    def get_market_snapshot(self):
        return Provenanced(value=self._market_snapshot, source="live", as_of="2026-06-14T16:00:00Z")

    def get_ticker_snapshot(self, ticker: str):
        value = self._tickers.get(ticker)
        return Provenanced(value=value, source="live", as_of="2026-06-14T16:00:00Z")
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
REQUIRED_SEED_FIELDS = {
    "trade_id",
    "ticker",
    "direction",
    "category",
    "thesis_type",
    "timeframe",
    "research_checklist",
    "market_regime",
    "signal_alignment",
    "position_sizing",
    "timing_quality",
    "risk_reward_actual",
    "emotional_indicator",
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
    "provenance",
}


def _score(client, category: str = "trend_following") -> dict:
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


def test_seed_context_uses_current_trading_factor_width():
    preset = TradingPreset()
    context = _build_seed_context(
        {
            "factors": {
                "signal_alignment": 0.7,
                "market_regime": 0.8,
                "position_sizing": 0.6,
                "timing_quality": 0.5,
                "risk_reward_actual": 0.9,
                "emotional_indicator": 0.4,
            }
        }
    )

    assert tuple(context) == tuple(preset.shape.factor_names)
    assert len(context) == preset.shape.n_factors
    assert context["options_delta_exposure"] == 0.5
    assert context["options_iv_percentile"] == 0.5
    assert context["options_gamma_risk"] == 0.5


def test_market_snapshot(client, monkeypatch):
    monkeypatch.setattr(
        context_router,
        "_provider",
        _FakeContextProvider(
            market_snapshot={
                "spy": {"price": 555.2, "change_pct": 1.3},
                "vix": 14.8,
                "rsi": 58.2,
                "above_50ma": True,
                "volume_rank": 67,
                "sector": "Financial Services",
                "market_cap_b": 550.1,
            }
        ),
    )
    response = client.get("/api/context/market-snapshot")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "live"
    assert payload["provenance"]["source"] == "live"
    assert "spy" in payload
    assert "vix" in payload
    assert "sector" in payload
    assert payload["spy"]["change30dPct"] == 1.3


def test_market_snapshot_missing_file_returns_default(client, monkeypatch, tmp_path):
    monkeypatch.setattr(context_router, "_provider", _FakeContextProvider(market_snapshot=None))
    monkeypatch.setattr(context_router, "_DATA_DIR", tmp_path / "missing-data")
    monkeypatch.setattr(context_router, "_DEFAULT_DATA_DIR", tmp_path / "missing-default-data")

    response = client.get("/api/context/market-snapshot")

    assert response.status_code == 200
    payload = response.json()
    assert payload["regime"] == "ranging"
    assert payload["vix"]["price"] == 20.0
    assert payload["adx"] == 25.0
    assert payload["source"] == "default"
    assert payload["provenance"] == {"source": "fixture", "as_of": None}


def test_ticker_known(client, monkeypatch):
    monkeypatch.setattr(
        context_router,
        "_provider",
        _FakeContextProvider(
            tickers={
                "NVDA": {
                    "ticker": "NVDA",
                    "price": 900.0,
                    "change_30d_pct": 2.1,
                    "volume": 30_000_000,
                }
            }
        ),
    )
    response = client.get("/api/context/ticker/NVDA")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "NVDA"
    assert payload["price"] is not None
    assert payload["source"] == "live"
    assert payload["provenance"]["as_of"] == "2026-06-14T16:00:00Z"


def test_ticker_unknown(client, monkeypatch):
    monkeypatch.setattr(context_router, "_provider", _FakeContextProvider())
    response = client.get("/api/context/ticker/ZZZZ")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "ZZZZ"
    assert payload["price"] is None
    assert payload["source"] == "unknown"
    assert payload["provenance"] == {"source": "fixture", "as_of": None}


def test_ticker_enhanced_fields(client, monkeypatch):
    monkeypatch.setattr(
        context_router,
        "_provider",
        _FakeContextProvider(
            tickers={
                "MSFT": {
                    "ticker": "MSFT",
                    "price": 430.0,
                    "change_30d_pct": 1.4,
                    "volume": 22_000_000,
                    "sector": "Technology",
                    "rsi": 59.5,
                    "above_50ma": True,
                    "vol_rank_pctl": 71,
                    "market_cap_b": 3200.0,
                }
            }
        ),
    )
    response = client.get("/api/context/ticker/MSFT")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "MSFT"
    assert payload["sector"] == "Technology"
    assert isinstance(payload["rsi"], float)
    assert isinstance(payload["above_50ma"], bool)
    assert isinstance(payload["vol_rank_pctl"], int)
    assert payload["volRankPctl"] == payload["vol_rank_pctl"]
    assert payload["marketCapB"] == payload["market_cap_b"]
    assert payload["market_cap_b"] > 0


def test_trade_metadata_store_and_retrieve(client):
    payload = {
        "decision_id": "decision-1",
        "ticker": "NVDA",
        "direction": "strong_execution",
        "thesis": "breakout with improving breadth",
        "research": "earnings and volume reviewed",
        "signal_alignment": 0.82,
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


def test_trade_metadata_malformed_file_returns_empty(client, monkeypatch, tmp_path):
    malformed_dir = tmp_path / "malformed-data"
    malformed_dir.mkdir()
    (malformed_dir / "trade_metadata.json").write_text('{"broken": true}}', encoding="utf-8")
    monkeypatch.setattr(context_router, "_DATA_DIR", malformed_dir)
    monkeypatch.setattr(context_router, "_DEFAULT_DATA_DIR", tmp_path / "missing-default-data")

    response = client.get("/api/context/trade-metadata")

    assert response.status_code == 200
    assert response.json() == {}


def test_trade_metadata_requires_decision_id(client):
    response = client.post("/api/context/trade-metadata", json={"ticker": "NVDA"})

    assert response.status_code == 400
    assert "decision_id" in response.json()["detail"]


def test_trade_metadata_v2_fields(client):
    payload = {
        "decision_id": "decision-v2",
        "ticker": "MSFT",
        "direction": "strong_execution",
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
        assert trade["category"] in {"trend_following", "mean_reversion", "event_driven", "income_strategy", "scalp_intraday"}
        assert trade["direction"] in {"strong_execution", "partial_execution", "poor_execution"}
        assert trade["action_taken"] == trade["direction"]
        assert len(trade["research_checklist"]) == 5
        assert all(isinstance(item, bool) for item in trade["research_checklist"])
        for factor in TRADING_SEED_FACTORS:
            assert 0.0 <= trade[factor] <= 1.0


def test_auto_seed_empty_db(tmp_path):
    from app.main import create_app

    db_path = tmp_path / "trading_seeded.db"
    with TestClient(create_app(db_path=db_path, demo_bundle_path=False)) as startup_client:
        assert startup_client.get("/health").status_code == 200

    expected_verified, expected_correct = _fixture_outcome_counts(DATA_DIR / "trading_seed_v2.json")
    assert _count_decisions(db_path, "trading") == 40
    assert _count_verified(db_path, "trading") == expected_verified
    assert _count_correct(db_path, "trading") == expected_correct


def test_auto_seed_skips_populated(tmp_path):
    from app.main import create_app
    from copilot_sdk.graph import SQLiteGraphStore

    db_path = tmp_path / "trading_populated.db"
    store = SQLiteGraphStore(db_path, domain="trading")
    try:
        _save_proxy_decision(store, "existing")
    finally:
        store.close()

    with TestClient(create_app(db_path=db_path, demo_bundle_path=False)) as startup_client:
        assert startup_client.get("/health").status_code == 200

    assert _count_decisions(db_path, "trading") == 1


def test_ci_data_dir_creates_db(tmp_path, monkeypatch):
    from app.main import create_app

    data_dir = tmp_path / "ci-data"
    monkeypatch.setenv("CI_DATA_DIR", str(data_dir))
    with TestClient(create_app(demo_bundle_path=False)) as startup_client:
        assert startup_client.get("/health").status_code == 200

    db_path = data_dir / "trading.db"
    assert db_path.exists()
    assert _count_decisions(db_path, "trading") == 40
    assert _count_verified(db_path, "trading") == _fixture_outcome_counts(DATA_DIR / "trading_seed_v2.json")[0]


def test_explicit_db_path_wins(tmp_path, monkeypatch):
    from app.main import create_app

    ci_dir = tmp_path / "ci-data"
    explicit_db = tmp_path / "explicit.db"
    monkeypatch.setenv("CI_DATA_DIR", str(ci_dir))

    with TestClient(create_app(db_path=explicit_db, demo_bundle_path=False)) as startup_client:
        assert startup_client.get("/health").status_code == 200

    assert explicit_db.exists()
    assert not (ci_dir / "trading.db").exists()
    assert _count_decisions(explicit_db, "trading") == 40


def test_no_env_uses_explicit_fallback(tmp_path, monkeypatch):
    from app.main import create_app

    monkeypatch.delenv("CI_DATA_DIR", raising=False)
    db_path = tmp_path / "fallback.db"
    with TestClient(create_app(db_path=db_path, demo_bundle_path=False)) as startup_client:
        assert startup_client.get("/health").status_code == 200

    assert db_path.exists()
    assert _count_decisions(db_path, "trading") == 40


def test_startup_records_l5_source_status(tmp_path):
    from app.main import create_app

    with TestClient(create_app(db_path=tmp_path / "l5-status.db", demo_bundle_path=False)) as client:
        assert client.get("/health").status_code == 200
        status = client.app.state.l5_startup_status
    assert status["dk_source"] in {"missing", "l5", "error", "deferred"}
    assert status["welford_source"] in {"missing", "l5", "error"}
    assert status["centroid_source"] in {"missing", "l5", "error", "deferred"}
    assert status["conservation_source"] in {"missing", "l5", "error"}


def test_l5_startup_restore_runs_after_seed_setup(tmp_path, monkeypatch):
    from app import main as app_main

    calls: list[str] = []

    # MOCK-OK: this test is only about startup sequencing. Real seed/restore
    # behavior is covered by integration tests, and these sentinels keep the
    # ordering assertion focused.
    def fake_seed(_store):
        calls.append("seed")

    def fake_restore(*, domain, scorer, learning_store, welford_tracker=None):
        calls.append("restore")
        assert domain == "trading"
        assert scorer is not None
        assert learning_store is not None
        assert welford_tracker is not None
        return {
            "dk_source": "missing",
            "welford_source": "missing",
            "centroid_source": "missing",
            "conservation_source": "missing",
            "welford_tracker": None,
        }

    monkeypatch.setattr(app_main, "_auto_seed_if_needed", fake_seed)
    monkeypatch.setattr(app_main, "restore_l5_runtime_state", fake_restore)

    with TestClient(app_main.create_app(db_path=tmp_path / "ordered.db", demo_bundle_path=False)) as client:
        assert client.get("/health").status_code == 200
        status = client.app.state.l5_startup_status

    assert calls == ["seed", "restore"]
    assert status["dk_source"] == "missing"


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
            "category": "trend_following",
            "signal_alignment": 0.6,
            "market_regime": 0.8,
            "position_sizing": 0.7,
            "timing_quality": 0.5,
            "risk_reward_actual": 0.4,
            "emotional_indicator": 0.7,
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
            "category": "trend_following",
            "signal_alignment": 0.6,
            "market_regime": 0.8,
            "position_sizing": 0.7,
            "timing_quality": 0.5,
            "risk_reward_actual": 0.4,
            "emotional_indicator": 0.7,
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

    assert payload["category"] == "trend_following"
    assert payload["action"] in {"strong_execution", "partial_execution", "poor_execution", "skip_recommended"}
    assert payload["decision_id"].startswith("TRD-")
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
    assert learn["reward"] >= 0
    assert learn["engine"]["gae"] == "gae.profile_scorer.ProfileScorer"


def test_conservation_status_returns_live_counts(client):
    before = client.get("/api/conservation/status").json()
    assert before["total_decisions"] == 0
    assert before["verified_count"] == 0
    assert before["correct_count"] == 0
    assert before["penalty_ratio"] == TradingPreset().penalty_ratio

    score = _score(client)
    after_score = client.get("/api/conservation/status").json()
    # Conservation V is verified-only; pending score writes are audit/store
    # activity but do not increase total_decisions.
    assert after_score["total_decisions"] == 0
    assert after_score["verified_count"] == 0
    assert after_score["correct_count"] == 0

    _learn(client, score["decision_id"], score["action"])
    payload = client.get("/api/conservation/status").json()
    assert payload["domain"] == "trading"
    assert payload["total_decisions"] == 1
    assert payload["verified_count"] == 1
    assert payload["correct_count"] == 1
    assert payload["penalty_ratio"] == TradingPreset().penalty_ratio


def test_in_memory_scoring_and_conservation_share_proxy_store():
    from app.main import create_app

    with TestClient(create_app(db_path=":memory:", demo_bundle_path=False)) as memory_client:
        score = _score(memory_client)
        payload = memory_client.get("/api/conservation/status").json()
        learn = _learn(memory_client, score["decision_id"], score["action"])
        after_learn = memory_client.get("/api/conservation/status").json()

    assert score["decision_id"].startswith("TRD-")
    assert learn["decision_id"] == score["decision_id"]
    assert payload["domain"] == "trading"
    assert payload["total_decisions"] == 0
    assert payload["verified_count"] == 0
    assert after_learn["total_decisions"] == 1
    assert after_learn["verified_count"] == 1


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
    from copilot_sdk.graph import SQLiteGraphStore

    db_path = tmp_path / "graph.sqlite"
    store = SQLiteGraphStore(db_path, domain="trading")
    try:
        _save_proxy_decision(store, "d-1")
        _save_proxy_decision(store, "d-2")
        store.write_outcome(
            decision_id="d-1",
            actual_action="strong_execution",
            is_correct=True,
            metadata={"actual_index": 0},
        )
    finally:
        store.close()

    assert _graph_store(str(db_path)).count_verified("trading") == 1


def test_graph_store_count_correct(tmp_path):
    from app.main import _graph_store
    from copilot_sdk.graph import SQLiteGraphStore

    db_path = tmp_path / "graph.sqlite"
    store = SQLiteGraphStore(db_path, domain="trading")
    try:
        _save_proxy_decision(store, "d-1")
        _save_proxy_decision(store, "d-2")
        store.write_outcome(
            decision_id="d-1",
            actual_action="strong_execution",
            is_correct=True,
            metadata={"actual_index": 0},
        )
        store.write_outcome(
            decision_id="d-2",
            actual_action="partial_execution",
            is_correct=False,
            metadata={"actual_index": 1},
        )
    finally:
        store.close()

    assert _graph_store(str(db_path)).count_correct("trading") == 1


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
    store.write_decision(
        "trading",
        category="trend_following",
        action="strong_execution",
        confidence=0.8,
        factors=TRADING_FACTORS,
        metadata={
            "decision_id": decision_id,
            "category_index": 0,
            "factor_vector": list(TRADING_FACTORS.values()),
            "recommended_index": 0,
            "probabilities": [0.8, 0.1, 0.1, 0.0],
        },
    )


def _seed_verified_history(db_path: Path, total: int) -> None:
    from copilot_sdk.graph import SQLiteGraphStore

    override_count = 30
    alternate_actions = [("partial_execution", 1), ("poor_execution", 2)]
    assert total >= override_count

    store = SQLiteGraphStore(db_path, domain="trading")
    try:
        for index in range(total):
            decision_id = f"seed-{index}"
            _save_proxy_decision(store, decision_id)
            if index < override_count:
                actual_action, actual_index = alternate_actions[
                    index % len(alternate_actions)
                ]
            else:
                actual_action, actual_index = "strong_execution", 0
            store.write_outcome(
                decision_id=decision_id,
                actual_action=actual_action,
                is_correct=True,
                metadata={"actual_index": actual_index},
            )
    finally:
        store.close()


def _count_decisions(db_path: Path, domain: str) -> int:
    from copilot_sdk.graph import SQLiteGraphStore

    store = SQLiteGraphStore(db_path, domain=domain)
    try:
        return store.count_decisions(domain)
    finally:
        store.close()


def _count_verified(db_path: Path, domain: str) -> int:
    from copilot_sdk.graph import SQLiteGraphStore

    store = SQLiteGraphStore(db_path, domain=domain)
    try:
        return store.count_verified(domain)
    finally:
        store.close()


def _count_correct(db_path: Path, domain: str) -> int:
    from copilot_sdk.graph import SQLiteGraphStore

    store = SQLiteGraphStore(db_path, domain=domain)
    try:
        return store.count_correct(domain)
    finally:
        store.close()


def _fixture_outcome_counts(path: Path) -> tuple[int, int]:
    seed = json.loads(path.read_text(encoding="utf-8"))
    verified = sum(1 for entry in seed if "is_correct" in entry)
    correct = sum(1 for entry in seed if bool(entry.get("is_correct")))
    return verified, correct
