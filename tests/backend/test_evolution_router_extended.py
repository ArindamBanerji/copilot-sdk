from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.evolution_router import create_evolution_router


class FakeEvolver:
    def __init__(self):
        self.history_calls = []

    def get_active_rules(self):
        return {"rule-b": object(), "rule-a": object()}

    def get_promoted_rules(self):
        return ["rule-a"]

    def get_evolution_history(self, rule_name=None, limit=50):
        self.history_calls.append((rule_name, limit))
        return [
            {
                "event_type": "promoted",
                "rule_name": rule_name or "rule-a",
                "variant_id": "variant-a",
            }
        ]


def _client(**kwargs):
    app = FastAPI()
    app.include_router(create_evolution_router(**kwargs))
    return TestClient(app)


def test_evolver_factory_is_accepted_and_used():
    evolver = FakeEvolver()
    client = _client(domain="trading", evolver_factory=lambda: evolver)

    payload = client.get("/api/evolution/variants").json()

    assert payload["domain"] == "trading"
    assert payload["active_rules"] == ["rule-a", "rule-b"]
    assert payload["promoted_rules"] == ["rule-a"]


def test_evolver_factory_cached_per_router_instance():
    calls = []

    def factory():
        calls.append(FakeEvolver())
        return calls[-1]

    client = _client(evolver_factory=factory)

    client.get("/api/evolution/variants")
    client.get("/api/evolution/history")
    client.get("/api/evolution/promoted")

    assert len(calls) == 1


def test_evolver_factory_none_falls_back_safely():
    client = _client(domain="dataops", evolver_factory=None)

    assert client.get("/api/evolution/variants").status_code == 200
    assert client.get("/api/evolution/history").status_code == 200
    assert client.get("/api/evolution/promoted").status_code == 200


def test_history_delegates_query_to_evolver_factory():
    evolver = FakeEvolver()
    client = _client(evolver_factory=lambda: evolver)

    payload = client.get("/api/evolution/history?rule_name=rule-x&limit=7").json()

    assert payload["events"][0]["rule_name"] == "rule-x"
    assert evolver.history_calls == [("rule-x", 7)]
