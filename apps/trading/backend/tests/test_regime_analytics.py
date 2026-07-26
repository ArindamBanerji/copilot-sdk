from __future__ import annotations

from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.regime_analytics import RegimeAnalytics
from copilot_sdk.scoring.scorer import CompoundingScorer


def _decision(regime: str, *, verified: bool = True, correct: bool = True) -> dict:
    payload = {
        "decision_id": f"{regime}-{verified}-{correct}",
        "regime_context": {
            "regime": regime,
            "vol_state": "normal",
            "hurst": 0.55,
            "vix_percentile": 0.42,
            "tagged_at": "2026-07-15T00:00:00+00:00",
        },
    }
    if verified:
        payload["verified"] = True
        payload["outcome_correct"] = correct
    return payload


def test_regime_analytics_groups_by_regime() -> None:
    payload = RegimeAnalytics().compute([
        _decision("trending"),
        _decision("trending"),
        _decision("volatile"),
    ])

    assert payload["regimes"]["trending"]["decision_count"] == 2
    assert payload["regimes"]["volatile"]["decision_count"] == 1


def test_regime_analytics_accuracy_correct() -> None:
    payload = RegimeAnalytics().compute([
        _decision("trending", correct=True),
        _decision("trending", correct=False),
    ])

    assert payload["regimes"]["trending"]["accuracy"] == 0.5


def test_regime_analytics_iks_proxy_correct() -> None:
    decisions = [_decision("trending", correct=index < 40) for index in range(50)]

    payload = RegimeAnalytics().compute(decisions)

    assert payload["regimes"]["trending"]["accuracy"] == 0.8
    assert payload["regimes"]["trending"]["iks_proxy"] == 0.2
    assert payload["regimes"]["trending"]["conservation_rate"] is None


def test_regime_analytics_accumulating_state() -> None:
    payload = RegimeAnalytics().compute([_decision("volatile") for _ in range(12)])

    stat = payload["regimes"]["volatile"]
    assert stat["measurement_state"] == "accumulating"
    assert stat["provenance"] == "accumulating"
    assert stat["iks_proxy"] is None


def test_regime_analytics_measured_state() -> None:
    payload = RegimeAnalytics().compute([_decision("trending") for _ in range(30)])

    stat = payload["regimes"]["trending"]
    assert stat["measurement_state"] == "measured"
    assert stat["provenance"] == "real_measured"


def test_regime_analytics_empty_regime() -> None:
    payload = RegimeAnalytics().compute([])

    stat = payload["regimes"]["ranging"]
    assert stat["decision_count"] == 0
    assert stat["verified_count"] == 0
    assert stat["accuracy"] is None
    assert stat["conservation_rate"] is None


def test_regime_analytics_conservation_stats_read_only() -> None:
    safe = _decision("trending")
    safe["conservation_safe"] = True
    unsafe = _decision("trending")
    unsafe["metadata"] = {"conservation_status": "RED"}

    payload = RegimeAnalytics().compute([safe, unsafe])

    stat = payload["regimes"]["trending"]
    assert stat["conservation_count"] == 2
    assert stat["conservation_safe_count"] == 1
    assert stat["conservation_rate"] == 0.5


def test_regime_analytics_endpoint_returns_200(tmp_path: Path) -> None:
    client = TestClient(create_app(db_path=tmp_path / "regime_analytics.db", demo_bundle_path=False))

    response = client.get("/api/trading/regime-analytics")

    assert response.status_code == 200
    assert "regimes" in response.json()


def test_regime_analytics_zero_writes_to_scorer(tmp_path: Path) -> None:
    scorer = CompoundingScorer.from_preset("trading", db_path=tmp_path / "zero_writes.db", profile="test")
    before = np.asarray(scorer.gae_scorer.centroids).copy()

    RegimeAnalytics().compute([_decision("trending") for _ in range(30)])

    after = np.asarray(scorer.gae_scorer.centroids)
    np.testing.assert_array_equal(before, after)
