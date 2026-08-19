from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.situation_analyzer import (
    build_situation_judgment,
    compute_regime_strategy_accuracy,
)
from app.services.situation_context import SituationContext


def _decision(strategy: str, correct: bool, regime: str = "trending", **extra: object) -> dict[str, object]:
    return {
        "strategy_tag": strategy,
        "category": strategy,
        "regime": regime,
        "verified": True,
        "outcome_correct": correct,
        **extra,
    }


def test_situation_context_detects_all_supported_regimes() -> None:
    assert SituationContext.detect(12, 15).regime == "calm"
    assert SituationContext.detect(15, 35).regime == "trending"
    assert SituationContext.detect(22, 20).regime == "ranging"
    assert SituationContext.detect(35, 20).regime == "volatile"


def test_strategy_accuracy_is_scoped_and_abstains_until_evidence_threshold() -> None:
    rows = [_decision("trend", True) for _ in range(3)] + [_decision("trend", False, "volatile")]
    payload = compute_regime_strategy_accuracy(rows, "trending", min_decisions=3)
    assert payload["trend"]["accuracy"] == 1.0
    assert payload["trend"]["evidence_sufficient"] is True


def test_situation_judgment_reports_rejections_and_observation_only() -> None:
    rows = [_decision("trend", True, rejected=True) for _ in range(2)]
    payload = build_situation_judgment(
        rows,
        regime="trending",
        confidence=0.8,
        indicators={"vix": 14.0, "adx": 32.0, "trend_strength": 32.0},
        min_decisions=3,
    )
    assert payload["regime_abstention"] is True
    assert payload["regime_rejection_count"] == 2
    assert payload["observation_only"] is True
    assert "insufficient regime-specific evidence" in str(payload["observation"]).lower()


def test_situation_endpoint_returns_conditioned_observation(tmp_path: Path) -> None:
    client = TestClient(create_app(db_path=tmp_path / "situation-judgment.db", demo_bundle_path=False))
    response = client.get("/api/trading/situation")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["regime"] in {"trending", "ranging", "volatile", "calm"}
    assert set(payload["indicators"]) >= {"vix", "adx", "trend_strength"}
    assert payload["observation_only"] is True
    assert "regime_abstention" in payload

