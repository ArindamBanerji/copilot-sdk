from __future__ import annotations

from typing import Any

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.intelligence_router import create_intelligence_router
from app.services.source_trust import FACTOR_TO_SOURCE, PIPELINE_SYSTEMS, compute_source_trust
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer


def _scorer(n_decisions: int = 8) -> tuple[CompoundingScorer, InMemoryGraphStore]:
    store = InMemoryGraphStore(domain="dataops")
    scorer = CompoundingScorer.from_preset("dataops", graph_store=store, profile="test")
    for index in range(n_decisions):
        factors = {name: 0.2 + index * 0.01 for name in FACTOR_TO_SOURCE}
        result = scorer.score(factors, "pipeline_failure", metadata={"system": "sap_mm_api"})
        scorer.learn(result.decision_id, result.action, persist_artifacts=False)
    return scorer, store


def _weights(scorer: CompoundingScorer, monkeypatch: pytest.MonkeyPatch) -> None:
    # Controlled estimator output isolates this presentation layer's aggregation.
    weights = np.tile([1.0, 0.7, 0.4, 0.2, 0.1, 0.6], (6, 1))
    monkeypatch.setattr(scorer._scorer, "_dk_weights", weights)


def test_source_trust_returns_all_systems(monkeypatch: pytest.MonkeyPatch) -> None:
    scorer, store = _scorer()
    _weights(scorer, monkeypatch)
    rows = compute_source_trust(scorer, store, "dataops")
    assert {row.source for row in rows} == set(PIPELINE_SYSTEMS) | set(FACTOR_TO_SOURCE.values())
    assert [row.trust for row in rows] == sorted((row.trust for row in rows), reverse=True)
    by_source = {row.source: row for row in rows}
    assert by_source["sap_mm_api"].verified == 8
    assert by_source["erp_connector"].verified == 0
    assert all(by_source[source].trust == 0.5 for source in PIPELINE_SYSTEMS)
    assert all(row.total_verified == 8 for row in rows)


def test_trust_range_0_to_1(monkeypatch: pytest.MonkeyPatch) -> None:
    scorer, store = _scorer()
    _weights(scorer, monkeypatch)
    rows = compute_source_trust(scorer, store, "dataops")
    assert all(0 <= row.trust <= 1 for row in rows)
    assert max(row.trust for row in rows) == 1.0
    assert min(row.trust for row in rows) == 0.1


def test_status_green_above_07(monkeypatch: pytest.MonkeyPatch) -> None:
    scorer, store = _scorer()
    _weights(scorer, monkeypatch)
    row = next(row for row in compute_source_trust(scorer, store, "dataops") if row.source == "source_direct")
    assert row.trust == 0.7
    assert row.status == "GREEN"


def test_status_amber_above_04(monkeypatch: pytest.MonkeyPatch) -> None:
    scorer, store = _scorer()
    _weights(scorer, monkeypatch)
    row = next(row for row in compute_source_trust(scorer, store, "dataops") if row.source == "monitoring")
    assert row.trust == 0.4
    assert row.status == "AMBER"


def test_status_red_below_04(monkeypatch: pytest.MonkeyPatch) -> None:
    scorer, store = _scorer()
    _weights(scorer, monkeypatch)
    row = next(row for row in compute_source_trust(scorer, store, "dataops") if row.source == "ingestion_pipeline")
    assert row.trust == 0.1
    assert row.status == "RED"


def test_trend_from_fingerprint_history(monkeypatch: pytest.MonkeyPatch) -> None:
    scorer, store = _scorer()
    _weights(scorer, monkeypatch)
    fingerprint = scorer.fingerprint(persist=False)
    baseline = [{"name": factor.name, "weight": 0.3} for factor in fingerprint.factors]
    store.write_fingerprint("previous", "dataops", list(FACTOR_TO_SOURCE),
                            {"factors": baseline, "decisions_analyzed": 5}, 0, 5)
    rows = compute_source_trust(scorer, store, "dataops")
    assert all(row.trend == "improving" for row in rows if row.dk_contribution)
    assert all(row.trend == "stable" for row in rows if row.source in PIPELINE_SYSTEMS)


def test_dk_contribution_per_source(monkeypatch: pytest.MonkeyPatch) -> None:
    scorer, store = _scorer()
    _weights(scorer, monkeypatch)
    rows = {row.source: row for row in compute_source_trust(scorer, store, "dataops")}
    for factor, source in FACTOR_TO_SOURCE.items():
        assert rows[source].dk_contribution == {factor: rows[source].trust}
        assert rows[source].verified == 8
    assert all(rows[source].dk_contribution == {} for source in PIPELINE_SYSTEMS)


def test_empty_decisions_returns_neutral(monkeypatch: pytest.MonkeyPatch) -> None:
    scorer, store = _scorer(0)
    _weights(scorer, monkeypatch)
    rows = compute_source_trust(scorer, store, "dataops")
    assert len(rows) == 15
    assert all(row.trust == 0.5 and row.status == "AMBER" and row.verified == 0 for row in rows)
    assert all(row.dk_contribution == {} for row in rows)


@pytest.mark.parametrize("weights", [None, [], [[1.0]], [[float("nan")] * 6], [[-1.0] * 6], [[0.0] * 6]])
def test_missing_or_invalid_weights_are_neutral(weights: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    scorer, store = _scorer()
    monkeypatch.setattr(scorer, "get_dk_weights", lambda: weights)
    rows = compute_source_trust(scorer, store, "dataops")
    assert all(row.trust == 0.5 and row.status == "AMBER" for row in rows)


def test_averages_categories_before_normalizing(monkeypatch: pytest.MonkeyPatch) -> None:
    scorer, store = _scorer()
    weights = np.tile([1.0, 0.8, 0.4, 0.2, 0.1, 0.6], (6, 1))
    weights[0, 1] = 0.2
    monkeypatch.setattr(scorer._scorer, "_dk_weights", weights)
    row = next(row for row in compute_source_trust(scorer, store, "dataops") if row.source == "source_direct")
    assert row.trust == 0.7


def test_endpoint_is_read_only_and_has_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
    scorer, store = _scorer()
    _weights(scorer, monkeypatch)
    before = store.get_verified_decisions("dataops")
    history = store.list_fingerprints("dataops")
    weights = scorer.get_dk_weights()
    app = FastAPI()
    app.include_router(create_intelligence_router(lambda: scorer, lambda: store))
    response = TestClient(app).get("/api/dataops/intelligence/source-trust")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 15
    assert all(row["provenance"] == "DK weights from verified decisions" for row in rows)
    assert all(row["total_verified"] == 8 for row in rows)
    assert store.get_verified_decisions("dataops") == before
    assert store.list_fingerprints("dataops") == history
    assert scorer.get_dk_weights() == weights


def test_unverified_decisions_do_not_inflate_counts(monkeypatch: pytest.MonkeyPatch) -> None:
    scorer, store = _scorer()
    _weights(scorer, monkeypatch)
    scorer.score({name: 0.5 for name in FACTOR_TO_SOURCE}, "pipeline_failure",
                 metadata={"system": "sap_mm_api"})
    rows = compute_source_trust(scorer, store, "dataops")
    assert all(row.total_verified == 8 for row in rows)
    assert next(row.verified for row in rows if row.source == "sap_mm_api") == 8


@pytest.mark.parametrize("record_names", [False, True])
def test_vector_only_graph_decisions_keep_source_evidence(
    monkeypatch: pytest.MonkeyPatch, record_names: bool,
) -> None:
    scorer, store = _scorer()
    _weights(scorer, monkeypatch)
    projected = store.get_verified_decisions("dataops")
    for decision in projected:
        decision.pop("factors", None)
        decision["metadata"].pop("factor_names", None)
        if record_names:
            decision["factor_names"] = list(FACTOR_TO_SOURCE)
    monkeypatch.setattr(store, "get_verified_decisions", lambda domain: projected)

    rows = {row.source: row for row in compute_source_trust(scorer, store, "dataops")}

    assert rows["source_direct"].verified == 8
    assert rows["source_direct"].trust == 0.7
    assert rows["source_direct"].dk_contribution == {"source_reliability": 0.7}
    assert all(rows[source].verified == 8 for source in FACTOR_TO_SOURCE.values())
    assert all(rows[source].trust == 0.5 for source in PIPELINE_SYSTEMS)
