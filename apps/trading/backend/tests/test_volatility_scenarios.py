from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.volatility_analytics import VolatilityAnalytics


def _trade(index: int, regime: str = "volatile") -> dict[str, object]:
    return {
        "regime": regime,
        "quality": 0.4 + (index % 2) * 0.2,
        "metadata": {"analytics": {"implied_vol": 0.25, "realized_vol": 0.2}},
        "vix": 32.0,
        "n_effective_bets": 1.5,
        "nominal_bets": 3.0,
    }


def test_all_volatility_surfaces_are_observation_only() -> None:
    analytics = VolatilityAnalytics()
    rows = [_trade(index) for index in range(30)]
    payloads = [
        analytics.clustering_adjusted_sharpe(rows, "volatile"),
        analytics.vrp_analysis(rows),
        analytics.rich_cheap_regime(rows, "volatile"),
        analytics.dispersion_follow_rate(rows),
        analytics.effective_bets_in_tail(rows),
    ]
    for payload in payloads:
        assert payload["observation_only"] is True
        assert payload["evidence_tier"] in {"T-O", "T-R"}
        assert isinstance(payload["observation"], str)


def test_sharpe_can_be_scoped_to_situation_regime() -> None:
    analytics = VolatilityAnalytics()
    rows = [_trade(index, "volatile") for index in range(30)] + [_trade(index, "trending") for index in range(5)]
    payload = analytics.clustering_adjusted_sharpe(rows, "volatile")
    assert payload["n_decisions"] == 30
    assert payload["observation_only"] is True


def test_rich_cheap_reports_current_regime() -> None:
    payload = VolatilityAnalytics().rich_cheap_regime([_trade(index) for index in range(30)], "volatile")
    assert payload["current_regime"] == "volatile"
    assert payload["observation_only"] is True


def test_effective_tail_bets_computed_from_persisted_diagnostics() -> None:
    payload = VolatilityAnalytics().effective_bets_in_tail([_trade(index) for index in range(30)])
    assert payload["effective_bets"] == 1.5
    assert payload["nominal_bets"] == 3.0
    assert payload["effective_bets_reduction"] == 0.5


def test_effective_tail_bets_abstains_without_diagnostics() -> None:
    rows = [{"vix": 35.0} for _ in range(30)]
    payload = VolatilityAnalytics().effective_bets_in_tail(rows)
    assert payload["effective_bets"] is None
    assert payload["day_zero"] is True


def test_volatility_endpoints_return_evidence_and_safe_json(tmp_path: Path) -> None:
    client = TestClient(create_app(db_path=tmp_path / "volatility.db", demo_bundle_path=False))
    for path in (
        "/api/trading/volatility/sharpe",
        "/api/trading/volatility/vrp",
        "/api/trading/volatility/rich-cheap?regime=volatile",
        "/api/trading/volatility/dispersion",
        "/api/trading/volatility/tail-bets",
    ):
        response = client.get(path)
        assert response.status_code == 200, (path, response.text)
        payload = response.json()
        assert "evidence_tier" in payload
        assert payload["observation_only"] is True
        assert isinstance(payload["observation"], str)


def test_unknown_regime_falls_back_without_directive() -> None:
    payload = VolatilityAnalytics().rich_cheap_regime([], "unknown")
    assert payload["current_regime"] == "ranging"
    assert "recommend" not in str(payload).lower()

