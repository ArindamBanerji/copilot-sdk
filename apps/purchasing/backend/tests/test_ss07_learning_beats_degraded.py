from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.learning_beats import create_learning_beats_router


class BrokenGraph:
    def get_verified_decisions(self, _domain: str):
        raise RuntimeError("offline")

    def get_latest_conservation_statuses(self, _domain: str):
        raise RuntimeError("offline")


def _client() -> TestClient:
    app = FastAPI()
    scorer = SimpleNamespace(
        graph_store=BrokenGraph(),
        trajectory=lambda: {"current_iks": 0.0},
    )
    app.include_router(create_learning_beats_router(scorer))
    return TestClient(app)


def test_learning_hero_marks_verified_history_unavailable() -> None:
    payload = _client().get("/api/purchasing/learning/hero").json()

    assert payload["verified_count"] == 0
    assert payload["verified_available"] is False
    assert payload["conservation_status"] == "UNAVAILABLE"
    assert payload["data_available"] is False


def test_learning_stats_does_not_claim_bootstrap_after_conservation_failure() -> None:
    payload = _client().get("/api/purchasing/learning/hero").json()

    assert payload["conservation_available"] is False
    assert payload["degraded"] is True
    assert payload["conservation_status"] != "BOOTSTRAP"
