from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from ci_trading.quant import CorrelationMonitor
from copilot_sdk.scoring.presets.trading import TradingPreset
from app.analytics.dispersion_follow import compute_dispersion_follow_rate
from app.analytics.regime_vrp import compute_regime_vrp
from app.analytics.vol_sharpe import compute_clustering_adjusted_sharpe
from app.analytics.vrp_attribution import compute_vrp_attribution
from app.main import create_app
from app.services.regime_scoring import _tag_analytics_metadata


def _client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(db_path=tmp_path / "trading_vol_analytics.db", demo_bundle_path=False))


def test_quality_adjusted_score_lower_on_clustered_data() -> None:
    decisions = [{"quality": value} for value in ([1.0] * 20 + [0.0] * 20 + [1.0] * 20)]

    payload = compute_clustering_adjusted_sharpe(decisions)

    assert payload["n_decisions"] == 60
    assert payload["quality_adjusted_score"] < payload["naive_quality_score"]
    assert payload["inflation"] > 1.0


def test_quality_score_day_zero_when_few_decisions() -> None:
    payload = compute_clustering_adjusted_sharpe([{"quality": 1.0}, {"quality": 0.0}])

    assert payload["day_zero"] is True
    assert payload["decisions_until_measured"] == 28


def test_quality_score_provenance_correct() -> None:
    measured = compute_clustering_adjusted_sharpe([{"quality": 1.0 if index % 2 else 0.0} for index in range(30)])
    accumulating = compute_clustering_adjusted_sharpe([{"quality": 1.0} for _ in range(3)])

    assert measured["provenance"] == "real_measured"
    assert measured["substantiation"] == "T-R"
    assert accumulating["provenance"] == "accumulating"


def test_quality_score_groups_by_persisted_cluster_id() -> None:
    decisions = [
        {"quality": 0.4 + (index % 2) * 0.2, "metadata": {"analytics": {"cluster_id": "regime:trending"}}}
        for index in range(10)
    ]

    payload = compute_clustering_adjusted_sharpe(decisions)

    assert payload["clusters"] == [
        {
            "cluster_id": "regime:trending",
            "n_decisions": 10,
            "mean_return": 0.5,
            "std_return": 0.105409,
            "risk_adjusted_quality": 4.743,
            "status": "measured",
        }
    ]


def test_quality_score_uses_unclassified_and_zero_std_is_zero() -> None:
    payload = compute_clustering_adjusted_sharpe([{"quality": 0.5} for _ in range(10)])

    assert payload["clusters"][0]["cluster_id"] == "unclassified"
    assert payload["clusters"][0]["risk_adjusted_quality"] == 0.0
    assert payload["clusters"][0]["status"] == "measured"


def test_quality_score_marks_small_clusters_accumulating() -> None:
    decisions = (
        [{"quality": 0.4 + (index % 2) * 0.2, "metadata": {"analytics": {"cluster_id": "regime:trending"}}} for index in range(10)]
        + [{"quality": 0.5, "metadata": {"analytics": {"cluster_id": "regime:volatile"}}} for _ in range(2)]
    )

    payload = compute_clustering_adjusted_sharpe(decisions)
    clusters = {row["cluster_id"]: row for row in payload["clusters"]}

    assert clusters["regime:trending"]["status"] == "measured"
    assert clusters["regime:volatile"]["status"] == "accumulating"


def test_score_metadata_tags_regime_cluster_and_request_volatility() -> None:
    metadata = {
        "context": {"iv": 25.0, "realized_volatility": 20.0},
        "regime_metadata": {"regime": "volatile"},
    }

    _tag_analytics_metadata(metadata)

    assert metadata["analytics"] == {
        "cluster_id": "regime:volatile",
        "cluster_method": "regime_v1",
        "implied_vol": 0.25,
        "implied_vol_raw": 25.0,
        "realized_vol": 0.2,
        "realized_vol_raw": 20.0,
        "vol_unit": "annualized_decimal",
        "iv_rv_source": "request_input",
    }


def test_score_metadata_persists_decimal_volatility() -> None:
    metadata = {"context": {"iv": 0.25}, "regime_metadata": {"regime": "volatile"}}

    _tag_analytics_metadata(metadata)

    assert metadata["analytics"]["implied_vol"] == 0.25


def test_score_metadata_normalizes_percentage_volatility() -> None:
    metadata = {"context": {"iv": 25.0}, "regime_metadata": {"regime": "volatile"}}

    _tag_analytics_metadata(metadata)

    assert metadata["analytics"]["implied_vol"] == 0.25


def test_score_metadata_persists_zero_volatility() -> None:
    metadata = {"context": {"iv": 0.0}, "regime_metadata": {"regime": "volatile"}}

    _tag_analytics_metadata(metadata)

    assert metadata["analytics"]["implied_vol"] == 0.0


def test_score_metadata_treats_two_as_percentage_volatility() -> None:
    metadata = {"context": {"iv": 2.0}, "regime_metadata": {"regime": "volatile"}}

    _tag_analytics_metadata(metadata)

    assert metadata["analytics"]["implied_vol"] == 0.02


def test_score_persists_analytics_metadata(tmp_path: Path) -> None:
    client = _client(tmp_path)
    factors = {name: 0.5 for name in TradingPreset().shape.factor_names}
    response = client.post(
        "/api/score",
        json={
            "category": "trend_following",
            "factors": factors,
            "metadata": {"context": {"iv": 0.25, "rv": 0.20}},
        },
    )

    assert response.status_code == 200
    decision = client.app.state.trading_selected_graph_store.get_decision(response.json()["decision_id"])
    assert decision is not None
    assert decision["metadata"]["analytics"]["cluster_id"].startswith("regime:")
    assert decision["metadata"]["analytics"]["implied_vol"] == 0.25
    assert decision["metadata"]["analytics"]["realized_vol"] == 0.2


def test_vrp_attribution_groups_by_tail_state() -> None:
    decisions = (
        [{"vrp_harvest": True, "iv": 0.24, "rv": 0.16, "tail_dependence": 0.1, "vrp_capture": 1.0} for _ in range(20)]
        + [{"vrp_harvest": True, "iv": 0.28, "rv": 0.18, "tail_dependence": 0.7, "vrp_capture": -0.5} for _ in range(10)]
    )

    payload = compute_vrp_attribution(decisions)

    assert payload["tail_attribution"]["low_tail_decisions"] == 20
    assert payload["tail_attribution"]["high_tail_decisions"] == 10


def test_vrp_low_tail_capture_percentage() -> None:
    decisions = (
        [{"vrp_harvest": True, "iv": 0.24, "rv": 0.16, "tail_dependence": 0.1, "vrp_capture": 2.0} for _ in range(3)]
        + [{"vrp_harvest": True, "iv": 0.28, "rv": 0.18, "tail_dependence": 0.7, "vrp_capture": 1.0} for _ in range(1)]
    )

    payload = compute_vrp_attribution(decisions)

    assert payload["tail_attribution"]["low_tail_capture_pct"] == 0.857


def test_vrp_day_zero_when_few_decisions() -> None:
    payload = compute_vrp_attribution([
        {"vrp_harvest": True, "iv": 0.24, "rv": 0.16, "tail_dependence": 0.1, "vrp_capture": 1.0}
    ])

    assert payload["status"] == "instrument_validated"
    assert payload["day_zero"] is True
    assert payload["decisions_until_measured"] == 30
    assert payload["tail_attribution"]["decisions_until_measured"] == 29


def test_vrp_spread_and_edge_classification_from_analytics_metadata() -> None:
    decisions = [{"metadata": {"analytics": {"implied_vol": 0.25, "realized_vol": 0.20}}} for _ in range(30)]

    payload = compute_vrp_attribution(decisions)

    assert payload["vrp_spread_mean"] == 0.0225
    assert payload["vrp_spread_current"] == 0.0225
    assert payload["classification"] == "edge"
    assert payload["iv_mean"] == 0.25
    assert payload["rv_mean"] == 0.2
    assert payload["n_eligible"] == 30
    assert payload["status"] == "measured"
    assert payload["provenance"] == "real_measured"
    assert payload["day_zero"] is False
    assert payload["tail_attribution"]["day_zero"] is True


def test_vrp_insurance_and_neutral_classifications() -> None:
    insurance = compute_vrp_attribution([{"metadata": {"analytics": {"implied_vol": 0.10, "realized_vol": 0.20}}} for _ in range(30)])
    neutral = compute_vrp_attribution([{"metadata": {"analytics": {"implied_vol": 0.20, "realized_vol": 0.20}}} for _ in range(30)])

    assert insurance["classification"] == "insurance"
    assert neutral["classification"] == "neutral"


def test_vrp_missing_volatility_is_instrument_validated() -> None:
    payload = compute_vrp_attribution([{"quality": 1.0}, {"metadata": {"analytics": {"implied_vol": 0.2}}}])

    assert payload["status"] == "instrument_validated"
    assert payload["n_eligible"] == 0
    assert payload["n_excluded_missing_iv_rv"] == 2
    assert payload["vrp_spread_mean"] is None


def test_vrp_top_level_state_uses_iv_rv_eligibility_not_tail_state() -> None:
    decisions = [
        {
            "vrp_harvest": True,
            "iv": 0.24,
            "rv": 0.16,
            "tail_dependence": 0.1,
            "metadata": {"analytics": {"implied_vol": 0.25, "realized_vol": 0.20}},
        }
        for _ in range(30)
    ]

    payload = compute_vrp_attribution(decisions)

    assert payload["status"] == "measured"
    assert payload["day_zero"] is False
    assert payload["tail_attribution"]["day_zero"] is False


def test_vrp_top_level_state_is_instrument_validated_despite_tail_data() -> None:
    decisions = [{"vrp_harvest": True, "iv": 0.24, "rv": 0.16, "tail_dependence": 0.1} for _ in range(30)]

    payload = compute_vrp_attribution(decisions)

    assert payload["status"] == "instrument_validated"
    assert payload["provenance"] == "instrument_validated"
    assert payload["day_zero"] is True
    assert payload["tail_attribution"]["day_zero"] is False


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
