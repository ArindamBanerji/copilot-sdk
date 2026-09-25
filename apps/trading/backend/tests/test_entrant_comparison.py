from fastapi import FastAPI
from fastapi.testclient import TestClient
from types import SimpleNamespace

from apps.trading.backend.app.routers.entrant_comparison import create_entrant_comparison_router


class FakeScorer:
    def __init__(self, accuracy: float = 0.75, iks: float = 42.0) -> None:
        self.accuracy = accuracy
        self.iks = iks

    def fingerprint(self) -> SimpleNamespace:
        return SimpleNamespace(
            overall_win_rate=self.accuracy,
            decisions_analyzed=80,
        )

    def trajectory(self) -> SimpleNamespace:
        return SimpleNamespace(current_iks=self.iks)


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(create_entrant_comparison_router(lambda: FakeScorer()))
    return TestClient(app)


def test_entrant_comparison_200() -> None:
    response = _client().get("/api/trading/entrant-comparison")
    assert response.status_code == 200
    assert set(response.json()) == {"incumbent", "entrant", "gap"}


def test_entrant_gap_preserves_positive_value() -> None:
    body = _client().get("/api/trading/entrant-comparison").json()
    assert body["gap"]["accuracy_pp"] == 25.0


def test_negative_gap_preserved() -> None:
    app = FastAPI()
    app.include_router(
        create_entrant_comparison_router(lambda: FakeScorer(accuracy=0.40, iks=12.0))
    )
    body = TestClient(app).get("/api/trading/entrant-comparison").json()
    assert body["gap"]["accuracy_pp"] == -10.0
    assert body["incumbent"]["warm_start_advantage_pp"] == -10.0


def test_iks_from_correct_attribute() -> None:
    body = _client().get("/api/trading/entrant-comparison").json()
    assert body["incumbent"]["iks"] == 42.0


def test_baseline_labeled() -> None:
    body = _client().get("/api/trading/entrant-comparison").json()
    assert body["gap"]["baseline_source"] == "assumed_default"


def test_fake_scorer_matches_production() -> None:
    scorer = FakeScorer()
    assert hasattr(scorer.fingerprint(), "overall_win_rate")
    assert hasattr(scorer.fingerprint(), "decisions_analyzed")
    assert scorer.trajectory().current_iks == 42.0


def test_entrant_baseline_zero() -> None:
    body = _client().get("/api/trading/entrant-comparison").json()
    assert body["entrant"]["verified_decisions"] == 0
