from __future__ import annotations

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.trust_router import create_trust_router




class _TrustScorer:
    def __init__(self):
        self.graph_store = InMemoryGraphStore(domain="dataops")
        for index in range(340):
            decision_id = self.graph_store.write_decision("dataops", "pipeline_failure", "investigate",
                0.8, {"impact_scope": 0.5})
            self.graph_store.write_outcome(decision_id, "investigate" if index < 260 else "pause_downstream",
                                          index < 260, domain="dataops")

    def fingerprint(self) -> dict[str, object]:
        return {
            "factors": [
                {"name": "impact_scope", "weight": 0.87},
                {"name": "source_reliability", "weight": 0.94},
                {"name": "recurrence_frequency", "weight": 0.23},
                {"name": "downstream_urgency", "weight": 0.61},
                {"name": "data_freshness", "weight": 0.18},
                {"name": "business_criticality", "weight": 0.88},
            ],
            "decisions_analyzed": self.graph_store.count_verified("dataops"),
        }

    def trajectory(self) -> dict[str, float]:
        return {"current_iks": 19.0}


def _client() -> TestClient:
    app = FastAPI()
    scorer = _TrustScorer()
    app.state.scorer = scorer
    app.include_router(create_trust_router("dataops", lambda: scorer))
    return TestClient(app)


def test_trust_returns_6_factors() -> None:
    response = _client().get("/dataops/trust")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["factors"]) == 6
    assert {factor["name"] for factor in payload["factors"]} == {
        "impact_scope",
        "source_reliability",
        "recurrence_frequency",
        "downstream_urgency",
        "data_freshness",
        "business_criticality",
    }


def test_trust_overall_is_weighted_average() -> None:
    payload = _client().get("/dataops/trust").json()

    expected = (0.87 + 0.94 + 0.23 + 0.61 + 0.18 + 0.88) / 6
    assert payload["overall_trust"] == round(expected, 3)


def test_trust_labels_correct() -> None:
    factors = _client().get("/dataops/trust").json()["factors"]
    labels = {factor["name"]: factor["label"] for factor in factors}

    assert labels["source_reliability"] == "reliable"
    assert labels["business_criticality"] == "reliable"
    assert labels["downstream_urgency"] == "moderate"
    assert labels["recurrence_frequency"] == "noisy"
    assert labels["data_freshness"] == "noisy"


def test_trust_includes_conservation_status() -> None:
    payload = _client().get("/dataops/trust").json()

    assert payload["conservation_status"] in {"GREEN", "AMBER", "RED"}
    assert payload["verified_decisions"] == 340


def test_trust_includes_iks() -> None:
    payload = _client().get("/dataops/trust").json()

    assert payload["iks"] == 19.0


def test_trust_narrative_mentions_highest_and_lowest() -> None:
    payload = _client().get("/dataops/trust").json()

    assert "source_reliability" in payload["narrative"]
    assert "data_freshness" in payload["narrative"]


def test_trust_counts_refresh_after_graph_outcome():
    client = _client()
    store = client.app.state.scorer.graph_store
    before = client.get("/dataops/trust").json()["verified_decisions"]
    decision_id = store.write_decision("dataops", "pipeline_failure", "investigate", 0.8, {"impact_scope": 0.5})
    store.write_outcome(decision_id, "investigate", True, domain="dataops")
    assert client.get("/dataops/trust").json()["verified_decisions"] == before + 1 == store.count_verified("dataops")
