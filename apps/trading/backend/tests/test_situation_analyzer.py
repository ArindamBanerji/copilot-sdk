from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.situation_analyzer import (
    check_regime_data_sufficiency,
    compute_regime_conditioned_stats,
    compute_regime_rejections,
    compute_sharpe_adjustment,
    detect_regime,
)


def _decision(regime: str, correct: bool = True) -> dict[str, object]:
    return {
        "regime": regime,
        "verified": True,
        "outcome_correct": correct,
    }


def test_regime_detection_uses_latest_tag() -> None:
    assert detect_regime([_decision("trending"), _decision("volatile")]) == "volatile"


def test_mixed_regime_data_is_classified_as_choppy_when_untagged() -> None:
    assert detect_regime([_decision("trending"), _decision("choppy")]) == "choppy"
    assert detect_regime([]) == "choppy"


def test_conditioned_stats_differ_by_regime() -> None:
    rows = [_decision("trending", True) for _ in range(10)] + [_decision("choppy", False) for _ in range(10)]
    payload = compute_regime_conditioned_stats(rows)
    assert payload["regimes"]["trending"]["accuracy"] == 1.0
    assert payload["regimes"]["choppy"]["accuracy"] == 0.0
    assert payload["provenance"] == "illustrative"


def test_sharpe_adjustment_deflates_raw_score() -> None:
    payload = compute_sharpe_adjustment([_decision("calm") for _ in range(20)])
    assert payload["clustering_adjusted_sharpe"] < payload["raw_sharpe"]
    assert payload["provenance"] == "illustrative"


def test_abstention_on_low_regime_data() -> None:
    payload = check_regime_data_sufficiency([_decision("volatile") for _ in range(4)], "volatile")
    assert payload["abstention_recommended"] is True
    assert payload["decision_count"] == 4


def test_regime_rejection_reason() -> None:
    payload = compute_regime_rejections([])
    assert payload["rejections"][0]["reason"] == "single_regime_only"


def test_situation_endpoints_return_200(tmp_path: Path) -> None:
    client = TestClient(create_app(db_path=tmp_path / "situation.db", demo_bundle_path=False))
    paths = (
        "/api/trading/situation/regime",
        "/api/trading/situation/conditioned-stats",
        "/api/trading/situation/sharpe-adjustment",
        "/api/trading/situation/abstention",
        "/api/trading/situation/regime-rejections",
    )
    for path in paths:
        response = client.get(path)
        assert response.status_code == 200, (path, response.text)
