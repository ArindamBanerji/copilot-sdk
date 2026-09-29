from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock
from datetime import datetime, timezone
from dataclasses import dataclass

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.investigation_router import create_investigation_router
from copilot_sdk.scoring.investigation import (
    EvidenceProvider,
    InvestigationStep,
    InvestigationTrace,
    KUtilityStore,
    VLDInvestigator,
    investigate,
)
from copilot_sdk.scoring.situation_classifier import (
    SITUATION_BUDGETS,
    SituationClassifier,
    extract_features,
)


class MockEvidenceProvider:
    def __init__(self, evidence_map: dict[int, dict]):
        self.evidence_map = evidence_map
        self.reads: list[int] = []

    def read_evidence(self, decision_id: str, dimension: int, factor_name: str):
        self.reads.append(dimension)
        return self.evidence_map.get(dimension)


class MutatingEvidenceProvider(MockEvidenceProvider):
    def __init__(self, evidence_map: dict[int, dict], array_to_mutate: np.ndarray):
        super().__init__(evidence_map)
        self.array_to_mutate = array_to_mutate

    def read_evidence(self, decision_id: str, dimension: int, factor_name: str):
        self.array_to_mutate[:] = 0.0
        return super().read_evidence(decision_id, dimension, factor_name)


@dataclass
class StoreWithConn:
    conn: object


@dataclass
class FakeReadOnlyResult:
    action_index: int
    probabilities: list[float]


class FakeScorer:
    def __init__(self, centroids: np.ndarray, sigma: np.ndarray, factor_names: list[str]):
        self.centroids = centroids
        self.sigma = sigma
        self.factor_names = factor_names
        self.tau = 0.1
        self.read_only_calls: list[tuple[dict[str, float], str]] = []

    def score_read_only(self, factors: dict[str, float], category: str):
        self.read_only_calls.append((dict(factors), category))
        vector = np.asarray([factors[name] for name in self.factor_names], dtype=np.float64)
        precision = 1.0 / np.maximum(self.sigma**2, 0.001)
        dists = np.sum(precision.reshape(1, -1) * (vector.reshape(1, -1) - self.centroids) ** 2, axis=1)
        logits = -dists / self.tau
        logits = logits - np.max(logits)
        exp = np.exp(logits)
        probs = exp / np.sum(exp)
        return FakeReadOnlyResult(int(np.argmax(probs)), [float(p) for p in probs])


@pytest.fixture
def simple_geometry():
    mu = np.asarray(
        [
            [0.8, 0.8, 0.2, 0.2, 0.5, 0.5],
            [0.5, 0.5, 0.5, 0.5, 0.5, 0.5],
            [0.2, 0.2, 0.8, 0.8, 0.5, 0.5],
            [0.1, 0.1, 0.1, 0.1, 0.9, 0.9],
        ],
        dtype=np.float64,
    )
    sigma = np.asarray([0.1, 0.1, 0.1, 0.1, 0.15, 0.15], dtype=np.float64)
    factor_names = ["severity", "identity", "intel", "timing", "history", "device"]
    return mu, sigma, factor_names


@pytest.fixture
def investigator(simple_geometry):
    mu, sigma, factor_names = simple_geometry
    return VLDInvestigator(mu, sigma, factor_names)


@pytest.fixture
def mock_decision_store(tmp_path):
    conn = sqlite3.connect(tmp_path / "k.sqlite3")
    try:
        yield StoreWithConn(conn)
    finally:
        conn.close()


def test_evidence_provider_protocol_runtime() -> None:
    assert isinstance(MockEvidenceProvider({}), EvidenceProvider)


def test_Q_additive_positive_values(investigator) -> None:
    v = np.asarray([0.55, 0.55, 0.45, 0.45, 0.5, 0.5])
    _, p = investigator.score(v)
    q = investigator.compute_Q(v, p)
    assert q.shape == (6,)
    assert np.all(q >= 0)


def test_Q_excludes_enriched_dims(investigator) -> None:
    _, p = investigator.score(np.asarray([0.55, 0.55, 0.45, 0.45, 0.5, 0.5]))
    q = investigator.compute_Q(np.asarray([0.55, 0.55, 0.45, 0.45, 0.5, 0.5]), p, enriched_set={0, 1})
    assert q[0] == -1.0
    assert q[1] == -1.0
    assert np.all(q[2:] >= 0)


def test_Q_with_K_weights(investigator) -> None:
    v = np.asarray([0.55, 0.55, 0.45, 0.45, 0.5, 0.5])
    _, p = investigator.score(v)
    q = investigator.compute_Q(v, p)
    weights = np.ones(6)
    weights[2] = 3.0
    q_weighted = investigator.compute_Q(v, p, K_weights=weights)
    assert q_weighted[2] > q[2]


def test_Q_additive_not_multiplicative(investigator) -> None:
    v = investigator.mu[0].copy()
    _, p = investigator.score(v)
    q = investigator.compute_Q(v, p)
    assert np.max(q) > 0.001


def test_Q_highest_for_most_discriminative(investigator) -> None:
    v = np.asarray([0.65, 0.65, 0.35, 0.35, 0.5, 0.5])
    p = np.asarray([0.49, 0.48, 0.02, 0.01])
    q = investigator.compute_Q(v, p)
    gaps = np.abs(investigator.mu[0] - investigator.mu[1])
    assert int(np.argmax(q)) in set(np.flatnonzero(gaps == gaps.max()))


def test_Q_recomputed_from_current_v(investigator) -> None:
    p = np.asarray([0.49, 0.48, 0.02, 0.01])
    q1 = investigator.compute_Q(np.asarray([0.65, 0.65, 0.35, 0.35, 0.5, 0.5]), p)
    q2 = investigator.compute_Q(np.asarray([0.35, 0.35, 0.65, 0.65, 0.5, 0.5]), p)
    assert int(np.argmax(q1)) != int(np.argmax(q2)) or not np.allclose(q1, q2)


def test_investigate_returns_trace(investigator) -> None:
    trace = investigator.investigate("d1", "cat", np.asarray([0.5] * 6), MockEvidenceProvider({}), budget=1)
    assert isinstance(trace, InvestigationTrace)
    assert trace.decision_id == "d1"


def test_investigate_reads_highest_Q_first(investigator) -> None:
    v = np.asarray([0.55, 0.55, 0.45, 0.45, 0.5, 0.5])
    _, p = investigator.score(v)
    expected = int(np.argmax(investigator.compute_Q(v, p)))
    provider = MockEvidenceProvider({expected: {"value": 0.9, "confidence": 1.0, "source": "raw"}})
    investigator.investigate("d1", "cat", v, provider, budget=1)
    assert provider.reads[0] == expected


def test_investigate_stops_at_budget(investigator) -> None:
    provider = MockEvidenceProvider({i: {"value": 0.9, "confidence": 1.0, "source": "raw"} for i in range(6)})
    trace = investigator.investigate("d1", "cat", np.asarray([0.5] * 6), provider, budget=2)
    assert len(trace.steps) <= 2


def test_investigate_skips_none_evidence(investigator) -> None:
    provider = MockEvidenceProvider({1: {"value": 0.9, "confidence": 1.0, "source": "raw"}})
    trace = investigator.investigate("d1", "cat", np.asarray([0.5] * 6), provider, budget=2)
    assert len(provider.reads) == 2
    assert trace.steps[0].status == "empty"
    assert trace.steps[0].evidence_value is None
    assert trace.steps[0].evidence_available is True
    assert trace.steps[0].evidence_admitted is False
    assert len([step for step in trace.steps if step.status == "acquired"]) <= 1


def test_investigate_empty_reads_are_recorded(investigator) -> None:
    trace = investigator.investigate("d1", "cat", np.asarray([0.5] * 6), MockEvidenceProvider({}), budget=2)
    assert len(trace.steps) == 2
    assert all(step.status == "empty" for step in trace.steps)
    assert all(step.action_before == step.action_after for step in trace.steps)


def test_module_level_investigate_records_empty_reads(simple_geometry) -> None:
    mu, sigma, names = simple_geometry
    result = investigate(
        factors=np.asarray([0.5] * 6),
        category="cat",
        budget=2,
        evidence_provider=lambda *args: None,
        score_fn=None,
        mu=mu,
        sigma=sigma,
        factor_names=names,
    )
    assert len([step for step in result["steps"] if step["status"] == "empty"]) == 2


def test_investigate_rejects_degraded_provider_payload(investigator) -> None:
    v = np.asarray([0.5] * 6)
    provider = MagicMock()
    provider.read_evidence.return_value = {
        "value": 0.9, "confidence": 1.0, "source": "neutral",
        "data_available": False, "degraded": True,
        "failure_reason": "graph unavailable",
    }
    trace = investigator.investigate("d1", "cat", v, provider, budget=1)
    step = trace.steps[0]
    assert step.v_after == step.v_before == v.tolist()
    assert step.evidence_available is False
    assert step.evidence_admitted is False
    assert step.failure_reason == "graph unavailable"
    assert trace.degraded is True
    assert trace.failed_providers == [step.factor_name]


def test_investigate_available_payload_is_admitted(investigator) -> None:
    v = np.asarray([0.5] * 6)
    provider = MagicMock()
    provider.read_evidence.return_value = {
        "value": 0.9, "confidence": 1.0, "source": "graph",
        "data_available": True, "degraded": False,
    }
    trace = investigator.investigate("d1", "cat", v, provider, budget=1)
    step = trace.steps[0]
    assert step.evidence_available is True
    assert step.evidence_admitted is True
    assert step.v_after != step.v_before
    assert trace.degraded is False
    assert trace.failed_providers == []


def test_investigate_mixed_providers_uses_only_available_evidence(investigator) -> None:
    v = np.asarray([0.5] * 6)
    provider = MagicMock()
    provider.read_evidence.side_effect = [
        {"value": 0.9, "confidence": 1.0, "source": "graph", "data_available": True},
        {"value": 0.1, "confidence": 1.0, "source": "neutral", "data_available": False},
    ]
    trace = investigator.investigate("d1", "cat", v, provider, budget=2, delta=0.0)
    assert trace.steps[0].evidence_admitted is True
    assert trace.steps[1].evidence_admitted is False
    assert trace.steps[1].v_after == trace.steps[1].v_before
    assert trace.final_action == trace.steps[0].action_after
    assert trace.degraded is True
    assert trace.failed_providers == [trace.steps[1].factor_name]


def test_investigate_all_providers_fail_without_vector_change(investigator) -> None:
    v = np.asarray([0.5] * 6)
    provider = MagicMock()
    provider.read_evidence.return_value = {
        "value": 0.5,
        "confidence": 0.0,
        "source": "purchasing_domain_context",
        "data_available": False,
        "degraded": True,
        "failure_reason": "graph unavailable",
    }
    trace = investigator.investigate("d1", "cat", v, provider, budget=2)
    assert trace.degraded is True
    assert trace.evidence_available is False
    assert len(trace.failed_providers) == 2
    assert all(step.v_after == step.v_before for step in trace.steps)
    assert all(step.evidence_admitted is False for step in trace.steps)


def test_investigate_records_flips(investigator) -> None:
    v = np.asarray([0.2, 0.2, 0.75, 0.75, 0.5, 0.5])
    provider = MockEvidenceProvider({0: {"value": 0.95, "confidence": 1.0, "source": "raw"}, 1: {"value": 0.95, "confidence": 1.0, "source": "raw"}})
    trace = investigator.investigate("d1", "cat", v, provider, budget=2)
    if trace.surface_action != trace.final_action:
        assert any(step.flipped for step in trace.steps)


def test_investigate_contrast_strip(investigator) -> None:
    trace = investigator.investigate("d1", "cat", np.asarray([0.5] * 6), MockEvidenceProvider({}), budget=0)
    assert isinstance(trace.surface_action, int)
    assert isinstance(trace.final_margin, float)


def test_investigate_gated_vs_raw_update(simple_geometry) -> None:
    mu, sigma, names = simple_geometry
    raw = VLDInvestigator(mu, sigma, names)
    gated = VLDInvestigator(mu, sigma, names)
    v = np.asarray([0.5] * 6)
    _, p = raw.score(v)
    k = int(np.argmax(raw.compute_Q(v, p)))
    evidence = {k: {"value": 1.0, "confidence": 0.25, "source": "trusted"}}
    raw_trace = raw.investigate("d1", "cat", v, MockEvidenceProvider(evidence), budget=1)
    gated_trace = gated.investigate("d1", "cat", v, MockEvidenceProvider(evidence), budget=1, gated_sources={"trusted"})
    assert raw_trace.steps[0].v_after[k] == 1.0
    assert gated_trace.steps[0].v_after[k] == pytest.approx(0.25 * 1.0 + 0.75 * 0.5)


def test_investigate_recomputes_Q_each_step(investigator) -> None:
    provider = MockEvidenceProvider({i: {"value": 0.9, "confidence": 1.0, "source": "raw"} for i in range(6)})
    trace = investigator.investigate("d1", "cat", np.asarray([0.5] * 6), provider, budget=2)
    assert len(provider.reads) >= 2
    assert provider.reads[1] != provider.reads[0]


def test_investigate_uses_score_fn_for_actions(investigator) -> None:
    calls: list[tuple[list[float], str]] = []

    def score_fn(vector: np.ndarray, category: str):
        calls.append((vector.tolist(), category))
        return {"action_index": 2, "probabilities": [0.05, 0.05, 0.85, 0.05]}

    trace = investigator.investigate("d1", "cat", np.asarray([0.5] * 6), MockEvidenceProvider({}), budget=1, score_fn=score_fn)
    assert calls
    assert all(category == "cat" for _, category in calls)
    assert trace.surface_action == 2
    assert trace.final_action == 2


def test_score_fn_object_result_matches_internal_scoring(simple_geometry) -> None:
    mu, sigma, names = simple_geometry
    inv = VLDInvestigator(mu, sigma, names)
    v = np.asarray([0.55, 0.55, 0.45, 0.45, 0.5, 0.5])
    action, probs = inv.score(v)

    result = FakeReadOnlyResult(action, [float(p) for p in probs])
    via_score_fn = inv.predict(v, "cat", lambda _v, _category: result)
    assert via_score_fn[0] == action
    assert np.allclose(via_score_fn[1], probs)
    assert via_score_fn[2] == pytest.approx(inv.margin(probs))


def test_k_store_initial_weights(mock_decision_store) -> None:
    store = KUtilityStore(mock_decision_store, 6)
    assert np.allclose(store.get_weights("cat"), np.full(6, 0.5))


def _trace_for_dim(dim: int = 2, flipped: bool = False) -> InvestigationTrace:
    step = InvestigationStep(0, dim, "f", 0.9, 1.0, "raw", [0.5] * 6, [0.5] * 6, 0, 1 if flipped else 0, 0.1, 0.2, flipped)
    return InvestigationTrace("d", "cat", 1, [step], 0, 0.1, 1 if flipped else 0, 0.2)


def test_k_store_update_increases_correct(mock_decision_store) -> None:
    store = KUtilityStore(mock_decision_store, 6)
    store.update_weights("cat", _trace_for_dim(2), correct=True)
    assert store.get_weights("cat")[2] > 0.5


def test_k_store_update_decreases_incorrect(mock_decision_store) -> None:
    store = KUtilityStore(mock_decision_store, 6)
    store.update_weights("cat", _trace_for_dim(2), correct=False)
    assert store.get_weights("cat")[2] < 0.5


def test_k_store_per_category_isolation(mock_decision_store) -> None:
    store = KUtilityStore(mock_decision_store, 6)
    store.update_weights("cat_a", _trace_for_dim(2), correct=True)
    assert store.get_weights("cat_b")[2] == 0.5


def test_k_store_weight_bounds(mock_decision_store) -> None:
    store = KUtilityStore(mock_decision_store, 6)
    for _ in range(200):
        store.update_weights("cat", _trace_for_dim(2, flipped=True), correct=True)
    assert store.get_weights("cat")[2] == pytest.approx(3.0)
    for _ in range(1000):
        store.update_weights("bad", _trace_for_dim(2), correct=False)
    assert store.get_weights("bad")[2] == pytest.approx(0.1)


def test_classifier_fallback_without_model(simple_geometry) -> None:
    mu, sigma, _ = simple_geometry
    clf = SituationClassifier()
    inv = VLDInvestigator(mu, sigma, [f"f{i}" for i in range(6)])
    v = np.asarray([0.4] * 6)
    _, p = inv.score(v)
    q = inv.compute_Q(v, p)
    assessment = clf.classify(v, mu, sigma, p, q)
    assert assessment.situation in SITUATION_BUDGETS
    assert assessment.recommended_budget >= 0


def test_classifier_s1_near_centroid(simple_geometry) -> None:
    mu, sigma, _ = simple_geometry
    inv = VLDInvestigator(mu, sigma, [f"f{i}" for i in range(6)])
    v = mu[0].copy()
    _, p = inv.score(v)
    q = inv.compute_Q(v, p)
    assessment = SituationClassifier().classify(v, mu, sigma, p, q)
    assert assessment.situation == "S1"
    assert assessment.recommended_budget == 0


def test_extract_features_shape(simple_geometry) -> None:
    mu, sigma, _ = simple_geometry
    inv = VLDInvestigator(mu, sigma, [f"f{i}" for i in range(6)])
    v = np.asarray([0.4] * 6)
    _, p = inv.score(v)
    q = inv.compute_Q(v, p)
    features = extract_features(v, mu, sigma, p, q)
    assert features.shape == (10,)
    assert np.all(np.isfinite(features))


def test_classifier_s6_far_from_centroids(simple_geometry) -> None:
    mu, sigma, _ = simple_geometry
    inv = VLDInvestigator(mu, sigma, [f"f{i}" for i in range(6)])
    v = np.asarray([2.0] * 6)
    _, p = inv.score(v)
    q = inv.compute_Q(v, p)
    assessment = SituationClassifier().classify(v, mu, sigma, p, q)
    assert assessment.situation == "S6"
    assert assessment.recommended_budget == 4


@pytest.fixture
def client(simple_geometry):
    mu, sigma, names = simple_geometry
    scorer = FakeScorer(mu, sigma, names)

    def scorer_provider():
        return scorer

    def evidence_factory(decision_id: str):
        return MockEvidenceProvider({0: {"value": 0.95, "confidence": 1.0, "source": "raw"}, 1: {"value": 0.95, "confidence": 1.0, "source": "raw"}})

    app = FastAPI()
    app.include_router(create_investigation_router(scorer_provider, evidence_factory, factor_names=names, default_budget=2))
    return TestClient(app)


def test_router_health(client) -> None:
    response = client.get("/api/investigation/health")
    assert response.status_code == 200
    assert response.json()["investigation_available"] is True


def test_router_investigate(client) -> None:
    response = client.post("/api/investigation/investigate", json={"decision_id": "d1", "category": "cat", "factor_vector": [0.5] * 6, "budget": 2})
    assert response.status_code == 200
    body = response.json()
    assert "steps" in body
    assert "contrast" in body


def test_router_contrast_fields(client) -> None:
    body = client.post("/api/investigation/investigate", json={"decision_id": "d1", "category": "cat", "factor_vector": [0.5] * 6, "budget": 1}).json()
    assert {"sp_action", "sp_margin", "vld_action", "vld_margin", "improved"} <= set(body["contrast"])


def test_router_no_evidence(simple_geometry) -> None:
    mu, sigma, names = simple_geometry
    app = FastAPI()
    app.include_router(create_investigation_router(lambda: FakeScorer(mu, sigma, names), lambda decision_id: MockEvidenceProvider({}), factor_names=names))
    response = TestClient(app).post("/api/investigation/investigate", json={"decision_id": "d1", "category": "cat", "factor_vector": [0.5] * 6, "budget": 1})
    assert response.status_code == 200
    steps = response.json()["steps"]
    assert len(steps) == 1
    payload = response.json()
    assert steps[0]["status"] == "empty"
    assert steps[0]["evidence_available"] is True
    assert steps[0]["evidence_admitted"] is False
    assert payload["evidence_available"] is True
    assert payload["degraded"] is False
    assert payload["failed_providers"] == []
    assert all(value is not None for value in payload.values())


def test_router_with_budget(client) -> None:
    body = client.post("/api/investigation/investigate", json={"decision_id": "d1", "category": "cat", "factor_vector": [0.5] * 6, "budget": 1}).json()
    assert len(body["steps"]) <= 1
    assert body["budget_used"] == 1


def test_router_action_changed_flag(client) -> None:
    body = client.post("/api/investigation/investigate", json={"decision_id": "d1", "category": "cat", "factor_vector": [0.2, 0.2, 0.75, 0.75, 0.5, 0.5], "budget": 2}).json()
    assert body["action_changed"] == (body["surface_action"] != body["final_action"])


def test_router_uses_score_read_only(simple_geometry) -> None:
    mu, sigma, names = simple_geometry
    scorer = FakeScorer(mu, sigma, names)
    app = FastAPI()
    app.include_router(create_investigation_router(lambda: scorer, lambda decision_id: MockEvidenceProvider({}), factor_names=names))
    response = TestClient(app).post("/api/investigation/investigate", json={"decision_id": "d1", "category": "cat", "factor_vector": [0.5] * 6, "budget": 1})
    assert response.status_code == 200
    assert scorer.read_only_calls
    assert scorer.read_only_calls[0][0] == {name: 0.5 for name in names}



def test_q_computation_matches_formula() -> None:
    mu = np.asarray([
        [0.1, 0.2, 0.3],
        [0.7, 0.25, 0.4],
        [0.2, 0.8, 0.1],
    ], dtype=float)
    sigma = np.asarray([0.5, 1.0, 0.25], dtype=float)
    inv = VLDInvestigator(mu, sigma, ["a", "b", "c"])
    v = np.asarray([0.4, 0.3, 0.2], dtype=float)
    p = np.asarray([0.52, 0.41, 0.07], dtype=float)
    actual = inv.compute_Q(v, p)
    a1, a2 = 0, 1
    expected = np.asarray([
        (1.0 / max(float(sigma[k] ** 2), 0.001)) / 100.0
        + abs(float(mu[a1, k] - mu[a2, k]))
        + abs(float((v[k] - mu[a1, k]) ** 2 - (v[k] - mu[a2, k]) ** 2))
        for k in range(3)
    ])
    assert np.allclose(actual, expected)
    assert int(np.argmax(actual)) == int(np.argmax(expected))


def test_budget_zero_immediate_return(investigator) -> None:
    provider = MockEvidenceProvider({0: {"value": 0.9, "confidence": 1.0, "source": "raw"}})
    trace = investigator.investigate("d1", "cat", np.asarray([0.5] * 6), provider, budget=0)
    assert trace.steps == []
    assert isinstance(trace.surface_action, int)
    assert isinstance(trace.surface_margin, float)
    assert provider.reads == []


def test_budget_exceeds_ndim(investigator) -> None:
    provider = MockEvidenceProvider({})
    trace = investigator.investigate("d1", "cat", np.asarray([0.5] * 6), provider, budget=10)
    dims = [step.dimension for step in trace.steps]
    assert len(trace.steps) <= 6
    assert len(dims) == len(set(dims))


def test_identical_centroids_graceful() -> None:
    mu = np.asarray([[0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [0.5, 0.5, 0.5]], dtype=float)
    inv = VLDInvestigator(mu, np.ones(3), ["a", "b", "c"])
    v = np.asarray([0.5, 0.5, 0.5], dtype=float)
    action, p = inv.score(v)
    q = inv.compute_Q(v, p)
    trace = inv.investigate("d1", "cat", v, MockEvidenceProvider({}), budget=2)
    assert action in {0, 1, 2}
    assert np.all(np.isfinite(p))
    assert np.all(np.isfinite(q))
    assert np.all(q >= 0)
    assert all(np.isfinite(step.margin_before) and np.isfinite(step.margin_after) for step in trace.steps)


def test_evidence_out_of_range(investigator) -> None:
    v = np.asarray([0.5] * 6)
    _, p = investigator.score(v)
    k = int(np.argmax(investigator.compute_Q(v, p)))
    high = investigator.investigate("d1", "cat", v, MockEvidenceProvider({k: {"value": 1.5, "confidence": 1.0, "source": "raw"}}), budget=1)
    low = investigator.investigate("d1", "cat", v, MockEvidenceProvider({k: {"value": -0.3, "confidence": 1.0, "source": "raw"}}), budget=1)
    assert high.steps[0].evidence_value == 1.0
    assert high.steps[0].v_after[k] == 1.0
    assert low.steps[0].evidence_value == 0.0
    assert low.steps[0].v_after[k] == 0.0


def test_concurrent_investigation_isolation(simple_geometry) -> None:
    mu, sigma, names = simple_geometry
    inv = VLDInvestigator(mu, sigma, names)
    provider_a = MockEvidenceProvider({0: {"value": 0.95, "confidence": 1.0, "source": "raw"}})
    provider_b = MockEvidenceProvider({2: {"value": 0.05, "confidence": 1.0, "source": "raw"}})
    first = inv.investigate("a", "cat", np.asarray([0.5] * 6), provider_a, budget=1)
    second = inv.investigate("b", "cat", np.asarray([0.2, 0.2, 0.8, 0.8, 0.5, 0.5]), provider_b, budget=1)
    assert first.decision_id == "a"
    assert second.decision_id == "b"
    assert provider_a.reads != provider_b.reads or first.steps[0].v_before != second.steps[0].v_before
    assert first.steps[0].v_before == [0.5] * 6


def test_snapshot_captured_at_start(simple_geometry) -> None:
    mu, sigma, names = simple_geometry
    inv = VLDInvestigator(mu, sigma, names)
    trace = inv.investigate("d1", "cat", np.asarray([0.5] * 6), MockEvidenceProvider({}), budget=1)
    assert trace.snapshot is not None
    assert trace.snapshot.geometry_hash
    assert np.allclose(trace.snapshot.centroids, mu)
    assert np.allclose(trace.snapshot.sigma, sigma)


def test_snapshot_immutable(simple_geometry) -> None:
    mu, sigma, names = simple_geometry
    original = mu.copy()
    inv = VLDInvestigator(mu, sigma, names)
    provider = MutatingEvidenceProvider({0: {"value": 0.95, "confidence": 1.0, "source": "raw"}}, mu)
    trace = inv.investigate("d1", "cat", np.asarray([0.5] * 6), provider, budget=1)
    assert trace.snapshot is not None
    assert np.allclose(trace.snapshot.centroids, original)
    assert not np.allclose(mu, original)


def test_snapshot_timestamp(simple_geometry) -> None:
    mu, sigma, names = simple_geometry
    before = datetime.now(timezone.utc)
    trace = VLDInvestigator(mu, sigma, names).investigate("d1", "cat", np.asarray([0.5] * 6), MockEvidenceProvider({}), budget=0)
    after = datetime.now(timezone.utc)
    assert trace.snapshot is not None
    parsed = datetime.fromisoformat(trace.snapshot.timestamp)
    assert before <= parsed <= after


def test_contrast_matches_budget_zero(investigator) -> None:
    trace = investigator.investigate("d1", "cat", np.asarray([0.5] * 6), MockEvidenceProvider({}), budget=0)
    assert trace.contrast is not None
    assert trace.contrast["action"] == trace.surface_action
    assert trace.contrast["margin"] == pytest.approx(trace.surface_margin)


def test_contrast_uses_original_v0(investigator) -> None:
    v = np.asarray([0.2, 0.2, 0.8, 0.8, 0.5, 0.5])
    provider = MockEvidenceProvider({0: {"value": 0.95, "confidence": 1.0, "source": "raw"}, 1: {"value": 0.95, "confidence": 1.0, "source": "raw"}})
    trace = investigator.investigate("d1", "cat", v, provider, budget=2)
    assert trace.contrast is not None
    assert trace.contrast["action"] == trace.surface_action
    if trace.steps:
        assert trace.contrast["action"] != trace.steps[-1].action_after or trace.contrast["margin"] == pytest.approx(trace.surface_margin)


def test_contrast_uses_same_geometry(simple_geometry) -> None:
    mu, sigma, names = simple_geometry
    trace = VLDInvestigator(mu, sigma, names).investigate("d1", "cat", np.asarray([0.5] * 6), MockEvidenceProvider({}), budget=1)
    assert trace.snapshot is not None
    assert trace.contrast is not None
    assert trace.contrast["geometry_hash"] == trace.snapshot.geometry_hash


def test_halt_residual(investigator) -> None:
    v = np.asarray([0.5] * 6)
    provider = MockEvidenceProvider({i: {"value": 0.501, "confidence": 1.0, "source": "raw"} for i in range(6)})
    trace = investigator.investigate("d1", "cat", v, provider, budget=4, delta=0.01)
    assert trace.halt_reason == "residual_below_threshold"
    assert trace.steps[-1].halt_reason == "residual_below_threshold"
    assert 1 < len(trace.steps) < 4


def test_halt_oscillation() -> None:
    mu = np.asarray([[0.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.5, 0.5, 0.0]], dtype=float)
    sigma = np.ones(3)
    inv = VLDInvestigator(mu, sigma, ["first", "second", "third"])

    def score_fn(vector: np.ndarray, category: str):
        if vector[1] > 0.5:
            return {"action_index": 0, "probabilities": [0.8, 0.1, 0.1]}
        if vector[0] > 0.5:
            return {"action_index": 1, "probabilities": [0.1, 0.8, 0.1]}
        return {"action_index": 0, "probabilities": [0.8, 0.1, 0.1]}

    provider = MockEvidenceProvider({0: {"value": 1.0, "confidence": 1.0, "source": "raw"}, 1: {"value": 1.0, "confidence": 1.0, "source": "raw"}})
    trace = inv.investigate(
        "d1",
        "cat",
        np.asarray([0.0, 0.0, 0.0]),
        provider,
        budget=3,
        score_fn=score_fn,
        K_weights=np.asarray([2.0, 1.0, 0.1]),
        max_flips=2,
    )
    assert trace.halt_reason == "oscillation_detected"
    assert trace.steps[-1].halt_reason == "oscillation_detected"
    assert [step.action_after for step in trace.steps[:2]] == [1, 0]


def test_halt_budget_still_works(investigator) -> None:
    provider = MockEvidenceProvider({i: {"value": 0.9, "confidence": 1.0, "source": "raw"} for i in range(6)})
    trace = investigator.investigate("d1", "cat", np.asarray([0.5] * 6), provider, budget=1)
    assert len(trace.steps) == 1
    assert trace.halt_reason == "budget_exhausted"
    assert trace.steps[-1].halt_reason == "budget_exhausted"


def test_halt_reason_in_trace(investigator) -> None:
    trace = investigator.investigate("d1", "cat", np.asarray([0.5] * 6), MockEvidenceProvider({}), budget=1)
    assert hasattr(trace.steps[-1], "halt_reason")
    assert trace.steps[-1].halt_reason == trace.halt_reason


def test_default_delta_and_max_flips(investigator) -> None:
    v = np.asarray([0.5] * 6)
    provider = MockEvidenceProvider({i: {"value": 0.501, "confidence": 1.0, "source": "raw"} for i in range(6)})
    trace = investigator.investigate("d1", "cat", v, provider, budget=4)
    assert trace.halt_reason == "residual_below_threshold"


def test_production_k_utility_rejects_sqlite(mock_decision_store) -> None:
    with pytest.raises(RuntimeError, match="graph-backed connection"):
        KUtilityStore(mock_decision_store, 6, profile="production")

