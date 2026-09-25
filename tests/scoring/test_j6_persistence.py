from __future__ import annotations

import ast
import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest.mock import Mock

from gae.profile_scorer import ProfileScorer
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from copilot_sdk.backend.scoring_router import (
    _persist_conservation_state_l5,
    create_scoring_router,
)
from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.scoring.startup_restore import restore_l5_runtime_state


@pytest.fixture(autouse=True)
def isolate_persistence_outbox(tmp_path: Path) -> Iterator[None]:
    """Give each persistence test an isolated real outbox database."""
    previous = os.environ.get("CI_PERSISTENCE_OUTBOX_PATH")
    os.environ["CI_PERSISTENCE_OUTBOX_PATH"] = str(tmp_path / "persistence-outbox.db")
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("CI_PERSISTENCE_OUTBOX_PATH", None)
        else:
            os.environ["CI_PERSISTENCE_OUTBOX_PATH"] = previous


def _scorer(mock_preset, store: InMemoryGraphStore) -> CompoundingScorer:
    engine = ProfileScorer(
        mu=mock_preset.bootstrap_centroids.copy(),
        actions=list(mock_preset.shape.action_names),
        categories=list(mock_preset.shape.category_names),
    )
    return CompoundingScorer(mock_preset, engine, graph_store=store, profile="test")










def _failing_v2_store(domain):
    store = InMemoryGraphStore(domain=domain)
    for method, message in {
        "write_conservation_status": "conservation persistence failed",
        "write_fingerprint": "fingerprint persistence failed",
        "write_centroid_checkpoint": "checkpoint persistence failed",
        "append_evidence_receipt": "evidence persistence failed",
        "save_centroids": "legacy checkpoint persistence failed",
    }.items():
        setattr(store, method, Mock(side_effect=RuntimeError(message)))
    return store


def _single_failure_store(domain, failure):
    store = InMemoryGraphStore(domain=domain)
    methods = {"conservation": "write_conservation_status", "fingerprint": "write_fingerprint",
               "evidence": "append_evidence_receipt", "checkpoint": "write_centroid_checkpoint"}
    method = methods[failure]
    setattr(store, method, Mock(side_effect=RuntimeError(f"{failure} failed")))
    return store


def _verified_scorer(mock_preset, store: InMemoryGraphStore):
    scorer = _scorer(mock_preset, store)
    result = scorer.score(
        {"amount": 0.25, "risk": 0.35, "history": 0.45},
        mock_preset.shape.category_names[0],
    )
    alternate = next(action for action in mock_preset.shape.action_names if action != result.action)
    store.write_outcome(
        result.decision_id,
        alternate,
        False,
        metadata={"source": "j6-test"},
        domain=store.domain,
    )
    return scorer, result, alternate


def _seed_capture_decisions(
    store: InMemoryGraphStore,
    preset: Any,
    count: int,
    *,
    correct: bool = True,
    empty_vectors: bool = False,
) -> None:
    factor_names = list(preset.shape.factor_names)
    for index in range(count):
        vector = [] if empty_vectors else [0.1 + index * 0.01] * len(factor_names)
        decision_id = store.write_decision(
            "mock",
            category=preset.shape.category_names[0],
            action=preset.shape.action_names[0],
            confidence=0.8,
            factors={name: value for name, value in zip(factor_names, vector)},
            metadata={
                "decision_id": f"capture-{index}",
                "category_index": 0,
                "recommended_index": 0,
                "factor_vector": vector,
                "probabilities": [0.8, 0.2],
            },
        )
        store.write_outcome(
            decision_id,
            preset.shape.action_names[0] if correct else preset.shape.action_names[1],
            correct,
            metadata={"actual_index": 0 if correct else 1},
            domain=store.domain,
        )


def test_capture_existing_state_writes_three_artifacts(mock_preset):
    store = InMemoryGraphStore(domain="mock")
    _seed_capture_decisions(store, mock_preset, 5)
    scorer = _scorer(mock_preset, store)

    try:
        result = scorer.capture_existing_state(capture_reason="startup_restore")

        assert result["conservation"] == 1
        assert result["fingerprint"] == 1
        assert result["checkpoint"] == 1
        assert not result["errors"]
        assert len(store._conservation_snapshots) == 1
        assert len(store._fingerprints) == 1
        assert len(store._protocol_centroid_checkpoints) == 1
        assert len(store._evidence_receipts) == 0
    finally:
        store.close()


def test_capture_existing_state_idempotent(mock_preset):
    store = InMemoryGraphStore(domain="mock")
    _seed_capture_decisions(store, mock_preset, 5)
    scorer = _scorer(mock_preset, store)

    try:
        scorer.capture_existing_state(capture_reason="startup_restore")
        scorer.capture_existing_state(capture_reason="startup_restore")

        assert len(store._conservation_snapshots) == 1
        assert len(store._fingerprints) == 1
        assert len(store._protocol_centroid_checkpoints) == 1
    finally:
        store.close()


def test_capture_existing_state_no_receipt(mock_preset):
    store = InMemoryGraphStore(domain="mock")
    _seed_capture_decisions(store, mock_preset, 5)
    scorer = _scorer(mock_preset, store)

    try:
        scorer.capture_existing_state(capture_reason="manual_state_capture")
        assert not store._evidence_receipts
    finally:
        store.close()


def test_capture_existing_state_insufficient_factors(mock_preset):
    store = InMemoryGraphStore(domain="mock")
    _seed_capture_decisions(store, mock_preset, 3, empty_vectors=True)
    scorer = _scorer(mock_preset, store)

    try:
        result = scorer.capture_existing_state(capture_reason="startup_restore")

        assert result["conservation"] == 1
        assert result["fingerprint"] == 0
        assert result["checkpoint"] == 1
        assert not store._fingerprints
        assert len(store._conservation_snapshots) == 1
        assert len(store._protocol_centroid_checkpoints) == 1
    finally:
        store.close()


def test_pause_path_writes_fingerprint(mock_preset):
    store = InMemoryGraphStore(domain="mock")
    _seed_capture_decisions(store, mock_preset, 10, correct=False)
    scorer = _scorer(mock_preset, store)
    score_result = scorer.score(
        {"amount": 0.2, "risk": 0.3, "history": 0.4},
        mock_preset.shape.category_names[0],
    )

    try:
        learned = scorer.learn(score_result.decision_id, score_result.action)

        assert learned["status"] == "paused"
        assert store._conservation_snapshots
        assert store._protocol_centroid_checkpoints
        assert store._fingerprints
        assert not store._evidence_receipts
    finally:
        store.close()


def test_startup_restore_calls_capture(mock_preset):
    store = InMemoryGraphStore(domain="mock")
    _seed_capture_decisions(store, mock_preset, 5)
    scorer = _scorer(mock_preset, store)

    try:
        status = restore_l5_runtime_state(
            domain="mock",
            scorer=scorer,
            learning_store=store,
        )

        assert status["state_capture"]["conservation"] == 1
        assert status["state_capture"]["fingerprint"] == 1
        assert status["state_capture"]["checkpoint"] == 1
        assert store._conservation_snapshots
        assert store._fingerprints
        assert store._protocol_centroid_checkpoints
        assert not store._evidence_receipts

        failing_store = _failing_v2_store(domain="mock")
        failing_scorer = _scorer(mock_preset, failing_store)
        failure_status = restore_l5_runtime_state(
            domain="mock",
            scorer=failing_scorer,
            learning_store=failing_store,
        )
        assert "state_capture" in failure_status
    finally:
        store.close()


def test_scorer_persists_v2_evidence_fingerprint_and_checkpoint(mock_preset):
    store = InMemoryGraphStore(domain="mock")
    scorer = _scorer(mock_preset, store)

    try:
        result = scorer.score(
            {"amount": 0.25, "risk": 0.35, "history": 0.45},
            mock_preset.shape.category_names[0],
        )
        scorer.learn(result.decision_id, result.action)

        assert len(store._evidence_receipts) == 1
        receipt = next(iter(store._evidence_receipts.values()))
        assert receipt["domain"] == "mock"
        assert receipt["decision_id"] == result.decision_id

        assert len(store._protocol_centroid_checkpoints) == 1
        checkpoint = next(iter(store._protocol_centroid_checkpoints.values()))
        assert checkpoint["domain"] == "mock"
        assert checkpoint["metadata"]["decision_id"] == result.decision_id

        fingerprint = scorer.fingerprint()
        assert fingerprint.decisions_analyzed == 1
        assert len(store._fingerprints) == 1
        assert all(snapshot["domain"] == "mock" for snapshot in store._fingerprints.values())
        assert any(snapshot["window"] == 1 for snapshot in store._fingerprints.values())
        scorer.fingerprint()
        assert len(store._fingerprints) == 1
    finally:
        store.close()


def test_conservation_persistence_failure_is_not_reported_as_success(mock_preset):
    store = _failing_v2_store(domain="mock")
    scorer = _scorer(mock_preset, store)

    try:
        result = scorer.score(
            {"amount": 0.25, "risk": 0.35, "history": 0.45},
            mock_preset.shape.category_names[0],
        )
        with pytest.raises(RuntimeError, match="conservation persistence failed"):
            scorer.learn(result.decision_id, result.action)
        assert store.count_verified("mock") == 1
    finally:
        store.close()


def test_learn_route_persists_conservation_snapshot(mock_preset):
    store = InMemoryGraphStore(domain="mock")
    scorer = _scorer(mock_preset, store)
    app = FastAPI()
    app.include_router(
        create_scoring_router(
            domain="mock",
            scorer_factory=lambda: scorer,
        )
    )

    try:
        with TestClient(app) as client:
            score_payload = client.post(
                "/score",
                json={
                    "category": mock_preset.shape.category_names[0],
                    "factors": {"amount": 0.25, "risk": 0.35, "history": 0.45},
                },
            ).json()
            decision_id = score_payload["decision_id"]
            response = client.post(
                "/learn",
                json={"decision_id": decision_id, "actual_action": score_payload["action"]},
            )

        assert response.status_code == 200
        assert len(store._conservation_snapshots) == 1
        snapshot = next(iter(store._conservation_snapshots.values()))
        assert snapshot["domain"] == "mock"
        assert snapshot["verified_count"] == 1
    finally:
        store.close()


def test_persist_learning_artifacts_writes_all_four(mock_preset):
    store = InMemoryGraphStore(domain="mock")
    scorer, result, alternate = _verified_scorer(mock_preset, store)

    try:
        scorer._persist_learning_artifacts(
            result.decision_id,
            actual_action=alternate,
            is_correct=False,
            outcome="overridden",
            metadata={"source": "j6-test"},
        )

        assert len(store._conservation_snapshots) == 1
        assert len(store._fingerprints) == 1
        assert len(store._evidence_receipts) == 1
        assert len(store._protocol_centroid_checkpoints) == 1
        assert next(iter(store._conservation_snapshots.values()))["domain"] == "mock"
        assert next(iter(store._fingerprints.values()))["domain"] == "mock"
        receipt = next(iter(store._evidence_receipts.values()))
        assert receipt["domain"] == "mock"
        assert receipt["canonical_payload"]["receipt_type"] == "post_outcome_verification"
        assert next(iter(store._protocol_centroid_checkpoints.values()))["domain"] == "mock"
    finally:
        store.close()


def test_persist_learning_artifacts_propagates_regime_tag(mock_preset):
    store = InMemoryGraphStore(domain="trading")
    scorer = _scorer(mock_preset, store)
    result = scorer.score(
        {"amount": 0.25, "risk": 0.35, "history": 0.45},
        mock_preset.shape.category_names[0],
        metadata={
            "regime_tag": "trending",
            "regime_metadata": {"regime": "trending"},
        },
    )

    try:
        scorer._persist_learning_artifacts(
            result.decision_id,
            actual_action=result.action,
            is_correct=True,
            outcome="confirmed",
        )

        checkpoint = next(iter(store._protocol_centroid_checkpoints.values()))
        assert checkpoint["metadata"]["regime_tag"] == "trending"
    finally:
        store.close()


def test_persist_learning_artifacts_without_regime_tag_remains_null(mock_preset):
    store = InMemoryGraphStore(domain="purchasing")
    scorer = _scorer(mock_preset, store)
    result = scorer.score(
        {"amount": 0.25, "risk": 0.35, "history": 0.45},
        mock_preset.shape.category_names[0],
    )

    try:
        scorer._persist_learning_artifacts(
            result.decision_id,
            actual_action=result.action,
            is_correct=True,
            outcome="confirmed",
        )

        checkpoint = next(iter(store._protocol_centroid_checkpoints.values()))
        assert checkpoint["metadata"]["regime_tag"] is None
    finally:
        store.close()


def test_persist_learning_artifacts_skips_cold_start(mock_preset, caplog):
    store = InMemoryGraphStore(domain="mock")
    scorer = _scorer(mock_preset, store)
    result = scorer.score(
        {"amount": 0.25, "risk": 0.35, "history": 0.45},
        mock_preset.shape.category_names[0],
    )

    try:
        scorer._persist_learning_artifacts(
            result.decision_id,
            actual_action=result.action,
            is_correct=True,
            outcome="confirmed",
            metadata={"source": "j6-cold-start"},
        )

        assert len(store._conservation_snapshots) == 0
        assert len(store._fingerprints) == 1
        assert len(store._evidence_receipts) == 1
        assert len(store._protocol_centroid_checkpoints) == 1
        assert "skipping conservation snapshot" in caplog.text
    finally:
        store.close()


@pytest.mark.parametrize("failure", ["conservation", "fingerprint", "evidence", "checkpoint"])
def test_persist_learning_artifacts_individual_failures(mock_preset, failure):
    store = _single_failure_store(domain="mock", failure=failure)
    scorer, result, alternate = _verified_scorer(mock_preset, store)

    try:
        if failure == "conservation":
            with pytest.raises(RuntimeError, match="conservation failed"):
                scorer._persist_learning_artifacts(
                    result.decision_id,
                    actual_action=alternate,
                    is_correct=False,
                    outcome="overridden",
                    metadata={"source": "j6-failure"},
                )
        else:
            scorer._persist_learning_artifacts(
                result.decision_id,
                actual_action=alternate,
                is_correct=False,
                outcome="overridden",
                metadata={"source": "j6-failure"},
            )

        method = {"conservation": "write_conservation_status", "fingerprint": "write_fingerprint",
                  "evidence": "append_evidence_receipt", "checkpoint": "write_centroid_checkpoint"}[failure]
        assert getattr(store, method).called
        if failure not in {"conservation", "fingerprint"}:
            assert store._conservation_snapshots
        if failure not in {"conservation", "fingerprint"}:
            assert store._fingerprints
        if failure not in {"conservation", "evidence"}:
            assert store._evidence_receipts
        if failure not in {"conservation", "checkpoint"}:
            assert store._protocol_centroid_checkpoints
    finally:
        store.close()


def test_s2p_receipt_type_distinction(mock_preset):
    s2p_source = (
        Path(__file__).resolve().parents[3]
        / "s2p-copilot"
        / "backend"
        / "app"
        / "routers"
        / "s2p.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(s2p_source)
    payload_types: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Return) or not isinstance(node.value, ast.Dict):
            continue
        for key, value in zip(node.value.keys, node.value.values):
            if isinstance(key, ast.Constant) and key.value == "receipt_type":
                literal = ast.literal_eval(value)
                if isinstance(literal, str):
                    payload_types.append(literal)

    assert "pre_outcome_context" in payload_types
    store = InMemoryGraphStore(domain="mock")
    scorer = _scorer(mock_preset, store)
    result = scorer.score(
        {"amount": 0.25, "risk": 0.35, "history": 0.45},
        mock_preset.shape.category_names[0],
    )
    try:
        scorer.learn(result.decision_id, result.action)
        receipt = next(iter(store._evidence_receipts.values()))
        assert receipt["canonical_payload"]["receipt_type"] == "post_outcome_verification"
    finally:
        store.close()
    assert "pre_outcome_context" != "post_outcome_verification"


def test_l5_v2_conservation_coexistence(mock_preset):
    store = InMemoryGraphStore(domain="mock")
    store.update_conservation_state = Mock(wraps=store.update_conservation_state)
    scorer = _scorer(mock_preset, store)
    app = FastAPI()
    app.include_router(
        create_scoring_router(
            domain="mock",
            scorer_factory=lambda: scorer,
        )
    )

    try:
        with TestClient(app) as client:
            score_payload = client.post(
                "/score",
                json={
                    "category": mock_preset.shape.category_names[0],
                    "factors": {"amount": 0.25, "risk": 0.35, "history": 0.45},
                },
            ).json()
            response = client.post(
                "/learn",
                json={"decision_id": score_payload["decision_id"], "actual_action": score_payload["action"]},
            )

        assert response.status_code == 200
        assert store._conservation_snapshots
        assert store.get_conservation_state("mock") is not None
        assert store.update_conservation_state.call_count > 0
    finally:
        store.close()


def _age_query(store, query: str) -> list[dict[str, Any]]:
    return list(store._store._run_query(query))


@pytest.mark.age
def test_conservation_creates_summarizes_domain_edge(age_graph_store):
    store = age_graph_store("trading")
    store.write_conservation_status(
        status_id="trading:conservation:edge-test",
        domain="trading",
        V=1,
        q=1.0,
        alpha=1.0,
        theta_min=0.5,
        verified_count=1,
        correct_count=1,
        status="GREEN",
        policy_version="test",
    )

    rows = _age_query(
        store,
        """
        MATCH (c:ConservationStatus {status_id: 'trading:conservation:edge-test'})
              -[:SUMMARIZES_DOMAIN]->(d:Domain)
        WHERE c.domain = 'trading' AND d.domain_id = 'trading'
        RETURN count(d) AS edge_count
        """,
    )
    assert rows and int(rows[0]["edge_count"]) == 1


@pytest.mark.age
def test_fingerprint_creates_summarizes_domain_edge(age_graph_store):
    store = age_graph_store("trading")
    store.write_fingerprint(
        fingerprint_id="trading:fingerprint:edge-test",
        domain="trading",
        factor_names=["amount"],
        factor_stats={"factors": []},
        skipped_incompatible=0,
        window=1,
    )

    rows = _age_query(
        store,
        """
        MATCH (f:Fingerprint {fingerprint_id: 'trading:fingerprint:edge-test'})
              -[:SUMMARIZES_DOMAIN]->(d:Domain)
        WHERE f.domain = 'trading' AND d.domain_id = 'trading'
        RETURN count(d) AS edge_count
        """,
    )
    assert rows and int(rows[0]["edge_count"]) == 1


@pytest.mark.age
def test_checkpoint_creates_snapshot_and_derived_edges(age_graph_store):
    store = age_graph_store("trading")
    decision_id = store.write_decision(
        domain="trading",
        category="edge-test",
        action="hold",
        confidence=0.8,
        factors={"amount": 0.5},
    )
    store.write_centroid_checkpoint(
        checkpoint_id="trading:checkpoint:edge-test",
        domain="trading",
        category="edge-test",
        action="hold",
        centroids=[[[0.5]]],
        decisions_count=1,
        verified_count=0,
        iks=1.0,
        shape=[1, 1, 1],
        factor_names_hash="edge-test",
        metadata={"decision_id": decision_id},
    )

    snapshot_rows = _age_query(
        store,
        f"""
        MATCH (d:Decision {{decision_id: '{decision_id}'}})
              -[:SNAPSHOT_AFTER]->(c:CentroidCheckpoint
              {{checkpoint_id: 'trading:checkpoint:edge-test'}})
        WHERE d.domain = 'trading' AND c.domain = 'trading'
        RETURN count(c) AS edge_count
        """,
    )
    derived_rows = _age_query(
        store,
        f"""
        MATCH (c:CentroidCheckpoint {{checkpoint_id: 'trading:checkpoint:edge-test'}})
              -[:DERIVED_FROM]->(d:Decision {{decision_id: '{decision_id}'}})
        WHERE c.domain = 'trading' AND d.domain = 'trading'
        RETURN count(d) AS edge_count
        """,
    )
    assert snapshot_rows and int(snapshot_rows[0]["edge_count"]) == 1
    assert derived_rows and int(derived_rows[0]["edge_count"]) == 1


def test_conservation_status_id_deterministic(mock_preset):
    store = InMemoryGraphStore(domain="mock")
    scorer, result, alternate = _verified_scorer(mock_preset, store)
    kwargs = {
        "actual_action": alternate,
        "is_correct": False,
        "outcome": "overridden",
        "metadata": {"source": "j6-retry"},
    }

    try:
        scorer._persist_learning_artifacts(result.decision_id, **kwargs)
        scorer._persist_learning_artifacts(result.decision_id, **kwargs)

        assert list(store._conservation_snapshots) == [
            f"mock:conservation:{result.decision_id}"
        ]
    finally:
        store.close()


def test_persistence_failure_structured_warning(mock_preset, caplog):
    store = _single_failure_store(domain="mock", failure="conservation")
    scorer, result, alternate = _verified_scorer(mock_preset, store)
    caplog.set_level("WARNING", logger="copilot_sdk.scoring.scorer")

    try:
        with pytest.raises(RuntimeError, match="conservation failed"):
            scorer._persist_learning_artifacts(
                result.decision_id,
                actual_action=alternate,
                is_correct=False,
                outcome="overridden",
                metadata={"source": "j6-warning"},
            )
        message = caplog.text
        assert "domain=mock" in message
        assert f"decision={result.decision_id}" in message
        assert "artifact=conservation" in message
        assert "error=RuntimeError: conservation failed" in message
    finally:
        store.close()
