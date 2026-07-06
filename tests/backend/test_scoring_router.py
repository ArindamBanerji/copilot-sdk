from __future__ import annotations

import math
import threading
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import numpy as np
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend import scoring_router as scoring_router_module
from copilot_sdk.backend.conservation_utils import compute_conservation_metrics
from copilot_sdk.backend.models import LearnResponse
from copilot_sdk.backend.scoring_router import create_scoring_router
from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer


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


class FakeStore:  # MOCK-OK: scoring router contract fixture, no production conservation path
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


class FakeScorer:  # MOCK-OK: scoring router contract fixture, real scorer tests cover scorer behavior
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


class PausingScorer(FakeScorer):
    def learn(
        self,
        decision_id: str,
        actual_action: str,
        outcome: str = "confirmed",
    ) -> dict:
        del decision_id, actual_action, outcome
        return {
            "status": "paused",
            "reason": "conservation_red",
            "q": 0.0,
            "override_rate": 1.0,
            "theta_min": 0.9,
            "verified_count": 7,
            "correct_count": 0,
        }


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


class SQLiteL5Scorer(FakeScorer):
    def __init__(self, db_path: Path) -> None:
        super().__init__()
        self.graph_store = SQLiteGraphStore(db_path, domain="test")
        self._preset = SimpleNamespace(
            shape=SimpleNamespace(n_categories=3),
            penalty_ratio=1.0,
        )

    def score(self, factors: dict[str, float], category: str) -> FakeScoreResult:
        decision_id = self.graph_store.write_decision(
            "test",
            category=category,
            action="auto_approve",
            confidence=0.72,
            factors=factors,
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
            outcome=outcome,
        )


class RecordingLearningStore:
    def __init__(self, old_state: dict[str, object] | None = None) -> None:
        self.old_state = old_state
        self.updates: list[dict[str, object]] = []

    def get_conservation_state(self, domain: str) -> dict[str, object] | None:
        assert domain == "test"
        return self.old_state

    def update_conservation_state(self, **kwargs: object) -> str:
        self.updates.append(kwargs)
        return "l5-row"


class FailingReadLearningStore(RecordingLearningStore):
    def get_conservation_state(self, domain: str) -> dict[str, object] | None:
        raise RuntimeError("read failed")


class FailingWriteLearningStore(RecordingLearningStore):
    def update_conservation_state(self, **kwargs: object) -> str:
        raise RuntimeError("write failed")


class RecordingDKLearningStore:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.dk_updates: list[dict[str, object]] = []

    def update_dk_weights(self, **kwargs: object) -> None:
        if self.fail:
            raise RuntimeError("dk write failed")
        self.dk_updates.append(kwargs)


class RecordingCentroidLearningStore:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.centroid_updates: list[dict[str, object]] = []

    def update_centroid(self, **kwargs: object) -> None:
        if self.fail:
            raise RuntimeError("centroid write failed")
        self.centroid_updates.append(kwargs)


class DKRuntimeScorer(FakeScorer):
    def __init__(self, weights: list[list[float]] | None = None) -> None:
        super().__init__()
        self.weights = weights
        self.reestimate_calls = 0
        self.get_weight_calls = 0
        self._counter = 0

    def score(self, factors: dict[str, float], category: str) -> FakeScoreResult:
        self._counter += 1
        result = FakeScoreResult(
            decision_id=f"dk-dec-{self._counter}",
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
                "factor_vector": list(factors.values()),
                "factors": factors,
                "recommended_action": result.action,
                "confidence": result.confidence,
            }
        )
        return result

    def reestimate_dk_if_due(self) -> bool:
        self.reestimate_calls += 1
        return self.weights is not None

    def get_dk_weights(self) -> list[list[float]] | None:
        self.get_weight_calls += 1
        if self.weights is None:
            return None
        return [row[:] for row in self.weights]


class CentroidRuntimeScorer(DKRuntimeScorer):
    def __init__(self, phase: str = "MEAN_CONVERGENCE") -> None:
        super().__init__(weights=None)
        self.phase = phase
        self.centroids: dict[tuple[str, str], list[float]] = {
            ("pipeline_failure", "auto_approve"): [0.2, 0.4],
            ("pipeline_failure", "investigate"): [0.6, 0.8],
        }
        self.save_centroids_calls = 0

    def get_centroid(self, category: str, action: str) -> list[float] | None:
        value = self.centroids.get((category, action))
        return None if value is None else list(value)

    def get_category_phase(self, category: str) -> str:
        assert category == "pipeline_failure"
        return self.phase

    def learn(
        self,
        decision_id: str,
        actual_action: str,
        outcome: str = "confirmed",
    ) -> FakeLearnResult:
        self.graph_store.get_decision(decision_id)
        self.save_centroids_calls += 1
        if self.phase == "MEAN_CONVERGENCE":
            before = self.centroids[("pipeline_failure", actual_action)]
            self.centroids[("pipeline_failure", actual_action)] = [
                before[0] + 0.3,
                before[1] + 0.4,
            ]
        return FakeLearnResult(
            decision_id=decision_id,
            iks_before=0.0,
            iks_after=25.1,
            centroid_delta=0.5,
            decisions_total=1,
            outcome=outcome,
        )


class BlockingDKRuntimeScorer(DKRuntimeScorer):
    def __init__(self) -> None:
        super().__init__(weights=[[0.2]])
        self.graph_store.save(
            {
                "decision_id": "dk-block-1",
                "category": "pipeline_failure",
                "factor_vector": [1.0],
                "recommended_action": "auto_approve",
            }
        )
        self.graph_store.save(
            {
                "decision_id": "dk-block-2",
                "category": "pipeline_failure",
                "factor_vector": [0.0],
                "recommended_action": "auto_approve",
            }
        )
        self.first_reestimate_entered = threading.Event()
        self.second_reestimate_entered = threading.Event()
        self.release_first_reestimate = threading.Event()
        self._reestimate_lock = threading.Lock()
        self._entries = 0

    def reestimate_dk_if_due(self) -> bool:
        with self._reestimate_lock:
            self._entries += 1
            entry = self._entries
        if entry == 1:
            self.first_reestimate_entered.set()
            assert self.release_first_reestimate.wait(5)
        else:
            self.second_reestimate_entered.set()
        self.reestimate_calls += 1
        return True


class ConcurrentGraphStore:
    domain = "test"

    def __init__(self) -> None:
        self.decisions = {
            "dec-1": {
                "decision_id": "dec-1",
                "recommended_action": "auto_approve",
                "factors": {"business_criticality": 0.8},
                "confidence": 0.72,
            },
            "dec-2": {
                "decision_id": "dec-2",
                "recommended_action": "auto_approve",
                "factors": {"business_criticality": 0.8},
                "confidence": 0.72,
            },
        }

    def get_decision(self, decision_id: str) -> dict[str, object] | None:
        return self.decisions.get(decision_id)

    def count_verified(self, domain: str) -> int:
        return 2

    def count_correct(self, domain: str) -> int:
        return 2

    def count_verified_decisions(self, domain: str) -> int:
        return 2

    def count_categories_with_n(self, domain: str, n: int) -> int:
        return 1


class ConcurrentScorer:
    def __init__(self) -> None:
        self.graph_store = ConcurrentGraphStore()
        self._preset = SimpleNamespace(
            shape=SimpleNamespace(n_categories=3),
            penalty_ratio=1.0,
        )

    def learn(
        self,
        decision_id: str,
        actual_action: str,
        outcome: str = "confirmed",
    ) -> FakeLearnResult:
        return FakeLearnResult(
            decision_id=decision_id,
            iks_before=0.0,
            iks_after=25.1,
            centroid_delta=0.012,
            decisions_total=2,
            outcome=outcome,
        )


class DomainAwareCountStore:
    def __init__(
        self,
        *,
        verified: dict[str, int],
        correct: dict[str, int],
        total: dict[str, int],
        categories: dict[str, int],
    ) -> None:
        self.verified = verified
        self.correct = correct
        self.total = total
        self.categories = categories
        self.calls: list[tuple[str, str]] = []

    def count_verified(self, domain: str) -> int:
        self.calls.append(("count_verified", domain))
        return self.verified.get(domain, 0)

    def count_correct(self, domain: str) -> int:
        self.calls.append(("count_correct", domain))
        return self.correct.get(domain, 0)

    def count_verified_decisions(self, domain: str) -> int:
        self.calls.append(("count_verified_decisions", domain))
        return self.total.get(domain, 0)

    def count_categories_with_n(self, domain: str, n: int) -> int:
        self.calls.append(("count_categories_with_n", domain))
        assert n == 1
        return self.categories.get(domain, 0)


class DomainAwareMetricScorer:
    def __init__(self, graph_store: DomainAwareCountStore) -> None:
        self.graph_store = graph_store
        self._preset = SimpleNamespace(
            shape=SimpleNamespace(n_categories=3),
            penalty_ratio=1.0,
        )


class BlockingLearningStore:
    def __init__(self) -> None:
        self.first_get_entered = threading.Event()
        self.second_get_entered = threading.Event()
        self.release_first_get = threading.Event()
        self._lock = threading.Lock()
        self.get_entries = 0
        self.updates: list[dict[str, object]] = []

    def get_conservation_state(self, domain: str) -> dict[str, object] | None:
        with self._lock:
            self.get_entries += 1
            entry = self.get_entries
        if entry == 1:
            self.first_get_entered.set()
            assert self.release_first_get.wait(5)
            return {"status": "RED"}
        self.second_get_entered.set()
        return {"status": "GREEN"}

    def update_conservation_state(self, **kwargs: object) -> str:
        self.updates.append(kwargs)
        return "l5-row"


def build_client(
    domain: str = "dataops",
    scorer: FakeScorer | None = None,
    learning_store: Any | None = None,
) -> TestClient:
    fake = scorer or FakeScorer()
    app = FastAPI()
    app.include_router(
        create_scoring_router(
            domain,
            scorer_factory=lambda: fake,
            learning_store=learning_store,
        )
    )
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
    assert payload["paused"] is False
    assert payload["centroid_updated"] is True
    assert payload["action"] == "auto_approve"
    assert payload["confidence"] == 0.72
    LearnResponse.model_validate(payload)


def test_learn_conservation_pause_returns_learn_response_shape():
    scorer = PausingScorer()
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
    LearnResponse.model_validate(payload)
    assert payload["decision_id"] == "dec-1"
    assert payload["iks_before"] == 0.0
    assert payload["iks_after"] == 0.0
    assert payload["centroid_delta"] == 0.0
    assert payload["decisions_total"] == 7
    assert payload["outcome"] == "confirmed"
    assert payload["paused"] is True
    assert payload["pause_reason"] == "conservation_red"
    assert payload["centroid_updated"] is False
    assert payload["action"] == "auto_approve"
    assert payload["confidence"] == 0.72
    assert payload["status"] == "paused"
    assert payload["reason"] == "conservation_red"


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


def test_conservation_metrics_use_real_category_coverage(tmp_path):
    scorer = SQLiteL5Scorer(tmp_path / "metrics.sqlite")
    decision_id = scorer.score({"business_criticality": 0.8}, "pipeline_failure").decision_id
    scorer.learn(decision_id, "auto_approve")

    metrics = compute_conservation_metrics(scorer, domain="test")

    assert metrics["categories_total"] == 3
    assert metrics["categories_with_data"] == 1
    assert metrics["alpha"] == 1 / 3
    assert metrics["categories_with_data"] == int(float(metrics["alpha"]) * int(metrics["categories_total"]))
    assert metrics["baseline_product"] == 0.0
    assert metrics["relative_threshold"] == 0.0
    assert metrics["complacency_flag"] == "false"
    assert isinstance(metrics["theta_min"], float)


def test_conservation_metrics_use_explicit_domain_for_all_counts():
    store = DomainAwareCountStore(
        verified={"dataops": 12},
        correct={"dataops": 9},
        total={"dataops": 16},
        categories={"dataops": 2},
    )
    scorer = DomainAwareMetricScorer(store)

    metrics = compute_conservation_metrics(scorer, domain="dataops")

    assert metrics["V"] == 12
    assert metrics["alpha"] == 2 / 3
    assert metrics["q"] == 9 / 12
    assert metrics["categories_with_data"] == 2
    assert math.isfinite(float(metrics["theta_min"]))
    assert {
        ("count_verified", "dataops"),
        ("count_correct", "dataops"),
        ("count_verified_decisions", "dataops"),
        ("count_categories_with_n", "dataops"),
    }.issubset(set(store.calls))


def test_conservation_metrics_do_not_bleed_between_live_domains():
    store = DomainAwareCountStore(
        verified={"trading": 4, "purchasing": 20},
        correct={"trading": 2, "purchasing": 18},
        total={"trading": 4, "purchasing": 25},
        categories={"trading": 1, "purchasing": 3},
    )
    scorer = DomainAwareMetricScorer(store)

    metrics = compute_conservation_metrics(scorer, domain="purchasing")

    assert metrics["V"] == 20
    assert metrics["alpha"] == 1.0
    assert metrics["q"] == 18 / 20
    assert metrics["categories_with_data"] == 3
    assert ("count_verified", "trading") not in store.calls
    assert math.isfinite(float(metrics["theta_min"]))


def test_learn_persists_l5_conservation_state_with_graph_store(tmp_path):
    scorer = SQLiteL5Scorer(tmp_path / "l5.sqlite")
    client = build_client(domain="test", scorer=scorer)
    decision_id = client.post(
        "/score",
        json={"category": "pipeline_failure", "factors": {"business_criticality": 0.8}},
    ).json()["decision_id"]

    response = client.post(
        "/learn",
        json={"decision_id": decision_id, "actual_action": "auto_approve"},
    )

    assert response.status_code == 200
    LearnResponse.model_validate(response.json())
    state = scorer.graph_store.get_conservation_state("test")
    assert state is not None
    assert state["domain"] == "test"
    assert state["caused_by_decision_id"] == decision_id
    assert state["old_status"] is None
    assert state["categories_total"] == 3
    assert state["categories_with_data"] == 1
    assert state["complacency_flag"] == "false"


def test_learn_persists_old_status_from_l5_store(tmp_path):
    scorer = SQLiteL5Scorer(tmp_path / "old-status.sqlite")
    learning_store = RecordingLearningStore(old_state={"status": "RED"})
    client = build_client(domain="test", scorer=scorer, learning_store=learning_store)
    decision_id = client.post(
        "/score",
        json={"category": "pipeline_failure", "factors": {"business_criticality": 0.8}},
    ).json()["decision_id"]

    response = client.post(
        "/learn",
        json={"decision_id": decision_id, "actual_action": "auto_approve"},
    )

    assert response.status_code == 200
    assert len(learning_store.updates) == 1
    update = learning_store.updates[0]
    assert update["old_status"] == "RED"
    assert update["caused_by_decision_id"] == decision_id
    assert update["categories_with_data"] == 1


def test_learn_without_l5_store_remains_silent_noop():
    scorer = FakeScorer()
    client = build_client(scorer=scorer)
    client.post(
        "/score",
        json={"category": "pipeline_failure", "factors": {"business_criticality": 0.8}},
    )

    response = client.post(
        "/learn",
        json={"decision_id": "dec-1", "actual_action": "auto_approve"},
    )

    assert response.status_code == 200
    LearnResponse.model_validate(response.json())


def test_learn_l5_get_failure_is_non_fatal(tmp_path):
    scorer = SQLiteL5Scorer(tmp_path / "get-failure.sqlite")
    learning_store = FailingReadLearningStore()
    client = build_client(domain="test", scorer=scorer, learning_store=learning_store)
    decision_id = client.post(
        "/score",
        json={"category": "pipeline_failure", "factors": {"business_criticality": 0.8}},
    ).json()["decision_id"]

    response = client.post(
        "/learn",
        json={"decision_id": decision_id, "actual_action": "auto_approve"},
    )

    assert response.status_code == 200
    LearnResponse.model_validate(response.json())
    assert learning_store.updates == []


def test_learn_l5_update_failure_is_non_fatal(tmp_path):
    scorer = SQLiteL5Scorer(tmp_path / "update-failure.sqlite")
    learning_store = FailingWriteLearningStore()
    client = build_client(domain="test", scorer=scorer, learning_store=learning_store)
    decision_id = client.post(
        "/score",
        json={"category": "pipeline_failure", "factors": {"business_criticality": 0.8}},
    ).json()["decision_id"]

    response = client.post(
        "/learn",
        json={"decision_id": decision_id, "actual_action": "auto_approve"},
    )

    assert response.status_code == 200
    LearnResponse.model_validate(response.json())


def test_learn_persists_dk_weights_to_l5_after_phase_transition():
    scorer = DKRuntimeScorer(weights=[[0.2, 0.8]])
    learning_store = RecordingDKLearningStore()
    client = build_client(domain="test", scorer=scorer, learning_store=learning_store)
    decision_id = client.post(
        "/score",
        json={"category": "pipeline_failure", "factors": {"signal": 0.9, "noise": 0.1}},
    ).json()["decision_id"]

    response = client.post(
        "/learn",
        json={"decision_id": decision_id, "actual_action": "auto_approve"},
    )

    assert response.status_code == 200
    LearnResponse.model_validate(response.json())
    assert scorer.reestimate_calls == 1
    assert len(learning_store.dk_updates) == 1
    update = learning_store.dk_updates[0]
    assert update["domain"] == "test"
    assert update["weight_tensor"] == [[0.2, 0.8]]
    assert update["n_decisions_used"] == 1
    assert update["n_confirmed"] == 1
    assert update["n_overridden"] == 0
    assert update["entity_group"] is None


def test_learn_dk_includes_welford_state_and_confirmed_overridden_split():
    scorer = DKRuntimeScorer(weights=[[0.2, 0.8]])
    learning_store = RecordingDKLearningStore()
    client = build_client(domain="test", scorer=scorer, learning_store=learning_store)
    first = client.post(
        "/score",
        json={"category": "pipeline_failure", "factors": {"signal": 1.0, "noise": 0.0}},
    ).json()["decision_id"]
    second = client.post(
        "/score",
        json={"category": "pipeline_failure", "factors": {"signal": 0.0, "noise": 1.0}},
    ).json()["decision_id"]

    assert client.post("/learn", json={"decision_id": first, "actual_action": "auto_approve"}).status_code == 200
    assert client.post("/learn", json={"decision_id": second, "actual_action": "investigate"}).status_code == 200

    update = learning_store.dk_updates[-1]
    state = update["welford_state"]
    assert isinstance(state, dict)
    assert set(state) == {
        "confirmed_mean",
        "confirmed_m2",
        "overridden_mean",
        "overridden_m2",
        "all_mean",
        "all_m2",
        "n_all",
    }
    assert state["n_all"] == 2
    assert update["n_decisions_used"] == 2
    assert update["n_confirmed"] == 1
    assert update["n_overridden"] == 1


def test_learn_dk_no_store_still_reestimates_runtime_dk():
    scorer = DKRuntimeScorer(weights=[[0.2, 0.8]])
    client = build_client(domain="test", scorer=scorer)
    decision_id = client.post(
        "/score",
        json={"category": "pipeline_failure", "factors": {"signal": 0.9, "noise": 0.1}},
    ).json()["decision_id"]

    response = client.post(
        "/learn",
        json={"decision_id": decision_id, "actual_action": "auto_approve"},
    )

    assert response.status_code == 200
    assert scorer.reestimate_calls == 1


def test_learn_dk_persist_failure_is_non_fatal():
    scorer = DKRuntimeScorer(weights=[[0.2, 0.8]])
    learning_store = RecordingDKLearningStore(fail=True)
    client = build_client(domain="test", scorer=scorer, learning_store=learning_store)
    decision_id = client.post(
        "/score",
        json={"category": "pipeline_failure", "factors": {"signal": 0.9, "noise": 0.1}},
    ).json()["decision_id"]

    response = client.post(
        "/learn",
        json={"decision_id": decision_id, "actual_action": "auto_approve"},
    )

    assert response.status_code == 200
    LearnResponse.model_validate(response.json())


def test_learn_dk_response_shape_unchanged():
    scorer = DKRuntimeScorer(weights=[[0.2, 0.8]])
    learning_store = RecordingDKLearningStore()
    client = build_client(domain="test", scorer=scorer, learning_store=learning_store)
    decision_id = client.post(
        "/score",
        json={"category": "pipeline_failure", "factors": {"signal": 0.9, "noise": 0.1}},
    ).json()["decision_id"]

    payload = client.post(
        "/learn",
        json={"decision_id": decision_id, "actual_action": "auto_approve"},
    ).json()

    LearnResponse.model_validate(payload)
    assert "welford_state" not in payload
    assert "weight_tensor" not in payload


def test_learn_dk_not_written_before_variance_phase():
    scorer = DKRuntimeScorer(weights=None)
    learning_store = RecordingDKLearningStore()
    client = build_client(domain="test", scorer=scorer, learning_store=learning_store)
    decision_id = client.post(
        "/score",
        json={"category": "pipeline_failure", "factors": {"signal": 0.9, "noise": 0.1}},
    ).json()["decision_id"]

    response = client.post(
        "/learn",
        json={"decision_id": decision_id, "actual_action": "auto_approve"},
    )

    assert response.status_code == 200
    assert scorer.reestimate_calls == 1
    assert learning_store.dk_updates == []


def test_learn_persists_centroid_to_l5_in_mean_convergence():
    scorer = CentroidRuntimeScorer()
    learning_store = RecordingCentroidLearningStore()
    client = build_client(domain="test", scorer=scorer, learning_store=learning_store)
    decision_id = client.post(
        "/score",
        json={"category": "pipeline_failure", "factors": {"signal": 0.9, "noise": 0.1}},
    ).json()["decision_id"]

    response = client.post(
        "/learn",
        json={"decision_id": decision_id, "actual_action": "auto_approve"},
    )

    assert response.status_code == 200
    LearnResponse.model_validate(response.json())
    assert len(learning_store.centroid_updates) == 1
    update = learning_store.centroid_updates[0]
    assert update["domain"] == "test"
    assert update["category"] == "pipeline_failure"
    assert update["action"] == "auto_approve"
    assert update["centroid_vector"] == [0.5, 0.8]
    assert update["caused_by_decision_id"] == decision_id
    assert update["delta_norm"] == pytest.approx(0.5)


def test_centroid_l5_nonfatal():
    scorer = CentroidRuntimeScorer()
    learning_store = RecordingCentroidLearningStore(fail=True)
    client = build_client(domain="test", scorer=scorer, learning_store=learning_store)
    decision_id = client.post(
        "/score",
        json={"category": "pipeline_failure", "factors": {"signal": 0.9, "noise": 0.1}},
    ).json()["decision_id"]

    response = client.post(
        "/learn",
        json={"decision_id": decision_id, "actual_action": "auto_approve"},
    )

    assert response.status_code == 200
    LearnResponse.model_validate(response.json())
    assert scorer.save_centroids_calls == 1


def test_centroid_l5_coexists_with_checkpoint():
    scorer = CentroidRuntimeScorer()
    learning_store = RecordingCentroidLearningStore()
    client = build_client(domain="test", scorer=scorer, learning_store=learning_store)
    decision_id = client.post(
        "/score",
        json={"category": "pipeline_failure", "factors": {"signal": 0.9, "noise": 0.1}},
    ).json()["decision_id"]

    response = client.post(
        "/learn",
        json={"decision_id": decision_id, "actual_action": "auto_approve"},
    )

    assert response.status_code == 200
    assert scorer.save_centroids_calls == 1
    assert len(learning_store.centroid_updates) == 1


def test_centroid_l5_skipped_in_variance_learning():
    scorer = CentroidRuntimeScorer(phase="VARIANCE_LEARNING")
    scorer.weights = [[0.2, 0.8]]
    learning_store = RecordingCentroidLearningStore()
    learning_store.update_dk_weights = lambda **kwargs: setattr(learning_store, "dk_update", kwargs)
    client = build_client(domain="test", scorer=scorer, learning_store=learning_store)
    decision_id = client.post(
        "/score",
        json={"category": "pipeline_failure", "factors": {"signal": 0.9, "noise": 0.1}},
    ).json()["decision_id"]

    response = client.post(
        "/learn",
        json={"decision_id": decision_id, "actual_action": "auto_approve"},
    )

    assert response.status_code == 200
    assert learning_store.centroid_updates == []
    assert hasattr(learning_store, "dk_update")


def test_get_centroid_copy_safe_and_phase_accessor():
    preset = SimpleNamespace(
        shape=SimpleNamespace(
            category_names=["pipeline_failure"],
            action_names=["auto_approve"],
            n_categories=1,
            n_factors=2,
        ),
        name="test",
    )
    gae_scorer = SimpleNamespace(
        centroids=np.asarray([[[0.2, 0.4]]], dtype=np.float64),
        _category_states=[SimpleNamespace(phase="MEAN_CONVERGENCE")],
    )
    scorer = CompoundingScorer(
        preset=preset,
        scorer=gae_scorer,
        graph_store=FakeStore(),
    )

    centroid = scorer.get_centroid("pipeline_failure", "auto_approve")
    assert centroid == [0.2, 0.4]
    assert centroid is not None
    centroid[0] = 9.0
    assert scorer.get_centroid("pipeline_failure", "auto_approve") == [0.2, 0.4]
    assert scorer.get_category_phase("pipeline_failure") == "MEAN_CONVERGENCE"


def test_l5_dk_persistence_serializes_tracker_reestimate_and_write():
    scorer = BlockingDKRuntimeScorer()
    learning_store = RecordingDKLearningStore()
    client = build_client(domain="test", scorer=scorer, learning_store=learning_store)
    responses: dict[str, int] = {}

    def learn(decision_id: str) -> None:
        response = client.post(
            "/learn",
            json={"decision_id": decision_id, "actual_action": "auto_approve"},
        )
        responses[decision_id] = response.status_code

    first = threading.Thread(target=learn, args=("dk-block-1",))
    second = threading.Thread(target=learn, args=("dk-block-2",))

    first.start()
    assert scorer.first_reestimate_entered.wait(5)
    second.start()
    assert not scorer.second_reestimate_entered.wait(0.25)
    assert learning_store.dk_updates == []

    scorer.release_first_reestimate.set()
    first.join(5)
    second.join(5)

    assert responses == {"dk-block-1": 200, "dk-block-2": 200}
    assert scorer.reestimate_calls == 2
    assert len(learning_store.dk_updates) == 2


def test_l5_conservation_persistence_serializes_old_status_read_and_update():
    scorer = ConcurrentScorer()
    learning_store = BlockingLearningStore()
    client = build_client(domain="test", scorer=scorer, learning_store=learning_store)
    responses: dict[str, int] = {}

    def learn(decision_id: str) -> None:
        response = client.post(
            "/learn",
            json={"decision_id": decision_id, "actual_action": "auto_approve"},
        )
        responses[decision_id] = response.status_code

    first = threading.Thread(target=learn, args=("dec-1",))
    second = threading.Thread(target=learn, args=("dec-2",))

    first.start()
    assert learning_store.first_get_entered.wait(5)
    second.start()
    assert not learning_store.second_get_entered.wait(0.25)
    assert learning_store.updates == []

    learning_store.release_first_get.set()
    first.join(5)
    second.join(5)

    assert responses == {"dec-1": 200, "dec-2": 200}
    assert learning_store.get_entries == 2
    assert [update["old_status"] for update in learning_store.updates] == [
        "RED",
        "GREEN",
    ]
    assert [update["caused_by_decision_id"] for update in learning_store.updates] == [
        "dec-1",
        "dec-2",
    ]


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
