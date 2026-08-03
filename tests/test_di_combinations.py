from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.di_router import create_di_router


class FakeMapBuilder:
    def discover_combinations(self) -> list[dict[str, object]]:
        return [
            {
                "source_a": "sap_s4hana",
                "source_b": "shipping_data",
                "correlation_strength": 0.87,
                "value_estimate_annual": 180000,
                "description": "Churn prediction improves 23pp",
                "status": "discovered",
            }
        ]

    def build(self) -> dict[str, object]:
        return {
            "nodes": [
                {"id": "sap", "label": "SAP", "trust": 0.94, "size": 340, "type": "source"}
            ],
            "edges": [
                {"source": "sap", "target": "shipping", "weight": 0.87, "type": "correlation"}
            ],
            "gold_lines": [
                {"source": "orders", "target": "weather", "value": 180000, "type": "suggested"}
            ],
        }


class FakeAdvisor:
    def __init__(self, recommendations: list[dict[str, object]] | None = None) -> None:
        self.recommendations = [
            {
                "source_name": "Weather API",
                "provider": "OpenWeatherMap",
                "cost": "free",
                "improvement_estimate_pp": 15,
                "value_estimate_annual": 180000,
                "rationale": "Demand prediction improves with weather",
                "priority": 1,
            }
        ] if recommendations is None else recommendations

    def recommend(self) -> list[dict[str, object]]:
        return self.recommendations


def _client(
    map_builder: FakeMapBuilder | None = None,
    advisor: FakeAdvisor | None = None,
) -> TestClient:
    app = FastAPI()
    app.include_router(
        create_di_router(
            {},
            map_builder=map_builder or FakeMapBuilder(),
            advisor=advisor or FakeAdvisor(),
        ),
        prefix="/api",
    )
    return TestClient(app)


def test_combinations_returns_list() -> None:
    payload = _client().get("/api/di/combinations").json()

    assert isinstance(payload["combinations"], list)
    assert payload["combinations"]


def test_combinations_have_value_estimates() -> None:
    combinations = _client().get("/api/di/combinations").json()["combinations"]

    assert combinations[0]["value_estimate_annual"] > 0


def test_combinations_have_correlation_strength() -> None:
    combinations = _client().get("/api/di/combinations").json()["combinations"]

    assert 0.0 <= combinations[0]["correlation_strength"] <= 1.0


def test_acquisition_returns_recommendations() -> None:
    payload = _client().get("/api/di/acquisition-advice").json()

    assert payload["recommendations"]


def test_acquisition_recommendations_have_priority_and_rationale() -> None:
    recommendation = _client().get("/api/di/acquisition-advice").json()["recommendations"][0]

    assert recommendation["priority"] == 1
    assert recommendation["rationale"]


def test_intelligence_map_returns_nodes_and_edges() -> None:
    payload = _client().get("/api/di/intelligence-map").json()

    assert payload["nodes"]
    assert payload["edges"]


def test_intelligence_map_nodes_have_trust() -> None:
    nodes = _client().get("/api/di/intelligence-map").json()["nodes"]

    assert nodes[0]["trust"] == 0.94


def test_intelligence_map_includes_gold_lines() -> None:
    gold_lines = _client().get("/api/di/intelligence-map").json()["gold_lines"]

    assert gold_lines[0]["type"] == "suggested"


def test_empty_advisor_returns_empty_list() -> None:
    payload = _client(advisor=FakeAdvisor([])).get("/api/di/acquisition-advice").json()

    assert payload["recommendations"] == []
