from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]

for path in (BACKEND_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.main import create_app  # noqa: E402
from copilot_sdk.scoring.presets.trading import TradingPreset  # noqa: E402


TRADING_FACTORS = {
    "signal_alignment": 0.82,
    "market_regime": 0.88,
    "position_sizing": 0.76,
    "timing_quality": 0.34,
    "risk_reward_actual": 0.67,
    "emotional_indicator": 0.71,
    "signal_confidence": 0.50,
}
ALT_FACTORS = {
    "signal_alignment": 0.25,
    "market_regime": 0.42,
    "position_sizing": 0.30,
    "timing_quality": 0.22,
    "risk_reward_actual": 0.28,
    "emotional_indicator": 0.35,
    "signal_confidence": 0.36,
}
VALID_CATEGORIES = set(TradingPreset().shape.category_names)
VALID_ACTIONS = set(TradingPreset().shape.action_names)
VALID_FACTORS = set(TradingPreset().shape.factor_names)


def _client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(db_path=tmp_path / "trading_analytics.db", demo_bundle_path=False))


def _score(client: TestClient, category: str, factors: dict[str, float] | None = None) -> dict[str, Any]:
    response = client.post(
        "/api/score",
        json={"category": category, "factors": factors or TRADING_FACTORS},
    )
    assert response.status_code == 200
    return response.json()


def _learn(client: TestClient, decision_id: str, actual_action: str) -> dict[str, Any]:
    response = client.post(
        "/api/learn",
        json={"decision_id": decision_id, "actual_action": actual_action},
    )
    assert response.status_code == 200
    return response.json()


def _seed_verified_decisions(client: TestClient) -> None:
    rows = [
        ("trend_following", TRADING_FACTORS, "strong_execution"),
        ("trend_following", ALT_FACTORS, "poor_execution"),
        ("mean_reversion", TRADING_FACTORS, "strong_execution"),
    ]
    for category, factors, actual_action in rows:
        score = _score(client, category, factors)
        _learn(client, score["decision_id"], actual_action)


def test_execution_analysis_empty_store_returns_zero_shape(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/api/trading/execution-analysis")

    assert response.status_code == 200
    payload = response.json()
    assert payload["decision_count"] == 0
    assert payload["quality_distribution"] == {action: 0 for action in VALID_ACTIONS}
    assert payload["factor_patterns"]
    assert payload["actionable_insights"] == []
    assert payload["source"] == "graphstore"


def test_cross_insights_empty_store_returns_default_shape(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/api/trading/cross-insights")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload["category_accuracy"]) == VALID_CATEGORIES
    assert all(row["verified_count"] == 0 for row in payload["category_accuracy"].values())
    assert payload["similar_categories"] == []
    assert payload["dominant_factors"] == {}
    assert payload["transfer_opportunities"] == []
    assert payload["source"] == "graphstore"


def test_execution_analysis_populates_from_verified_decisions(tmp_path: Path) -> None:
    client = _client(tmp_path)
    _seed_verified_decisions(client)

    payload = client.get("/api/trading/execution-analysis").json()

    assert payload["decision_count"] == 3
    assert sum(payload["quality_distribution"].values()) == payload["decision_count"]
    assert set(payload["quality_distribution"]) == VALID_ACTIONS
    assert payload["by_category"]["trend_following"]["decision_count"] == 2
    assert payload["by_category"]["mean_reversion"]["decision_count"] == 1
    assert {row["factor"] for row in payload["factor_patterns"]} == VALID_FACTORS
    assert all(row["severity"] in {"low", "medium", "high"} for row in payload["actionable_insights"])
    assert_json_safe(payload)


def test_execution_analysis_category_filter(tmp_path: Path) -> None:
    client = _client(tmp_path)
    _seed_verified_decisions(client)

    payload = client.get("/api/trading/execution-analysis?category=trend_following").json()

    assert payload["decision_count"] == 2
    assert set(payload["by_category"]) == {"trend_following"}
    assert sum(payload["quality_distribution"].values()) == 2


def test_execution_analysis_does_not_report_fill_level_fields(tmp_path: Path) -> None:
    client = _client(tmp_path)
    _seed_verified_decisions(client)

    payload = client.get("/api/trading/execution-analysis").json()
    text = str(payload).lower()

    assert "slippage" not in text
    assert "fill" not in text
    assert "entry_price" not in text
    assert "exit_price" not in text
    assert "order_id" not in text


def test_cross_insights_populates_trading_category_outputs(tmp_path: Path) -> None:
    client = _client(tmp_path)
    _seed_verified_decisions(client)

    payload = client.get("/api/trading/cross-insights").json()

    assert set(payload["category_accuracy"]) == VALID_CATEGORIES
    assert payload["category_accuracy"]["trend_following"]["verified_count"] == 2
    assert payload["category_accuracy"]["mean_reversion"]["verified_count"] == 1
    assert isinstance(payload["similar_categories"], list)
    assert set(payload["dominant_factors"]).issubset(VALID_CATEGORIES)
    for factors in payload["dominant_factors"].values():
        assert {item["factor"] for item in factors}.issubset(VALID_FACTORS)
    for opportunity in payload["transfer_opportunities"]:
        assert opportunity["source_category"] in VALID_CATEGORIES
        assert opportunity["target_category"] in VALID_CATEGORIES
    assert_json_safe(payload)


def test_cross_insights_stays_within_trading_domain(tmp_path: Path) -> None:
    client = _client(tmp_path)
    _seed_verified_decisions(client)

    payload = client.get("/api/trading/cross-insights").json()
    text = str(payload).lower()

    assert "purchasing" not in text
    assert "dataops" not in text
    assert "s2p" not in text


def assert_json_safe(value: Any) -> None:
    if isinstance(value, dict):
        for nested in value.values():
            assert_json_safe(nested)
    elif isinstance(value, list):
        for nested in value:
            assert_json_safe(nested)
    elif isinstance(value, float):
        assert math.isfinite(value)
