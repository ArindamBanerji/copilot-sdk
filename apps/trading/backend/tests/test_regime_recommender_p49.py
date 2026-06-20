from __future__ import annotations

from app.routers import data_import
from app.services.regime import RegimeService
from app.services.regime_recommender import RegimeRecommender
from conftest_helpers import seed_green_client


def _accuracy():
    return {
        "income_strategy": {"volatile": 0.78, "trending": 0.52, "ranging": 0.58},
        "trend_following": {"volatile": 0.45, "trending": 0.70, "ranging": 0.55},
    }


def _trades():
    trades = []
    for index in range(6):
        trades.append(
            {
                "trade_id": f"inc-v-win-{index}",
                "category": "income_strategy",
                "regime": "volatile",
                "pnl": 10,
                "factors": {"market_regime": 0.8, "position_sizing": 0.7},
            }
        )
    for index in range(2):
        trades.append(
            {
                "trade_id": f"inc-v-loss-{index}",
                "category": "income_strategy",
                "regime": "volatile",
                "pnl": -5,
                "factors": {"market_regime": 0.2, "position_sizing": 0.3},
            }
        )
    for index in range(5):
        trades.append({"trade_id": f"inc-t-win-{index}", "category": "income_strategy", "regime": "trending", "pnl": 10})
    for index in range(5):
        trades.append({"trade_id": f"inc-t-loss-{index}", "category": "income_strategy", "regime": "trending", "pnl": -5})
    return trades


def test_p49_edge_summary_compares_current_and_reference_regime():
    payload = RegimeRecommender().recommend("volatile", _accuracy(), trades=_trades(), current={"vix": 32.0})

    summary = payload["regime_edge_summary"]
    assert summary["category"] == "income_strategy"
    assert summary["comparison_regime"] == "trending"
    assert summary["edge_delta_pp"] == 26.0
    assert summary["sample_size_current"] == 8
    assert summary["sample_size_comparison"] == 10
    assert summary["status"] == "available"
    assert "observed income_strategy edge is larger at VIX 32" in summary["message"]
    assert "not a guarantee" in summary["message"]


def test_p49_edge_summary_insufficient_data_is_honest():
    payload = RegimeRecommender().recommend(
        "volatile",
        {"income_strategy": {"volatile": 0.8, "trending": 0.4}},
        trades=[
            {"category": "income_strategy", "regime": "volatile", "pnl": 1},
            {"category": "income_strategy", "regime": "trending", "pnl": -1},
        ],
    )

    summary = payload["regime_edge_summary"]
    assert summary["status"] == "insufficient_data"
    assert "insufficient data" in summary["message"]


def test_p49_sample_counts_include_inferred_regime_from_vix(monkeypatch):
    monkeypatch.setattr(RegimeService, "get_historical_vix", lambda self, trades: {"2026-01-01": 32.0, "2026-01-02": 18.0})
    trades = [
        {"category": "income_strategy", "entry_time": "2026-01-01T09:30:00", "pnl": 10},
        {"category": "income_strategy", "entry_time": "2026-01-02T09:30:00", "pnl": -5},
    ]

    payload = RegimeRecommender().recommend(
        "volatile",
        {"income_strategy": {"volatile": 1.0, "ranging": 0.0}},
        trades=trades,
        current={"vix": 32.0},
    )

    summary = payload["regime_edge_summary"]
    assert summary["sample_size_current"] == 1
    assert summary["sample_size_comparison"] == 1
    assert payload["data_quality"]["inferred_regime_rows"] == 2


def test_p49_edge_summary_uses_same_regime_inference_as_regime_accuracy(monkeypatch):
    monkeypatch.setattr(RegimeService, "get_historical_vix", lambda self, trades: {"2026-01-01": 32.0, "2026-01-02": 18.0})
    monkeypatch.setattr(RegimeService, "_batch_vix_lookup", lambda self, trades: {"2026-01-01": 32.0, "2026-01-02": 18.0})
    trades = [
        {"category": "income_strategy", "entry_time": "2026-01-01T09:30:00", "pnl": 10},
        {"category": "income_strategy", "entry_time": "2026-01-02T09:30:00", "pnl": -5},
    ]
    accuracy = RegimeService().get_regime_accuracy(trades)

    payload = RegimeRecommender().recommend("volatile", accuracy, trades=trades, current={"vix": 32.0})

    assert accuracy["income_strategy"]["volatile"] == 1.0
    assert payload["regime_edge_summary"]["sample_size_current"] == 1


def test_p49_unknown_regime_rows_warn_without_fabricating_samples(monkeypatch):
    monkeypatch.setattr(RegimeService, "get_historical_vix", lambda self, trades: {})
    payload = RegimeRecommender().recommend(
        "volatile",
        {"income_strategy": {"volatile": 0.8, "trending": 0.4}},
        trades=[{"category": "income_strategy", "entry_time": "2026-01-01T09:30:00", "pnl": 10}],
    )

    assert payload["regime_edge_summary"]["sample_size_current"] == 0
    assert payload["data_quality"]["unknown_regime_rows"] == 1
    assert any("lacked explicit or inferable regime" in warning for warning in payload["data_quality"]["warnings"])


def test_p49_sizing_recommendation_reduces_when_high_vol_or_sparse_data():
    payload = RegimeRecommender().recommend("volatile", _accuracy(), trades=_trades(), current={"vix": 32.0})

    sizing = payload["sizing_recommendation"]
    assert sizing["action"] in {"normal", "reduce"}
    assert sizing["suggested_size_multiplier"] <= 0.75
    assert sizing["max_size_multiplier"] <= 0.75
    assert sizing["advisory_only"] is True


def test_p49_sizing_recommendation_can_increase_small_when_edge_sample_supported():
    accuracy = {"income_strategy": {"trending": 0.78, "volatile": 0.52}}
    trades = []
    for index in range(8):
        trades.append({"category": "income_strategy", "regime": "trending", "pnl": 10})
    for index in range(10):
        trades.append({"category": "income_strategy", "regime": "volatile", "pnl": -5 if index < 5 else 5})
    payload = RegimeRecommender().recommend("trending", accuracy, trades=trades, current={"vix": 18.0})

    sizing = payload["sizing_recommendation"]
    assert sizing["action"] == "increase_small"
    assert sizing["suggested_size_multiplier"] == 1.1
    assert sizing["max_size_multiplier"] == 1.25
    assert sizing["min_sample_size_met"] is True


def test_p49_transition_alert_inactive_without_previous_regime():
    payload = RegimeRecommender().recommend("volatile", _accuracy(), trades=_trades())

    assert payload["transition_alert"]["active"] is False
    assert payload["transition_alert"]["reason"] == "previous_regime_unavailable"


def test_p49_transition_alert_active_when_regime_changes():
    payload = RegimeRecommender().recommend("volatile", _accuracy(), trades=_trades(), previous_regime="trending")

    alert = payload["transition_alert"]
    assert alert["active"] is True
    assert alert["previous_regime"] == "trending"
    assert alert["current_regime"] == "volatile"
    assert alert["message"] == "Regime changed; observed edge shifted."


def test_p49_transition_alert_reports_edge_shift():
    alert = RegimeRecommender().recommend("volatile", _accuracy(), trades=_trades(), previous_regime="trending")["transition_alert"]

    assert alert["edge_delta_pp"] is not None
    assert alert["old_recommendation"] is not None
    assert alert["new_recommendation"] is not None


def test_p49_transition_alert_inactive_when_previous_regime_has_no_data():
    payload = RegimeRecommender().recommend(
        "volatile",
        {"income_strategy": {"volatile": 0.78}},
        trades=[{"category": "income_strategy", "regime": "volatile", "pnl": 10}],
        previous_regime="trending",
    )

    alert = payload["transition_alert"]
    assert alert["active"] is False
    assert alert["reason"] == "previous_regime_data_unavailable"


def test_p49_transition_alert_does_not_fabricate_old_recommendation():
    alert = RegimeRecommender().recommend(
        "volatile",
        {"income_strategy": {"volatile": 0.78}},
        trades=[{"category": "income_strategy", "regime": "volatile", "pnl": 10}],
        previous_regime="trending",
    )["transition_alert"]

    assert alert["old_recommendation"] is None
    assert alert["message"] == "Regime changed, but previous-regime sample data is unavailable."


def test_p49_transition_alert_active_only_with_previous_and_current_data():
    alert = RegimeRecommender().recommend("volatile", _accuracy(), trades=_trades(), previous_regime="trending")["transition_alert"]

    assert alert["active"] is True
    assert alert["old_recommendation"] is not None
    assert alert["new_recommendation"] is not None


def test_p49_transition_alert_no_delta_when_comparison_unavailable():
    alert = RegimeRecommender().recommend(
        "volatile",
        {"income_strategy": {"volatile": 0.78}},
        trades=[{"category": "income_strategy", "regime": "volatile", "pnl": 10}],
        previous_regime="trending",
    )["transition_alert"]

    assert alert["active"] is False
    assert alert["edge_delta_pp"] is None


def test_p49_per_regime_dk_unavailable_not_fabricated():
    weights = RegimeRecommender().recommend("volatile", _accuracy(), trades=_trades())["regime_factor_weights"]

    assert weights["status"] == "unavailable"
    assert weights["factor_weights"] == []
    assert weights["source"] == "per_regime_dk_unavailable"


def test_p49_factor_influence_not_labeled_dk_if_derived():
    influence = RegimeRecommender().recommend("volatile", _accuracy(), trades=_trades())["regime_factor_influence"]

    assert influence["status"] == "available"
    assert influence["source"] == "journal_trades_observed_influence"
    assert "dk" not in influence["source"].lower()


def test_p49_accuracy_source_not_overclaimed_as_verified():
    payload = RegimeRecommender().recommend("volatile", _accuracy(), trades=_trades())

    assert payload["regime_edge_summary"]["source"] == "journal_trades"
    assert "verified accuracy" not in payload["recommendations"][0]["rationale"].lower()
    assert any("journal/PnL outcomes" in warning for warning in payload["product_honesty_warnings"])


def test_existing_regime_detail_response_compatible(client, monkeypatch):
    data_import._trade_store_ref.clear()
    data_import._trade_store_ref.extend(_trades())
    monkeypatch.setattr(RegimeService, "get_current_regime", lambda self: {"regime": "volatile", "vix": 32.0, "adx": 15.0, "source": "default"})
    monkeypatch.setattr(RegimeService, "get_regime_accuracy", lambda self, trades: _accuracy())
    seed_green_client(client)

    payload = client.get("/api/trading/regime/detail?previous_regime=trending").json()

    assert {"regime", "recommendations", "regime_transitions", "summary"} <= set(payload)
    assert "regime_edge_summary" in payload
    assert "sizing_recommendation" in payload
    assert payload["transition_alert"]["active"] is True


def test_no_scorer_graphstore_conservation_mutation():
    payload = RegimeRecommender().recommend("volatile", _accuracy(), trades=_trades())

    assert payload["sizing_recommendation"]["advisory_only"] is True
    assert "regime_factor_weights" in payload
    assert "product_honesty_warnings" in payload
