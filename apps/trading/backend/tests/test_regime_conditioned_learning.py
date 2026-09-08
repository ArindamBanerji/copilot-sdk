from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from app.services.regime_monitor import RegimeMonitor
from app.services.regime_scoring import TradingRegimeScorerProxy


def _factors() -> dict[str, float]:
    return {
        "signal_alignment": 0.7,
        "market_regime": 0.5,
        "position_sizing": 0.6,
        "timing_quality": 0.6,
        "risk_reward_actual": 0.7,
        "emotional_indicator": 0.2,
        "signal_confidence": 0.8,
        "options_delta_exposure": 0.5,
        "options_iv_percentile": 0.5,
        "options_gamma_risk": 0.2,
    }


def test_rc_10_trading_score_exposes_conditioned_parameters(client: Any) -> None:
    response = client.post(
        "/api/score",
        json={"category": "trend_following", "factors": _factors(), "metadata": {"vix": 35.0}},
    )
    assert response.status_code == 200, response.json()
    payload = response.json()
    assert payload["regime_context"]["regime"] == "volatile"
    assert payload["regime_parameters"]["penalty_ratio"] == 6.0
    adjusted = client.app.state.trading_regime_conditioning.conservation_status_adjuster(
        {"theta_min": 2.0, "signal": 3.0, "penalty_ratio": 3.0}
    )
    assert adjusted["regime"] == "volatile"
    assert adjusted["theta_min"] == 3.0
    assert adjusted["penalty_ratio"] == 6.0
    assert adjusted["status"] == "GREEN"
    assert adjusted["passed"] is True


def test_regime_adjustment_recomputes_status_from_adjusted_theta(client: Any) -> None:
    client.post(
        "/api/score",
        json={"category": "trend_following", "factors": _factors(), "metadata": {"vix": 35.0}},
    )

    adjusted = client.app.state.trading_regime_conditioning.conservation_status_adjuster(
        {"theta_min": 2.0, "signal": 2.5, "status": "GREEN", "passed": True, "penalty_ratio": 3.0}
    )

    assert adjusted["base_theta_min"] == 2.0
    assert adjusted["theta_min"] == 3.0
    assert adjusted["headroom"] == -0.5
    assert adjusted["status"] == "RED"
    assert adjusted["conservation_status"] == "RED"
    assert adjusted["passed"] is False


def test_rc_11_observation_only_controls_remain_available(client: Any) -> None:
    response = client.post(
        "/api/score",
        json={"category": "trend_following", "factors": _factors(), "metadata": {"vix": 35.0}},
    )
    assert response.status_code == 200
    assert response.json()["regime_parameters"]["regime"] == "volatile"


def test_adjusted_red_blocks_learning_even_when_unadjusted_gate_passed() -> None:
    scorer = _FakeScorer({"theta_min": 2.0, "signal": 2.5, "status": "GREEN", "passed": True})
    wrapper = _wrapper_for(scorer, "volatile")

    result = wrapper.learn("decision-1", "enter_long", context={"regime": "volatile"})

    assert result["status"] == "paused"
    assert result["reason"] == "conservation_red"
    assert result["theta_min"] == 3.0
    assert result["headroom"] == -0.5
    assert result["passed"] is False
    assert scorer.learn_calls == 0


def test_adjusted_green_allows_learning_to_proceed() -> None:
    scorer = _FakeScorer({"theta_min": 2.0, "signal": 3.5, "status": "GREEN", "passed": True})
    wrapper = _wrapper_for(scorer, "volatile")

    result = wrapper.learn("decision-1", "enter_long", context={"regime": "volatile"})

    assert result["learned"] is True
    assert scorer.learn_calls == 1


def test_cold_start_skips_regime_adjusted_threshold() -> None:
    scorer = _FakeScorer({
        "theta_min": 10.0,
        "signal": 0.0,
        "status": "COLD_START",
        "passed": True,
        "conservation_mode": "cold_start",
    })
    wrapper = _wrapper_for(scorer, "volatile")

    result = wrapper.learn("decision-1", "enter_long", context={"regime": "volatile"})

    assert result["learned"] is True
    assert scorer.learn_calls == 1


def test_bootstrap_skips_regime_adjusted_threshold() -> None:
    scorer = _FakeScorer({
        "theta_min": 10.0,
        "signal": 0.0,
        "status": "BOOTSTRAP",
        "passed": True,
        "conservation_mode": "bootstrap",
    })
    wrapper = _wrapper_for(scorer, "volatile")

    result = wrapper.learn("decision-1", "enter_long", context={"regime": "volatile"})

    assert result["learned"] is True
    assert scorer.learn_calls == 1


def test_public_adjuster_preserves_cold_start_status() -> None:
    monitor = RegimeMonitor()
    monitor.record("volatile")
    wrapper = TradingRegimeScorerProxy(_FakeScorerProxy(_FakeScorer({}), "volatile"), monitor)

    payload = wrapper.conservation_status_adjuster({
        "theta_min": 10.0,
        "signal": 0.0,
        "status": "COLD_START",
        "passed": True,
        "conservation_mode": "cold_start",
    })

    assert payload["status"] == "COLD_START"
    assert payload["passed"] is True


def test_public_conservation_adjuster_reflects_adjusted_threshold(client: Any) -> None:
    client.post(
        "/api/score",
        json={"category": "trend_following", "factors": _factors(), "metadata": {"vix": 35.0}},
    )

    payload = client.app.state.trading_regime_conditioning.conservation_status_adjuster(
        {
            "verified_count": 20,
            "correct_count": 20,
            "alpha": 1.0,
            "q": 1.0,
            "theta_min": 15.0,
            "status": "GREEN",
            "passed": True,
        }
    )

    assert payload["signal"] == 20.0
    assert payload["theta_min"] == 22.5
    assert payload["status"] == "RED"
    assert payload["passed"] is False


class _FakeGraphStore:
    def __init__(self, regime: str) -> None:
        self.regime = regime

    def get_decision(self, decision_id: str, domain: str) -> dict[str, Any]:
        return {"decision_id": decision_id, "domain": domain, "metadata": {"regime_tag": self.regime}}


class _FakeScorer:
    def __init__(self, conservation_state: dict[str, Any]) -> None:
        self._preset = SimpleNamespace(eta_confirm=0.05, eta_override=0.05)
        self._scorer = SimpleNamespace(centroids=[0.0, 1.0])
        self._conservation_state = {
            "verified_count": 20,
            "correct_count": 20,
            "alpha": 1.0,
            "q": 1.0,
            "penalty_ratio": 3.0,
            "conservation_mode": "normal",
            **conservation_state,
        }
        self.learn_calls = 0

    def _conservation_pause(self) -> None:
        return None

    def get_conservation_state(self) -> dict[str, Any]:
        return dict(self._conservation_state)

    def learn(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        self.learn_calls += 1
        return {"learned": True}


class _FakeScorerProxy:
    def __init__(self, scorer: _FakeScorer, regime: str) -> None:
        self._scorer_instance = scorer
        self.graph_store = _FakeGraphStore(regime)

    def _scorer(self) -> _FakeScorer:
        return self._scorer_instance


def _wrapper_for(scorer: _FakeScorer, regime: str) -> TradingRegimeScorerProxy:
    monitor = RegimeMonitor()
    monitor.record(regime)
    return TradingRegimeScorerProxy(_FakeScorerProxy(scorer, regime), monitor)
