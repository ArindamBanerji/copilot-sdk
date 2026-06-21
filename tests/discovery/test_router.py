from types import SimpleNamespace

import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.discovery_router import create_discovery_router
from copilot_sdk.discovery import ConservationAlignmentPattern, DiscoveryEngine


class FakeScorer:  # MOCK-OK: discovery router reads phase/alpha/centroids only
    def __init__(self, phase="A"):
        self.gae_scorer = SimpleNamespace(centroids=np.ones((1, 1, 2)))
        self._phase = phase

    def get_phase(self):
        return self._phase

    def get_alpha(self):
        return 0.8


def _client():
    engine = DiscoveryEngine(patterns=[ConservationAlignmentPattern()])
    engine.register_copilot("left", FakeScorer(phase="B"))
    engine.register_copilot("right", FakeScorer(phase="B"))
    app = FastAPI()
    app.include_router(create_discovery_router(engine))
    return TestClient(app)


def test_sweep_returns_200_and_new_alerts():
    client = _client()

    response = client.post("/api/discovery/sweep")

    assert response.status_code == 200
    payload = response.json()
    assert payload["new_alerts"] == 1
    assert len(payload["alerts"]) == 1


def test_digest_returns_alerts():
    client = _client()
    client.post("/api/discovery/sweep")

    response = client.get("/api/discovery/digest")

    assert response.status_code == 200
    assert len(response.json()["alerts"]) == 1


def test_digest_confidence_filter_works():
    client = _client()
    client.post("/api/discovery/sweep")

    response = client.get("/api/discovery/digest?min_confidence=0.9")

    assert response.status_code == 200
    assert response.json()["alerts"] == []


def test_alerts_returns_total():
    client = _client()
    client.post("/api/discovery/sweep")

    response = client.get("/api/discovery/alerts")

    assert response.status_code == 200
    assert response.json()["total"] == 1
