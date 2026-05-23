from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend import scoring_router as scoring_router_module
from copilot_sdk.backend.scoring_router import create_scoring_router
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


class FakeStore:
    def __init__(self) -> None:
        self.domain = "dataops"
        self.decisions: dict[str, dict] = {}

    def save(self, decision: dict) -> None:
        self.decisions[decision["decision_id"]] = decision

    def get_decision(self, decision_id: str) -> dict:
        if decision_id not in self.decisions:
            raise KeyError(decision_id)
        return self.decisions[decision_id]

    def get_decisions(self, domain: str, category: str | None = None, limit: int = 400) -> list[dict]:
        decisions = [
            decision
            for decision in self.decisions.values()
            if category is None or decision.get("category") == category
        ]
        return decisions[:limit]

    def get_all_decisions(self, domain: str) -> list[dict]:
        return list(self.decisions.values())


class FakeScorer:
    def __init__(self) -> None:
        self.graph_store = FakeStore()

    def score(self, factors: dict[str, float], category: str) -> FakeScoreResult:
        if category == "bad":
            raise AssertionError("unknown category: bad")
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

    def learn(
        self,
        decision_id: str,
        actual_action: str,
        outcome: str = "confirmed",
    ) -> FakeLearnResult:
        del actual_action, outcome
        self.graph_store.get_decision(decision_id)
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
            factors=[
                FakeFingerprintFactor(
                    name="impact_scope",
                    sigma=0.12,
                    weight=1.0,
                    interpretation="moderate",
                )
            ],
            overall_win_rate=1.0,
            per_category_precision={"pipeline_failure": 1.0},
            decisions_analyzed=1,
        )

    def trajectory(self) -> FakeTrajectoryResult:
        return FakeTrajectoryResult(
            points=[
                FakeTrajectoryPoint(
                    decisions=0,
                    iks=0.0,
                    win_rate=0.5,
                    timestamp=0.0,
                ),
                FakeTrajectoryPoint(
                    decisions=1,
                    iks=25.1,
                    win_rate=1.0,
                    timestamp=1.0,
                ),
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


class GraphStoreBackedScorer(FakeScorer):
    def __init__(self) -> None:
        super().__init__()
        self.graph_store = InMemoryGraphStore()
        self.learn_calls = []

    def score(self, factors: dict[str, float], category: str) -> FakeScoreResult:
        if category == "bad":
            raise AssertionError("unknown category: bad")
        decision_id = self.graph_store.write_decision(
            "test",
            category=category,
            action="auto_approve",
            confidence=0.72,
            factors=factors,
            metadata={"decision_id": "graph-dec-1", "entity_id": "entity-1"},
        )
        return FakeScoreResult(
            decision_id=decision_id,
            action="auto_approve",
            action_index=0,
            confidence=0.72,
            probabilities=[0.72, 0.28],
            category=category,
            factors=factors,
        )

    def learn(
        self,
        decision_id: str,
        actual_action: str,
        outcome: str = "confirmed",
    ) -> FakeLearnResult:
        self.learn_calls.append((decision_id, actual_action, outcome))
        decision = self.graph_store.get_decision(decision_id)
        if decision is None:
            raise KeyError(decision_id)
        self.graph_store.write_outcome(
            decision_id,
            actual_action,
            actual_action == decision["recommended_action"],
        )
        return FakeLearnResult(
            decision_id=decision_id,
            iks_before=0.0,
            iks_after=25.1,
            centroid_delta=0.012,
            decisions_total=1,
            outcome="applied",
        )


def build_client(domain: str = "dataops", scorer: FakeScorer | None = None) -> TestClient:
    fake = scorer or FakeScorer()
    app = FastAPI()
    app.include_router(create_scoring_router(domain, scorer_factory=lambda: fake))
    return TestClient(app)


def test_factory_creates_apirouter():
    router = create_scoring_router("dataops", scorer_factory=FakeScorer)

    assert isinstance(router, APIRouter)


def test_score_returns_action_confidence_probabilities_and_engine():
    client = build_client()

    response = client.post(
        "/score",
        json={
            "category": "pipeline_failure",
            "factors": {
                "business_criticality": 0.8,
                "impact_scope": 0.5,
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["engine"]["scoring"] == "copilot_sdk.scoring.CompoundingScorer"
    assert payload["engine"]["gae"] == "gae.profile_scorer.ProfileScorer"
    assert payload["action"] == "auto_approve"
    assert payload["confidence"] == 0.72
    assert payload["probabilities"] == [0.72, 0.28]
    assert payload["category"] == "pipeline_failure"


def test_learn_returns_reward_fields_and_engine():
    scorer = FakeScorer()
    client = build_client(scorer=scorer)
    client.post(
        "/score",
        json={
            "category": "pipeline_failure",
            "factors": {
                "business_criticality": 0.8,
                "impact_scope": 0.5,
            },
        },
    )

    response = client.post(
        "/learn",
        json={
            "decision_id": "dec-1",
            "actual_action": "auto_approve",
            "context": {"previous_reward": 0.2},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["engine"]["gae"] == "gae.profile_scorer.ProfileScorer"
    assert payload["reward"] == 0.4
    assert payload["previous_reward"] == 0.2
    assert payload["reward_multiplier"] == 2.0
    assert payload["iks_after"] == 25.1


def test_learn_negative_reward_when_action_incorrect():
    scorer = FakeScorer()
    client = build_client(scorer=scorer)
    client.post(
        "/score",
        json={
            "category": "pipeline_failure",
            "factors": {
                "business_criticality": 0.8,
                "impact_scope": 0.5,
            },
        },
    )

    response = client.post(
        "/learn",
        json={"decision_id": "dec-1", "actual_action": "investigate"},
    )

    assert response.status_code == 200
    assert response.json()["reward"] == -0.4


def test_learn_without_previous_reward_returns_null_and_default_multiplier():
    scorer = FakeScorer()
    client = build_client(scorer=scorer)
    client.post(
        "/score",
        json={
            "category": "pipeline_failure",
            "factors": {
                "business_criticality": 0.8,
                "impact_scope": 0.5,
            },
        },
    )

    response = client.post(
        "/learn",
        json={"decision_id": "dec-1", "actual_action": "auto_approve"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["previous_reward"] is None
    assert payload["reward_multiplier"] == 1.0


def test_learn_with_explicit_zero_previous_reward_keeps_zero_and_default_multiplier():
    scorer = FakeScorer()
    client = build_client(scorer=scorer)
    client.post(
        "/score",
        json={
            "category": "pipeline_failure",
            "factors": {
                "business_criticality": 0.8,
                "impact_scope": 0.5,
            },
        },
    )

    response = client.post(
        "/learn",
        json={
            "decision_id": "dec-1",
            "actual_action": "auto_approve",
            "context": {"previous_reward": 0.0},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["previous_reward"] == 0.0
    assert payload["reward_multiplier"] == 1.0


def test_fingerprint_returns_factor_data_and_engine():
    client = build_client()

    response = client.get("/fingerprint")

    assert response.status_code == 200
    payload = response.json()
    assert payload["engine"]["scoring"] == "copilot_sdk.scoring.CompoundingScorer"
    assert payload["decisions_analyzed"] == 1
    assert payload["factors"][0]["name"] == "impact_scope"


def test_trajectory_returns_points_current_iks_and_engine():
    client = build_client()

    response = client.get("/trajectory")

    assert response.status_code == 200
    payload = response.json()
    assert payload["engine"]["gae"] == "gae.profile_scorer.ProfileScorer"
    assert payload["current_iks"] == 25.1
    assert len(payload["points"]) == 2


def test_health_endpoint_returns_phase_and_alpha():
    client = build_client()

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["phase"] == "B"
    assert payload["alpha"] == 0.8125


def test_health_endpoint_returns_engine():
    client = build_client()

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["engine"]["scoring"] == "copilot_sdk.scoring.CompoundingScorer"
    assert payload["engine"]["gae"] == "gae.profile_scorer.ProfileScorer"


def test_history_returns_empty_then_populated_decisions():
    scorer = FakeScorer()
    client = build_client(scorer=scorer)

    empty = client.get("/history")
    assert empty.status_code == 200
    assert empty.json()["decisions"] == []

    client.post(
        "/score",
        json={
            "category": "pipeline_failure",
            "factors": {
                "business_criticality": 0.8,
                "impact_scope": 0.5,
            },
        },
    )
    populated = client.get("/history")

    assert populated.status_code == 200
    assert len(populated.json()["decisions"]) == 1


def test_learn_prelookup_prefers_graph_store_over_legacy_store():
    scorer = GraphStoreBackedScorer()
    client = build_client(scorer=scorer)
    score = client.post(
        "/score",
        json={
            "category": "pipeline_failure",
            "factors": {
                "business_criticality": 0.8,
                "impact_scope": 0.5,
            },
        },
    ).json()

    response = client.post(
        "/learn",
        json={"decision_id": score["decision_id"], "actual_action": "auto_approve"},
    )

    assert response.status_code == 200
    assert scorer.graph_store.count_verified("test") == 1
    assert scorer.learn_calls == [("graph-dec-1", "auto_approve", "confirmed")]


def test_history_prefers_graph_store_over_legacy_store():
    scorer = GraphStoreBackedScorer()
    client = build_client(scorer=scorer)
    client.post(
        "/score",
        json={
            "category": "pipeline_failure",
            "factors": {
                "business_criticality": 0.8,
                "impact_scope": 0.5,
            },
        },
    )

    response = client.get("/history")

    assert response.status_code == 200
    decisions = response.json()["decisions"]
    assert [decision["decision_id"] for decision in decisions] == ["graph-dec-1"]
    assert scorer.graph_store.get_all_decisions("test") == decisions


def test_scoring_router_uses_graph_store_only():
    source = Path(scoring_router_module.__file__).read_text(encoding="utf-8")
    assert '"graph_store"' in source
    assert '"_graph_store"' in source
    assert '"store"' not in source
    assert '"_store"' not in source


def test_invalid_score_input_returns_400():
    client = build_client()

    response = client.post("/score", json={"category": "bad", "factors": {}})

    assert response.status_code == 400
    assert "unknown category" in response.json()["detail"]


def test_missing_decision_on_learn_returns_404():
    client = build_client()

    response = client.post(
        "/learn",
        json={"decision_id": "missing", "actual_action": "auto_approve"},
    )

    assert response.status_code == 404
    assert "Unknown decision" in response.json()["detail"]


def test_unknown_domain_returns_clear_404():
    app = FastAPI()
    app.include_router(create_scoring_router("does-not-exist"))
    client = TestClient(app)

    response = client.get("/history")

    assert response.status_code == 404
    assert "Unknown preset" in response.json()["detail"]


def test_no_forbidden_modules_loaded():
    import sys

    build_client().get("/history")

    assert not any("domains.soc" in module for module in sys.modules)
    assert not any("domains.s2p" in module for module in sys.modules)
    assert not any("gen-ai-roi-demo" in module for module in sys.modules)
