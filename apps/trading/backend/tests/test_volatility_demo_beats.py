from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


ENDPOINTS = (
    ("/api/trading/vol/short-vol-illusion", ("clustering_adjustment_factor", "tail_risk_indicator")),
    ("/api/trading/vol/vrp-edge", ("vrp_edge", "tail_dependence")),
    ("/api/trading/vol/situational-abstention", ("per_regime_decisions", "vol_context")),
    ("/api/trading/vol/rich-cheap", ("current_regime", "observation_only")),
    ("/api/trading/vol/dispersion-follow", ("skipped_signal_dollar_impact", "observation_only")),
    ("/api/trading/vol/effective-bets", ("effective_bets", "day_zero")),
    ("/api/trading/regime/reconvergenc", ("current_regime", "cold_start_curves")),
)


@pytest.mark.parametrize("path,_keys", ENDPOINTS)
def test_trading_demo_beat_returns_success(client: TestClient, path: str, _keys: tuple[str, ...]) -> None:
    response = client.get(path)
    assert response.status_code == 200


@pytest.mark.parametrize("path,keys", ENDPOINTS)
def test_trading_demo_beat_contract(path: str, keys: tuple[str, ...], client: TestClient) -> None:
    payload = client.get(path).json()
    assert all(key in payload for key in keys)


@pytest.mark.parametrize("path,_keys", ENDPOINTS)
def test_trading_demo_beat_is_observation_safe(client: TestClient, path: str, _keys: tuple[str, ...]) -> None:
    payload = client.get(path).json()
    assert isinstance(payload, dict)
    assert "observation_only" in payload or "observation" in payload
