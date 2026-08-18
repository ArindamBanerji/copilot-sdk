from __future__ import annotations

import re
from pathlib import Path

from app.services.pattern_detector import detect_patterns
from app.services.regime_recommender import RegimeRecommender
from app.settings import settings


def test_safe_01_trading_backend_has_no_directive_phrases() -> None:
    app_root = Path(__file__).parents[1] / "app"
    patterns = (
        re.compile(r"reduce\s+size", re.IGNORECASE),
        re.compile(r"skip\s+(this|the|next)", re.IGNORECASE),
        re.compile(r"\bhold\s+sizing\b", re.IGNORECASE),
    )
    violations: list[str] = []
    for path in sorted(app_root.rglob("*.py")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            if any(pattern.search(line) for pattern in patterns):
                violations.append(f"{path}:{line_number}: {line.strip()}")
    assert violations == []


def test_safe_02_broker_order_endpoint_is_blocked(client) -> None:
    response = client.post(
        "/api/broker/orders",
        params={"broker": "mock"},
        json={"ticker": "AAPL", "side": "buy", "qty": 1},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == {
        "error": "observation_only",
        "message": "Trading copilot operates in observation-only mode.",
    }


def test_safe_03_pattern_detector_marks_observations() -> None:
    trades = [
        {
            "trade_id": f"t-{index}",
            "entry_time": f"2026-01-01T10:{index * 10:02d}:00Z",
            "pnl": -10.0 if index == 0 else 2.0,
            "is_correct": index != 0,
            "size": 1.0,
            "category": "trend_following",
        }
        for index in range(6)
    ]
    patterns = detect_patterns(trades)

    assert patterns
    assert all(pattern["observation_only"] is True for pattern in patterns)
    assert all("Observation:" in pattern["recommendation"] for pattern in patterns)


def test_safe_04_regime_recommender_is_observation_only() -> None:
    payload = RegimeRecommender().recommend(
        "volatile",
        {"trend_following": {"trending": 0.70, "ranging": 0.55, "volatile": 0.35}},
        conservation_status={"status": "AMBER"},
    )

    assert payload["observation_only"] is True
    assert all(item["observation_only"] is True for item in payload["recommendations"])
    assert payload["sizing_recommendation"]["observation_only"] is True
    assert "reduce" not in str(payload).lower()
    assert "avoid" not in str(payload).lower()


def test_safe_05_regime_endpoint_is_observation_only(client) -> None:
    response = client.get("/api/trading/regime")

    assert response.status_code == 200
    payload = response.json()
    assert all(item["observation_only"] is True for item in payload["recommendations"])
    assert "hold sizing" not in response.text.lower()


def test_safe_06_execution_is_disabled_by_default() -> None:
    assert settings.TRADING_EXECUTION_ENABLED is False
