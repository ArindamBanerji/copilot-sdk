from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.switching_cost_router import create_switching_cost_router


class FakeScorer:
    def __init__(self, decisions: list[dict[str, str]]) -> None:
        self.decisions = decisions

    def count_decisions(self) -> int:
        return len(self.decisions)


def _client(
    scorer: Any,
    *,
    percentage: float = 50.0,
    now: datetime | None = None,
) -> TestClient:
    app = FastAPI()
    app.include_router(
        create_switching_cost_router(
            scorer,
            labeled_stream_to_close_pct=percentage,
            now=(lambda: now) if now is not None else None,
        ),
        prefix="/api",
    )
    return TestClient(app)


def test_switching_cost_zero_decisions() -> None:
    response = _client(FakeScorer([])).get("/api/metrics/switching-cost")
    assert response.json() == {
        "decisions_accumulated": 0,
        "equivalent_calendar_days": 0.0,
        "labeled_stream_to_close_pct": 0.0,
    }


def test_switching_cost_with_decisions() -> None:
    scorer = FakeScorer([{"created_at": "2026-09-01T00:00:00+00:00"}] * 3)
    payload = _client(scorer, now=datetime(2026, 9, 4, tzinfo=timezone.utc)).get(
        "/api/metrics/switching-cost"
    ).json()
    assert payload["decisions_accumulated"] == 3


def test_switching_cost_calendar_calculation() -> None:
    scorer = FakeScorer([{"created_at": "2026-09-01T00:00:00+00:00"}] * 2)
    payload = _client(scorer, now=datetime(2026, 9, 6, tzinfo=timezone.utc)).get(
        "/api/metrics/switching-cost"
    ).json()
    assert payload["equivalent_calendar_days"] == 5.0


def test_switching_cost_labeled_stream_default() -> None:
    payload = _client(FakeScorer([{}]), now=datetime(2026, 9, 2, tzinfo=timezone.utc)).get(
        "/api/metrics/switching-cost"
    ).json()
    assert payload["labeled_stream_to_close_pct"] == 50.0


def test_switching_cost_labeled_stream_custom() -> None:
    payload = _client(FakeScorer([{}]), percentage=62.5).get("/api/metrics/switching-cost").json()
    assert payload["labeled_stream_to_close_pct"] == 62.5


def test_switching_cost_endpoint_200() -> None:
    assert _client(FakeScorer([])).get("/api/metrics/switching-cost").status_code == 200


def test_switching_cost_endpoint_shape() -> None:
    payload = _client(FakeScorer([])).get("/api/metrics/switching-cost").json()
    assert set(payload) == {
        "decisions_accumulated",
        "equivalent_calendar_days",
        "labeled_stream_to_close_pct",
    }


def test_switching_cost_no_first_decision() -> None:
    class CountOnlyScorer:
        def get_decision_count(self) -> int:
            return 3

    payload = _client(CountOnlyScorer()).get("/api/metrics/switching-cost").json()
    assert payload["decisions_accumulated"] == 3
    assert payload["equivalent_calendar_days"] == 0.0

def test_switching_cost_with_real_store(tmp_path: "Path") -> None:
    from copilot_sdk.backend.scorer_proxy import FreshScorerProxy
    from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
    from copilot_sdk.scoring.presets.trading import TradingPreset

    proxy = FreshScorerProxy(
        "trading", tmp_path / "switching.db",
        graph_store_factory=lambda path: SQLiteGraphStore(path, domain="trading"),
        profile="test",
    )
    try:
        preset = TradingPreset()
        factors = {name: 0.8 for name in preset.shape.factor_names}
        for category in preset.shape.category_names:
            result = proxy.score(factors, category)
            proxy.learn(result.decision_id, result.action)
        assert proxy.graph_store.count_verified("trading") == 5
        app = FastAPI()
        app.include_router(create_switching_cost_router(proxy, domain="trading"), prefix="/api")
        with TestClient(app) as client:
            response = client.get("/api/metrics/switching-cost")
        assert response.status_code == 200
        assert response.json()["decisions_accumulated"] == 5
        assert response.json()["equivalent_calendar_days"] >= 0
    finally:
        proxy.graph_store.close()
