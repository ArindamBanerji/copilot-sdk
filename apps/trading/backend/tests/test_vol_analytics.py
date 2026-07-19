from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from ci_trading.quant import CorrelationMonitor
from app.analytics.dispersion_follow import compute_dispersion_follow_rate
from app.analytics.regime_vrp import compute_regime_vrp
from app.analytics.vol_sharpe import compute_clustering_adjusted_sharpe
from app.analytics.vrp_attribution import compute_vrp_attribution
from app.main import create_app


def _client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(db_path=tmp_path / "trading_vol_analytics.db", demo_bundle_path=False))


def test_clustering_sharpe_adjusted_lower_on_clustered_data() -> None:
    decisions = [{"quality": value} for value in ([1.0] * 20 + [0.0] * 20 + [1.0] * 20)]

    payload = compute_clustering_adjusted_sharpe(decisions)

    assert payload["n_decisions"] == 60
    assert payload["adjusted_sharpe"] < payload["naive_sharpe"]
    assert payload["inflation"] > 1.0


def test_clustering_sharpe_day_zero_when_few_decisions() -> None:
    payload = compute_clustering_adjusted_sharpe([{"quality": 1.0}, {"quality": 0.0}])

    assert payload["day_zero"] is True
    assert payload["decisions_until_measured"] == 28


def test_clustering_sharpe_provenance_correct() -> None:
    measured = compute_clustering_adjusted_sharpe([{"quality": 1.0 if index % 2 else 0.0} for index in range(30)])
    accumulating = compute_clustering_adjusted_sharpe([{"quality": 1.0} for _ in range(3)])

    assert measured["provenance"] == "real_measured"
    assert measured["substantiation"] == "T-R"
    assert accumulating["provenance"] == "accumulating"


def test_vrp_attribution_groups_by_tail_state() -> None:
    decisions = (
        [{"vrp_harvest": True, "iv": 0.24, "rv": 0.16, "tail_dependence": 0.1, "vrp_capture": 1.0} for _ in range(20)]
        + [{"vrp_harvest": True, "iv": 0.28, "rv": 0.18, "tail_dependence": 0.7, "vrp_capture": -0.5} for _ in range(10)]
    )

    payload = compute_vrp_attribution(decisions)

    assert payload["low_tail_decisions"] == 20
    assert payload["high_tail_decisions"] == 10


def test_vrp_low_tail_capture_percentage() -> None:
    decisions = (
        [{"vrp_harvest": True, "iv": 0.24, "rv": 0.16, "tail_dependence": 0.1, "vrp_capture": 2.0} for _ in range(3)]
        + [{"vrp_harvest": True, "iv": 0.28, "rv": 0.18, "tail_dependence": 0.7, "vrp_capture": 1.0} for _ in range(1)]
    )

    payload = compute_vrp_attribution(decisions)

    assert payload["low_tail_capture_pct"] == 0.857


def test_vrp_day_zero_when_few_decisions() -> None:
    payload = compute_vrp_attribution([
        {"vrp_harvest": True, "iv": 0.24, "rv": 0.16, "tail_dependence": 0.1, "vrp_capture": 1.0}
    ])

    assert payload["day_zero"] is True
    assert payload["decisions_until_measured"] == 29


def test_regime_vrp_percentile_per_regime() -> None:
    decisions = [
        {"regime": "calm", "implied_variance": 0.02 + index * 0.001, "realized_variance": 0.01}
        for index in range(10)
    ]

    payload = compute_regime_vrp(decisions)

    assert payload["regimes"]["calm"]["percentile"] == 100.0
    assert payload["regimes"]["calm"]["band"] == "rich"


def test_regime_vrp_day_zero() -> None:
    payload = compute_regime_vrp([
        {"regime": "volatile", "implied_variance": 0.04, "realized_variance": 0.03}
    ])

    assert payload["day_zero"] is True
    assert payload["decisions_until_measured"] == 29


def test_dispersion_follow_rate_computed() -> None:
    decisions = (
        [{"dispersion_gap": 0.10, "dispersion_followed": True, "outcome_value": 100.0} for _ in range(4)]
        + [{"dispersion_gap": 0.12, "dispersion_followed": False, "outcome_value": 50.0} for _ in range(8)]
    )

    payload = compute_dispersion_follow_rate(decisions)

    assert payload["signals_fired"] == 12
    assert payload["followed"] == 4
    assert payload["follow_rate"] == 0.333


def test_dispersion_skipped_trades_valued() -> None:
    payload = compute_dispersion_follow_rate([
        {"dispersion_gap": 0.10, "dispersion_followed": False, "outcome_value": 62000.0},
        {"dispersion_gap": 0.02, "dispersion_followed": False, "outcome_value": 1000.0},
    ])

    assert payload["skipped"] == 1
    assert payload["skipped_value"] == 62000.0


def test_tail_bets_from_correlation_monitor() -> None:
    frame = pd.DataFrame({
        "AAPL": [0.01, 0.02, -0.04, 0.03, -0.05, 0.02, -0.03, 0.04, -0.06, 0.03, -0.04, 0.02],
        "MSFT": [0.011, 0.019, -0.041, 0.029, -0.052, 0.021, -0.031, 0.039, -0.061, 0.031, -0.039, 0.019],
        "NVDA": [0.012, 0.021, -0.045, 0.033, -0.057, 0.018, -0.034, 0.043, -0.064, 0.028, -0.043, 0.022],
    })
    market = frame.mean(axis=1)

    alert = CorrelationMonitor(alert_multiplier=1.1).check_correlation(frame, [1 / 3, 1 / 3, 1 / 3], market)

    assert alert is not None
    assert alert.effective_multiplier > 1.1
    assert alert.n_effective_bets < 3


def test_vol_analytics_endpoints_return_day_zero_shape(tmp_path: Path) -> None:
    client = _client(tmp_path)

    for path in (
        "/api/trading/analytics/vol-sharpe",
        "/api/trading/analytics/vrp-attribution",
        "/api/trading/analytics/regime-vrp",
        "/api/trading/analytics/dispersion-follow",
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()["day_zero"] is True
