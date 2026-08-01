from __future__ import annotations

import pytest

from app.main import _seed_metadata
from app.services.regime_monitor import RegimeMonitor
from app.services.regime_scoring import apply_conservation_tightening
from app.services.trading_evolver import TradingAgentEvolver, TRADING_FACTOR_NAMES


FACTORS = {
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


class BaselineScorer:
    graph_store = object()

    def predict(self, decision):
        return decision.get("recommended_action")


def _score(client, metadata=None):
    response = client.post(
        "/api/score",
        json={"category": "trend_following", "factors": FACTORS, "metadata": metadata or {}},
    )
    assert response.status_code == 200
    return response.json()


def _learn(client, decision_id: str, action: str):
    response = client.post(
        "/api/learn",
        json={"decision_id": decision_id, "actual_action": action},
    )
    assert response.status_code == 200
    return response.json()


def _seed_monitor_break(monitor: RegimeMonitor) -> None:
    for _ in range(10):
        monitor.record("trending")
    assert monitor.record("volatile") == "regime_break"


def test_score_includes_regime_context(client):
    payload = _score(client, {"vix_at_entry": 18.0, "trend_strength": 30.0})

    assert "regime_context" in payload
    assert payload["regime_context"]["regime"] in {"trending", "ranging", "volatile"}


def test_regime_context_has_required_fields(client):
    payload = _score(client, {"vix_at_entry": 35.0, "trend_strength": 12.0})

    assert {"regime", "hurst", "vol_state", "vix_percentile"} <= set(payload["regime_context"])


def test_regime_metadata_persisted_with_decision(client):
    payload = _score(client, {"vix_at_entry": 18.0, "trend_strength": 30.0})
    _learn(client, payload["decision_id"], payload["action"])

    store = client.app.state.trading_selected_graph_store
    decision = store.get_decision(payload["decision_id"], domain="trading")

    assert decision is not None
    metadata = decision["metadata"]
    assert metadata["regime_metadata"]["regime"] == payload["regime_context"]["regime"]
    assert "tagged_at" in metadata["regime_metadata"]


def test_regime_monitor_detects_break():
    monitor = RegimeMonitor(window=3)
    monitor.record("trending")
    monitor.record("trending")
    monitor.record("trending")

    assert monitor.record("volatile") == "regime_break"
    assert monitor.is_regime_break is True
    assert monitor.previous_regime == "trending"
    assert monitor.current_regime == "volatile"


def test_regime_monitor_no_break_in_stable():
    monitor = RegimeMonitor(window=3)

    assert monitor.record("ranging") is None
    assert monitor.record("ranging") is None
    assert monitor.record("ranging") is None
    assert monitor.is_regime_break is False


def test_regime_break_tightens_theta_min():
    monitor = RegimeMonitor()
    _seed_monitor_break(monitor)

    payload = apply_conservation_tightening({"theta_min": 10.0, "signal": 8.0}, monitor)

    assert payload["theta_min"] == pytest.approx(13.0)
    assert payload["headroom"] == pytest.approx(-5.0)


def test_theta_min_restored_after_stabilization():
    monitor = RegimeMonitor(stabilize_after=3)
    _seed_monitor_break(monitor)
    monitor.record("volatile")
    monitor.record("volatile")

    payload = apply_conservation_tightening({"theta_min": 10.0, "signal": 8.0}, monitor)

    assert monitor.is_regime_break is False
    assert payload["theta_min"] == 10.0


def test_ae_deferred_during_regime_break(caplog):
    evolver = TradingAgentEvolver(
        baseline_scorer=BaselineScorer(),
        store_factory=lambda: object(),
        factor_names=TRADING_FACTOR_NAMES,
        conservation_provider=lambda: {"status": "GREEN"},
        regime_break_provider=lambda: True,
    )

    result = evolver.check_promotion("variant-1")

    assert result["reason"] == "regime_break_deferred"
    assert "AE promotion deferred: regime break active" in caplog.text


def test_ae_resumes_after_stabilization():
    active = {"value": True}
    evolver = TradingAgentEvolver(
        baseline_scorer=BaselineScorer(),
        store_factory=lambda: object(),
        factor_names=TRADING_FACTOR_NAMES,
        conservation_provider=lambda: {"status": "GREEN"},
        regime_break_provider=lambda: active["value"],
    )
    assert evolver.check_promotion("variant-1")["reason"] == "regime_break_deferred"

    active["value"] = False

    assert evolver.check_promotion("variant-1")["reason"] == "insufficient_batches"


def test_regime_status_endpoint_returns_200(client):
    response = client.get("/api/trading/regime-status")

    assert response.status_code == 200
    assert "regime_break_active" in response.json()


def test_regime_status_shows_restrictions(client):
    monitor = client.app.state.trading_regime_monitor
    _seed_monitor_break(monitor)

    payload = client.get("/api/trading/regime-status").json()

    assert payload["autonomy_level"] == "restricted"
    assert "theta_min tightened 30%" in payload["restrictions"]
    assert "AE promotions deferred" in payload["restrictions"]


def test_sizing_paused_during_regime_break(client):
    monitor = client.app.state.trading_regime_monitor
    _seed_monitor_break(monitor)

    payload = client.get("/api/trading/regime/detail").json()

    assert payload["sizing_recommendation"]["paused"] is True
    assert payload["sizing_recommendation"]["action"] == "paused"


def test_regime_break_logged(client, caplog):
    monitor = client.app.state.trading_regime_monitor
    for _ in range(10):
        _score(client, {"vix_at_entry": 18.0, "trend_strength": 30.0})

    _score(client, {"vix_at_entry": 35.0, "trend_strength": 10.0})

    assert monitor.is_regime_break is True
    assert "Regime break detected: trending -> volatile" in caplog.text


def test_preseed_regime_metadata_present():
    metadata = _seed_metadata(
        {
            "trade_id": "seed-1",
            "vix_at_entry": 18.0,
            "trend_strength": 30.0,
        },
        1,
        FACTORS,
    )

    assert {"regime", "hurst", "vol_state", "vix_percentile", "tagged_at"} <= set(metadata["regime_metadata"])
