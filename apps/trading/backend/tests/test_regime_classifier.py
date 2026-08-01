from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from copilot_sdk.evidence.provenance import Provenanced
from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring.presets.trading import TradingPreset
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.regime_router import create_regime_router
from app.services.regime_classifier import RegimeClassifier, RegimePerformanceMapper
from app.services.regime_history import RegimeHistory


def test_classify_volatile() -> None:
    assert RegimeClassifier().classify(35, 10) == "volatile"


def test_classify_trending() -> None:
    assert RegimeClassifier().classify(18, 30) == "trending"


def test_classify_ranging_low_adx() -> None:
    assert RegimeClassifier().classify(15, 20) == "ranging"


def test_classify_ranging_elevated() -> None:
    assert RegimeClassifier().classify(25, 30) == "ranging"


def test_boundary_vix_30() -> None:
    assert RegimeClassifier().classify(30, 40) == "ranging"


def test_boundary_vix_20() -> None:
    assert RegimeClassifier().classify(20, 40) == "ranging"


def test_boundary_adx_25() -> None:
    assert RegimeClassifier().classify(18, 25) == "ranging"


def test_near_boundary_detection() -> None:
    result = RegimeClassifier().classify_with_confidence(28, 24)

    assert result["near_boundary"] is True


def test_not_near_boundary() -> None:
    result = RegimeClassifier().classify_with_confidence(10, 35)

    assert result["near_boundary"] is False


def test_confidence_clear_volatile() -> None:
    assert RegimeClassifier().classify_with_confidence(45, 20)["confidence"] == 1.0


def test_confidence_clear_trending() -> None:
    assert RegimeClassifier().classify_with_confidence(12, 40)["confidence"] >= 0.8


def test_confidence_near_boundary() -> None:
    near = RegimeClassifier().classify_with_confidence(19, 24)
    clear = RegimeClassifier().classify_with_confidence(12, 40)

    assert near["confidence"] < clear["confidence"]


def test_confidence_always_positive() -> None:
    assert RegimeClassifier().classify_with_confidence(20, 25)["confidence"] > 0


def test_history_records_entry() -> None:
    history = RegimeHistory()

    history.record("trending", 18, 30, timestamp="2026-06-01T00:00:00+00:00")

    assert history.history(365)[0]["regime"] == "trending"


def test_history_most_recent_first() -> None:
    history = RegimeHistory()
    history.record("ranging", 20, 20, timestamp="2026-01-01T00:00:00+00:00")
    history.record("volatile", 35, 20, timestamp="2026-02-01T00:00:00+00:00")

    assert [row["regime"] for row in history.history(365)] == ["volatile", "ranging"]


def test_history_days_filter() -> None:
    history = RegimeHistory()
    old = (datetime.now(timezone.utc) - timedelta(days=120)).isoformat()
    recent = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
    history.record("ranging", 20, 20, timestamp=old)
    history.record("trending", 18, 30, timestamp=recent)

    assert [row["regime"] for row in history.history(30)] == ["trending"]


def test_history_max_entries() -> None:
    history = RegimeHistory(max_entries=2)
    history.record("ranging", 20, 20, timestamp="2026-01-01T00:00:00+00:00")
    history.record("trending", 18, 30, timestamp="2026-01-02T00:00:00+00:00")
    history.record("volatile", 35, 20, timestamp="2026-01-03T00:00:00+00:00")

    assert [row["regime"] for row in history.history(365)] == ["volatile", "trending"]


def test_regime_distribution() -> None:
    history = RegimeHistory()
    timestamp = datetime.now(timezone.utc).isoformat()
    history.record("ranging", 20, 20, timestamp=timestamp)
    history.record("ranging", 21, 20, timestamp=timestamp)
    history.record("volatile", 35, 20, timestamp=timestamp)

    assert history.regime_distribution(30) == {"trending": 0, "ranging": 2, "volatile": 1}


def test_per_regime_accuracy() -> None:
    mapper = RegimePerformanceMapper(_seed_store(), TradingPreset())

    accuracy = mapper.per_regime_accuracy()

    assert accuracy["trend_following"]["trending"]["accuracy"] == 1.0
    assert accuracy["trend_following"]["trending"]["n_decisions"] == 10


def test_min_decisions_threshold() -> None:
    store = InMemoryGraphStore(domain="trading")
    _seed_decisions(store, "trend_following", "trending", correct=9, incorrect=0)

    assert RegimePerformanceMapper(store, TradingPreset()).per_regime_accuracy() == {}


def test_edge_ranking() -> None:
    edges = RegimePerformanceMapper(_seed_store(), TradingPreset()).regime_edge("trending")

    assert edges[0]["category"] == "trend_following"
    assert edges[0]["edge"] > edges[-1]["edge"]


def test_edge_positive_and_negative() -> None:
    edges = RegimePerformanceMapper(_seed_store(), TradingPreset()).regime_edge("trending")

    assert any(row["edge"] > 0 for row in edges)
    assert any(row["edge"] < 0 for row in edges)


def test_recommendation_conservation_gate() -> None:
    mapper = RegimePerformanceMapper(_seed_store(), TradingPreset())
    text = mapper.regime_recommendation(
        "trending",
        {"categories": {"trend_following": {"status": "AMBER"}}},
    )

    assert "Hold sizing on trend_following" in text


def test_recommendation_excludes_red_categories() -> None:
    mapper = RegimePerformanceMapper(_seed_store(), TradingPreset())
    text = mapper.regime_recommendation(
        "trending",
        {"categories": {"trend_following": {"status": "RED"}}},
    )

    assert "Your edge: trend_following" not in text
    assert "Hold sizing on trend_following" in text


def test_router_recommendation_gate() -> None:
    response = _client(_seed_store()).get("/api/trading/regime/recommendation")

    assert response.status_code == 200
    for shift in response.json()["shifts"]:
        if shift["conservation_status"] != "GREEN":
            assert shift["direction"] != "increase"


def test_recommendation_nl_format() -> None:
    mapper = RegimePerformanceMapper(_seed_store(), TradingPreset())
    text = mapper.regime_recommendation(
        "trending",
        {"categories": {"trend_following": {"status": "GREEN"}}},
    )

    assert "Current: trending conditions." in text
    assert "VIX" not in text
    assert "ADX" not in text


def test_recommendation_volatile() -> None:
    store = InMemoryGraphStore(domain="trading")
    _seed_decisions(store, "income_strategy", "volatile", correct=10, incorrect=0)
    _seed_decisions(store, "income_strategy", "ranging", correct=5, incorrect=5)
    mapper = RegimePerformanceMapper(store, TradingPreset())

    text = mapper.regime_recommendation("volatile", {"categories": {"income_strategy": {"status": "GREEN"}}})

    assert "income_strategy" in text
    assert "volatile conditions" in text


def test_recommendation_no_data() -> None:
    mapper = RegimePerformanceMapper(InMemoryGraphStore(domain="trading"), TradingPreset())

    assert mapper.regime_recommendation("ranging", {}) == "Score more verified trades before changing regime sizing."


def test_regime_endpoint_current() -> None:
    response = _client().get("/api/trading/regime/current")

    assert response.status_code == 200
    payload = response.json()
    assert payload["regime"] in {"trending", "ranging", "volatile"}
    assert 0 <= payload["hurst"] <= 1


def test_regime_endpoint_history() -> None:
    client = _client()
    client.get("/api/trading/regime/current")

    response = client.get("/api/trading/regime/history")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_regime_endpoint_performance() -> None:
    response = _client(_seed_store()).get("/api/trading/regime/performance")

    assert response.status_code == 200
    assert "per_regime_accuracy" in response.json()


def test_regime_endpoint_recommendation() -> None:
    response = _client(_seed_store()).get("/api/trading/regime/recommendation")

    assert response.status_code == 200
    assert "shifts" in response.json()


def test_negative_vix() -> None:
    assert RegimeClassifier().classify(-1, 30) in {"trending", "ranging", "volatile"}


def test_zero_adx() -> None:
    assert RegimeClassifier().classify(10, 0) == "ranging"


def test_extreme_vix() -> None:
    result = RegimeClassifier().classify_with_confidence(80, 0)

    assert result["regime"] == "volatile"
    assert result["confidence"] == 1.0


def _client(store: InMemoryGraphStore | None = None) -> TestClient:
    app = FastAPI()
    graph_store = store or InMemoryGraphStore(domain="trading")
    app.include_router(
        create_regime_router(
            lambda: graph_store,
            provider_factory=lambda: _Provider(),
            history=RegimeHistory(),
        )
    )
    return TestClient(app)


class _Provider:
    def get_vix_current(self) -> Provenanced[float]:
        return Provenanced(value=18.0, source="sample", as_of="2026-06-01T00:00:00+00:00")

    def get_ohlcv(self, *_args: Any, **_kwargs: Any) -> Provenanced[list[dict[str, float]]]:
        return Provenanced(
            value=[
                {"high": 100.0 + index, "low": 95.0 + index, "close": 98.0 + index}
                for index in range(30)
            ],
            source="sample",
            as_of="2026-06-01T00:00:00+00:00",
        )


def _seed_store() -> InMemoryGraphStore:
    store = InMemoryGraphStore(domain="trading")
    _seed_decisions(store, "trend_following", "trending", correct=10, incorrect=0)
    _seed_decisions(store, "trend_following", "ranging", correct=5, incorrect=5)
    _seed_decisions(store, "mean_reversion", "trending", correct=2, incorrect=8)
    _seed_decisions(store, "mean_reversion", "ranging", correct=9, incorrect=1)
    return store


def _seed_decisions(
    store: InMemoryGraphStore,
    category: str,
    regime: str,
    *,
    correct: int,
    incorrect: int,
) -> None:
    for index in range(correct + incorrect):
        is_correct = index < correct
        decision_id = store.write_decision(
            "trading",
            category,
            "strong_execution",
            0.8,
            {"market_regime": 0.7},
            metadata={"regime": regime, "decision_id": f"{category}-{regime}-{index}"},
        )
        store.write_outcome(
            decision_id,
            "strong_execution",
            is_correct=is_correct,
            metadata={"context": {"regime": regime}},
            domain="trading",
        )
