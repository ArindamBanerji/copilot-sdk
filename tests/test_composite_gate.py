from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.conservation_router import create_conservation_router
from copilot_sdk.scoring.composite_gate import CompositeGate


def _healthy_stream() -> list[bool]:
    return [True] * 400


def _drop_stream() -> list[bool]:
    return [True] * 380 + [False] * 20


def test_grate_no_fire_clean() -> None:
    result = CompositeGate().evaluate(alpha_q_v=10.0, theta_min=1.0, rolling_accuracy=1.0, baseline=1.0, verified_outcomes=_healthy_stream())
    assert result["g_rate"]["active"] is False


def test_grate_fires_on_sudden_drop() -> None:
    result = CompositeGate().evaluate(alpha_q_v=10.0, theta_min=1.0, rolling_accuracy=0.95, baseline=1.0, verified_outcomes=_drop_stream())
    assert result["g_rate"]["active"] is True


def test_grate_does_not_fire_below_window() -> None:
    result = CompositeGate().evaluate(alpha_q_v=10.0, theta_min=1.0, rolling_accuracy=0.0, baseline=1.0, verified_outcomes=[False] * 19)
    assert result["g_rate"]["active"] is False
    assert result["g_rate"]["short_window_count"] == 19


def test_grate_threshold_085() -> None:
    result = CompositeGate(m_rate=0.85).evaluate(alpha_q_v=10.0, theta_min=1.0, rolling_accuracy=1.0, baseline=1.0, verified_outcomes=_healthy_stream())
    assert result["g_rate"]["threshold"] == 0.85


def test_grate_threshold_090() -> None:
    stream = [True] * 397 + [True, True, True, False, False, False]
    low = CompositeGate(m_rate=0.85).evaluate(alpha_q_v=10.0, theta_min=1.0, rolling_accuracy=1.0, baseline=1.0, verified_outcomes=stream)
    high = CompositeGate(m_rate=0.90).evaluate(alpha_q_v=10.0, theta_min=1.0, rolling_accuracy=1.0, baseline=1.0, verified_outcomes=stream)
    assert low["g_rate"]["active"] is False
    assert high["g_rate"]["active"] is True


def test_grate_recovery() -> None:
    during = CompositeGate().evaluate(alpha_q_v=10.0, theta_min=1.0, rolling_accuracy=1.0, baseline=1.0, verified_outcomes=_drop_stream())
    recovered = CompositeGate().evaluate(alpha_q_v=10.0, theta_min=1.0, rolling_accuracy=1.0, baseline=1.0, verified_outcomes=_drop_stream() + [True] * 20)
    assert during["g_rate"]["active"] is True
    assert recovered["g_rate"]["active"] is False


def test_three_layer_all_green() -> None:
    result = CompositeGate().evaluate(alpha_q_v=10.0, theta_min=1.0, rolling_accuracy=1.0, baseline=1.0, verified_outcomes=_healthy_stream())
    assert result["status"] == "GREEN"


def test_three_layer_gabs_fires() -> None:
    result = CompositeGate().evaluate(alpha_q_v=0.1, theta_min=1.0, rolling_accuracy=1.0, baseline=1.0, verified_outcomes=_healthy_stream())
    assert result["status"] == "AMBER"
    assert result["g_abs"]["active"] is True


def test_three_layer_grel_fires() -> None:
    result = CompositeGate().evaluate(alpha_q_v=10.0, theta_min=1.0, rolling_accuracy=0.5, baseline=1.0, verified_outcomes=_healthy_stream())
    assert result["status"] == "AMBER"
    assert result["g_rel"]["active"] is True


def test_three_layer_grate_fires() -> None:
    result = CompositeGate().evaluate(alpha_q_v=10.0, theta_min=1.0, rolling_accuracy=1.0, baseline=1.0, verified_outcomes=_drop_stream())
    assert result["status"] == "AMBER"
    assert result["g_rate"]["active"] is True


def test_three_layer_multiple_fire() -> None:
    result = CompositeGate().evaluate(alpha_q_v=0.1, theta_min=1.0, rolling_accuracy=0.5, baseline=1.0, verified_outcomes=_drop_stream())
    assert result["status"] == "AMBER"
    assert result["g_abs"]["active"] is True
    assert result["g_rel"]["active"] is True
    assert result["g_rate"]["active"] is True


def test_three_layer_status_response() -> None:
    app = FastAPI()
    app.include_router(create_conservation_router("dataops", state_provider=lambda: {"verified_count": 400, "correct_count": 400, "total_decisions": 400, "penalty_ratio": 10.0, "total_categories": 6, "categories_with_data": 6, "verified_outcomes": _drop_stream()}))
    payload = TestClient(app).get("/conservation/status").json()
    assert {"g_abs", "g_rel", "g_rate"} <= set(payload)
    assert payload["g_rate"]["w_short"] == 20
    assert payload["g_rate"]["m_rate"] == 0.85
