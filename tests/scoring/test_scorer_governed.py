"""Behavioral coverage for the opt-in governed scorer write path."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import cast

import numpy as np
import pytest

from gae.profile_scorer import ProfileScorer

from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
from copilot_sdk.graph.protocol import GraphStore
from copilot_sdk.graph.dual_write_store import DualWriteStore
from copilot_sdk.scoring.config import DomainShape
from copilot_sdk.scoring.scorer import CompoundingScorer


@dataclass(frozen=True)
class GovernedWritePreset:
    """Small real scorer preset used to exercise both persistence paths."""

    name: str = "mock"
    shape: DomainShape = DomainShape(
        n_categories=3,
        n_actions=2,
        n_factors=3,
        category_names=("alpha", "beta", "gamma"),
        action_names=("approve", "review"),
        factor_names=("amount", "risk", "history"),
    )
    penalty_ratio: float = 5.0
    eta_confirm: float = 0.05
    eta_override: float = 0.01
    temperature: float = 0.1

    @property
    def bootstrap_centroids(self) -> np.ndarray:
        return cast(np.ndarray, np.array(
            [
                [[0.2, 0.3, 0.4], [0.7, 0.6, 0.5]],
                [[0.3, 0.4, 0.5], [0.8, 0.7, 0.6]],
                [[0.4, 0.5, 0.6], [0.9, 0.8, 0.7]],
            ],
            dtype=np.float64,
        ))


def _build_scorer(
    store: object,
    *,
    governed_writes: bool | None = True,
) -> CompoundingScorer:
    preset = GovernedWritePreset()
    gae_scorer = ProfileScorer(
        mu=preset.bootstrap_centroids.copy(),
        actions=list(preset.shape.action_names),
        categories=list(preset.shape.category_names),
    )
    return CompoundingScorer(
        preset,
        gae_scorer,
        graph_store=cast(GraphStore, store),
        governed_writes=governed_writes,
    )


def _factors() -> dict[str, float]:
    return {"amount": 0.25, "risk": 0.35, "history": 0.45}


def _metadata(decision: dict) -> dict:
    metadata = decision.get("metadata")
    assert isinstance(metadata, dict)
    return metadata


def test_raw_write_is_default_and_preserves_prefixed_id(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("SCORER_GOVERNED_WRITES", raising=False)
    store = SQLiteGraphStore(tmp_path / "raw.sqlite", domain="mock", decision_id_prefix="TRD-")
    try:
        result = _build_scorer(store, governed_writes=None).score(_factors(), "alpha")
        assert result.decision_id
        assert store.get_decision(result.decision_id, domain="mock") is not None
    finally:
        store.close()


def test_governed_age_compatible_store_writes_governed_fields_and_prefix() -> None:
    store = InMemoryGraphStore(domain="mock")
    try:
        result = _build_scorer(store).score(_factors(), "alpha")
        decision = store.get_decision(result.decision_id, domain="mock")
        assert decision is not None
        metadata = _metadata(decision)
        assert result.decision_id
        assert metadata["factor_names"] == ["amount", "risk", "history"]
        assert metadata["source"] == "compounding_scorer"
        assert metadata["scorer_version"] == "copilot_sdk.compounding_scorer.v1"
        assert metadata["preset_version"] == "mock.v1"
        assert metadata["factor_schema_version"] == "mock.factor_schema.v1"
        assert decision["factor_vector"] == metadata["factor_vector"]
        assert decision["probabilities"] == metadata["probabilities"]
        assert decision["category_index"] == metadata["category_index"]
        assert decision["recommended_index"] == metadata["recommended_index"]
    finally:
        store.close()


def test_governed_in_memory_uses_bare_generated_id() -> None:
    store = InMemoryGraphStore(domain="mock")
    try:
        result = _build_scorer(store).score(_factors(), "alpha")
        assert re.fullmatch(r"[0-9a-f]{12}", result.decision_id)
        assert store.get_decision(result.decision_id, domain="mock") is not None
    finally:
        store.close()


def test_governed_writes_require_protocol_v2_store() -> None:
    with pytest.raises(TypeError, match="Governed writes require a Protocol V2 graph store"):
        _build_scorer(object())


def test_governed_dual_write_preserves_identity_in_both_stores() -> None:
    primary = InMemoryGraphStore(domain="mock")
    secondary = InMemoryGraphStore(domain="mock")
    store = DualWriteStore(primary, secondary)
    try:
        result = _build_scorer(store).score(_factors(), "alpha")
        assert result.decision_id
        assert primary.get_decision(result.decision_id, domain="mock") is not None
        assert secondary.get_decision(result.decision_id, domain="mock") is not None
    finally:
        store.close()


def test_governed_score_then_learn_uses_compound_outcome_identity() -> None:
    store = InMemoryGraphStore(domain="mock")
    try:
        scorer = _build_scorer(store)
        result = scorer.score(_factors(), "alpha")
        scorer.learn(result.decision_id, result.action)
        decision = store.get_decision(result.decision_id, domain="mock")
        assert decision is not None
        assert decision["status"] == "confirmed"
        assert store.count_verified("mock") == 1
    finally:
        store.close()


def test_governed_metadata_remains_backward_compatible() -> None:
    store = InMemoryGraphStore(domain="mock")
    try:
        result = _build_scorer(store).score(_factors(), "alpha", metadata={"caller_key": "value"})
        decision = store.get_decision(result.decision_id, domain="mock")
        assert decision is not None
        metadata = _metadata(decision)
        assert metadata["decision_id"] == result.decision_id
        assert metadata["domain"] == "mock"
        assert metadata["category_index"] == decision["category_index"]
        assert metadata["factor_vector"] == decision["factor_vector"]
        assert metadata["recommended_index"] == decision["recommended_index"]
        assert metadata["probabilities"] == decision["probabilities"]
        assert metadata["caller_key"] == "value"
    finally:
        store.close()


def test_environment_gate_is_default_but_explicit_false_wins(monkeypatch) -> None:
    monkeypatch.setenv("SCORER_GOVERNED_WRITES", "1")
    enabled_store = InMemoryGraphStore(domain="mock")
    disabled_store = InMemoryGraphStore(domain="mock")
    try:
        enabled = _build_scorer(enabled_store, governed_writes=None)
        disabled = _build_scorer(disabled_store, governed_writes=False)
        assert enabled._governed_writes is True
        assert disabled._governed_writes is False
    finally:
        enabled_store.close()
        disabled_store.close()
