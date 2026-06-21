from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from copilot_sdk.backend.conservation_router import create_conservation_router
from copilot_sdk.backend.discovery_router import create_discovery_router
from copilot_sdk.backend.evolution_router import create_evolution_router
from copilot_sdk.backend.models import (
    AccuracyByCategoryResponse,
    CentroidHistoryResponse,
    ConservationStatusResponse,
    ConservationWhatIfResponse,
    DecisionFlowResponse,
    DiscoveryAlertsResponse,
    DiscoveryDigestResponse,
    DiscoverySweepResponse,
    EvolutionHistoryResponse,
    EvolutionPromotedResponse,
    EvolutionVariantsResponse,
    FingerprintResponse,
    LearnResponse,
    ScoreResponse,
    ScoringHealthResponse,
    ScoringHistoryResponse,
    SelfDecisionsResponse,
    TrajectoryResponse,
    TransferActiveResponse,
    TransferInactiveResponse,
)
from copilot_sdk.backend.scoring_router import create_scoring_router
from copilot_sdk.backend.self_computation_router import mount_self_computation_router
from copilot_sdk.backend.transfer_router import create_transfer_router
from copilot_sdk.discovery import ConservationAlignmentPattern, DiscoveryEngine
from copilot_sdk.graph import InMemoryGraphStore


@dataclass(frozen=True)
class FakeScoreResult:
    decision_id: str
    action: str
    action_index: int
    confidence: float
    probabilities: list[float]
    category: str
    factors: dict[str, float]


@dataclass(frozen=True)
class FakeLearnResult:
    decision_id: str
    iks_before: float
    iks_after: float
    centroid_delta: float
    decisions_total: int
    outcome: str


@dataclass(frozen=True)
class FakeFingerprintFactor:
    name: str
    sigma: float
    weight: float
    interpretation: str


@dataclass(frozen=True)
class FakeFingerprintResult:
    factors: list[FakeFingerprintFactor]
    overall_win_rate: float
    per_category_precision: dict[str, float]
    decisions_analyzed: int


@dataclass(frozen=True)
class FakeTrajectoryPoint:
    decisions: int
    iks: float
    win_rate: float
    timestamp: float


@dataclass(frozen=True)
class FakeTrajectoryResult:
    points: list[FakeTrajectoryPoint]
    current_iks: float
    current_win_rate: float
    decisions_total: int
    days_active: float


class FakeStore:  # MOCK-OK: response model fixture store, no conservation behavior
    domain = "dataops"

    def __init__(self) -> None:
        self.decisions: dict[str, dict[str, Any]] = {}

    def save(self, decision: dict[str, Any]) -> None:
        self.decisions[decision["decision_id"]] = decision

    def get_decision(self, decision_id: str) -> dict[str, Any] | None:
        return self.decisions.get(decision_id)

    def get_decisions(self, domain: str, category: str | None = None, limit: int = 400) -> list[dict[str, Any]]:
        del domain
        decisions = [
            decision
            for decision in self.decisions.values()
            if category is None or decision.get("category") == category
        ]
        return decisions[:limit]

    def get_all_decisions(self, domain: str) -> list[dict[str, Any]]:
        del domain
        return list(self.decisions.values())


class FakeScorer:  # MOCK-OK: response model fixture, real scorer covered elsewhere
    def __init__(self) -> None:
        self.graph_store = FakeStore()

    def score(self, factors: dict[str, float], category: str) -> FakeScoreResult:
        result = FakeScoreResult(
            decision_id="dec-1",
            action="auto_approve",
            action_index=0,
            confidence=0.72,
            probabilities=[0.72, 0.28],
            category=category,
            factors=factors,
        )
        self.graph_store.save(
            {
                "decision_id": result.decision_id,
                "category": category,
                "factors": factors,
                "recommended_action": result.action,
                "confidence": result.confidence,
            }
        )
        return result

    def learn(self, decision_id: str, actual_action: str, outcome: str = "confirmed") -> FakeLearnResult:
        del actual_action, outcome
        return FakeLearnResult(
            decision_id=decision_id,
            iks_before=0.0,
            iks_after=25.1,
            centroid_delta=0.012,
            decisions_total=1,
            outcome="applied",
        )

    def fingerprint(self) -> FakeFingerprintResult:
        return FakeFingerprintResult(
            factors=[FakeFingerprintFactor("impact_scope", 0.12, 1.0, "moderate")],
            overall_win_rate=1.0,
            per_category_precision={"pipeline_failure": 1.0},
            decisions_analyzed=1,
        )

    def trajectory(self) -> FakeTrajectoryResult:
        return FakeTrajectoryResult(
            points=[
                FakeTrajectoryPoint(0, 0.0, 0.5, 0.0),
                FakeTrajectoryPoint(1, 25.1, 1.0, 1.0),
            ],
            current_iks=25.1,
            current_win_rate=1.0,
            decisions_total=1,
            days_active=0.0,
        )

    def get_phase(self) -> str:
        return "B"

    def get_alpha(self) -> float:
        return 0.8125


class FakeDiscoveryScorer:
    def __init__(self, phase: str = "B") -> None:
        self._phase = phase

    def get_phase(self) -> str:
        return self._phase

    def get_alpha(self) -> float:
        return 0.8


class FakeEvolver:
    def get_active_rules(self) -> dict[str, object]:
        return {"rule-b": object(), "rule-a": object()}

    def get_promoted_rules(self) -> list[str]:
        return ["rule-a"]

    def get_evolution_history(self, rule_name: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        del limit
        return [{"event_type": "promoted", "rule_name": rule_name or "rule-a"}]


class FakeWarmScorer:
    _warm_start_info = {
        "source_copilot": "source",
        "patterns_transferred": 3,
        "transferred_at": "2026-01-01T00:00:00Z",
    }


def _scoring_client() -> TestClient:
    app = FastAPI()
    app.include_router(create_scoring_router("dataops", scorer_factory=FakeScorer))
    return TestClient(app)


def _self_store() -> InMemoryGraphStore:
    store = InMemoryGraphStore(domain="banking")
    d1 = store.write_decision(
        "banking",
        category="fraud_review",
        action="investigate",
        confidence=0.9,
        factors={"severity": 0.8},
        metadata={"decision_id": "d1", "created_at": 1.0},
    )
    store.write_outcome(d1, actual_action="investigate", is_correct=True, metadata={"reward": 0.8})
    store.save_centroids("banking", "fraud_review", {"centroid": [0.1]}, metadata={"iks": 10.0}, decision_id=d1)
    return store


def test_scoring_responses_validate_against_models() -> None:
    client = _scoring_client()
    score = client.post(
        "/score",
        json={"category": "pipeline_failure", "factors": {"business_criticality": 0.8, "impact_scope": 0.5}},
    )
    assert score.status_code == 200
    ScoreResponse.model_validate(score.json())

    learn = client.post("/learn", json={"decision_id": score.json()["decision_id"], "actual_action": "auto_approve"})
    assert learn.status_code == 200
    LearnResponse.model_validate(learn.json())

    FingerprintResponse.model_validate(client.get("/fingerprint").json())
    TrajectoryResponse.model_validate(client.get("/trajectory").json())
    ScoringHealthResponse.model_validate(client.get("/health").json())
    ScoringHistoryResponse.model_validate(client.get("/history").json())


def test_conservation_responses_validate_against_models() -> None:
    app = FastAPI()
    app.include_router(create_conservation_router("dataops"))
    client = TestClient(app)

    ConservationStatusResponse.model_validate(client.get("/conservation/status").json())
    response = client.post("/conservation/what-if", json={"alpha": 0.5, "q": 0.9, "V": 100.0})
    assert response.status_code == 200
    ConservationWhatIfResponse.model_validate(response.json())


def test_discovery_evolution_self_and_transfer_responses_validate_against_models() -> None:
    discovery = DiscoveryEngine(patterns=[ConservationAlignmentPattern()])
    discovery.register_copilot("left", FakeDiscoveryScorer())
    discovery.register_copilot("right", FakeDiscoveryScorer())

    app = FastAPI()
    app.include_router(create_discovery_router(discovery))
    app.include_router(create_evolution_router(domain="dataops", evolver_factory=FakeEvolver))
    mount_self_computation_router(app, _self_store())
    app.include_router(create_transfer_router(FakeWarmScorer()))
    client = TestClient(app)

    DiscoverySweepResponse.model_validate(client.post("/api/discovery/sweep").json())
    DiscoveryDigestResponse.model_validate(client.get("/api/discovery/digest").json())
    DiscoveryAlertsResponse.model_validate(client.get("/api/discovery/alerts").json())
    EvolutionVariantsResponse.model_validate(client.get("/api/evolution/variants").json())
    EvolutionHistoryResponse.model_validate(client.get("/api/evolution/history").json())
    EvolutionPromotedResponse.model_validate(client.get("/api/evolution/promoted").json())
    CentroidHistoryResponse.model_validate(client.get("/api/self/centroid-history").json())
    AccuracyByCategoryResponse.model_validate(client.get("/api/self/accuracy-by-category").json())
    SelfDecisionsResponse.model_validate(client.get("/api/self/decisions").json())
    DecisionFlowResponse.model_validate(client.get("/api/self/decision-flow").json())
    TypeAdapter(TransferActiveResponse | TransferInactiveResponse).validate_python(
        client.get("/api/transfer/status").json()
    )


def test_openapi_references_response_models() -> None:
    app = FastAPI()
    app.include_router(create_scoring_router("dataops", scorer_factory=FakeScorer))
    app.include_router(create_conservation_router("dataops"))
    app.include_router(create_evolution_router(domain="dataops", evolver_factory=FakeEvolver))
    mount_self_computation_router(app, _self_store())
    schema = app.openapi()
    schemas = schema["components"]["schemas"]

    for name in [
        "ScoreResponse",
        "LearnResponse",
        "ConservationStatusResponse",
        "EvolutionVariantsResponse",
        "DecisionFlowResponse",
    ]:
        assert name in schemas

    assert _response_ref(schema, "/score", "post") == "#/components/schemas/ScoreResponse"
    assert _response_ref(schema, "/learn", "post") == "#/components/schemas/LearnResponse"
    assert _response_ref(schema, "/conservation/status", "get") == "#/components/schemas/ConservationStatusResponse"
    assert _response_ref(schema, "/api/evolution/variants", "get") == "#/components/schemas/EvolutionVariantsResponse"
    assert _response_ref(schema, "/api/self/decision-flow", "get") == "#/components/schemas/DecisionFlowResponse"
    audit_schema = schema["paths"]["/api/self/audit-trail"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert "$ref" not in audit_schema


def _response_ref(schema: dict[str, Any], path: str, method: str) -> str:
    return schema["paths"][path][method]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
