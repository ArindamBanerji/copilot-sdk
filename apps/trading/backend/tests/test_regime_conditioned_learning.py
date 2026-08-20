from __future__ import annotations

from typing import Any


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


def test_rc_11_observation_only_controls_remain_available(client: Any) -> None:
    response = client.post(
        "/api/score",
        json={"category": "trend_following", "factors": _factors(), "metadata": {"vix": 35.0}},
    )
    assert response.status_code == 200
    assert response.json()["regime_parameters"]["regime"] == "volatile"
