from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, cast

import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.self_computation_router import create_self_computation_router
from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring.config import DomainShape
from copilot_sdk.scoring.scorer import CompoundingScorer
from gae.profile_scorer import ProfileScorer


@dataclass(frozen=True)
class RegimePreset:
    name: str = "regime-test"
    shape: DomainShape = DomainShape(
        n_categories=2,
        n_actions=2,
        n_factors=2,
        category_names=("alpha", "beta"),
        action_names=("approve", "review"),
        factor_names=("risk", "history"),
    )
    penalty_ratio: float = 5.0
    eta_confirm: float = 0.05
    eta_override: float = 0.01
    temperature: float = 0.1

    @property
    def bootstrap_centroids(self) -> np.ndarray:
        return np.asarray(
            [
                [[0.2, 0.3], [0.7, 0.6]],
                [[0.3, 0.4], [0.8, 0.7]],
            ],
            dtype=np.float64,
        )


def _make_scorer(store: InMemoryGraphStore) -> CompoundingScorer:
    preset = RegimePreset()
    engine = ProfileScorer(
        mu=preset.bootstrap_centroids.copy(),
        actions=list(preset.shape.action_names),
        categories=list(preset.shape.category_names),
    )
    return CompoundingScorer(cast(Any, preset), engine, graph_store=store)


def _checkpoint(store: InMemoryGraphStore, tag: str, value: float, index: int) -> dict:
    preset = RegimePreset()
    centroids = np.full(preset.bootstrap_centroids.shape, value, dtype=np.float64)
    store.write_centroid_checkpoint(
        checkpoint_id=f"cp-{tag}-{index}",
        domain="regime-test",
        category="alpha",
        action="approve",
        centroids=centroids,
        decisions_count=10,
        verified_count=10,
        iks=0.5,
        shape=list(centroids.shape),
        factor_names_hash="test",
        metadata={
            "regime_tag": tag,
            "dk_weights": np.full((2, 2), value + 1.0).tolist(),
            "temperature": value + 0.1,
        },
    )
    return {"centroids": centroids, "dk_weights": np.full((2, 2), value + 1.0)}


def _seed_verified(store: InMemoryGraphStore, count: int, start: int = 0) -> None:
    for index in range(start, start + count):
        decision_id = store.write_decision(
            "regime-test", "alpha", "approve", 0.8, {"risk": 0.2, "history": 0.8}
        )
        store.write_outcome(
            decision_id,
            "approve",
            True,
            {},
            domain="regime-test",
        )


def test_load_latest_checkpoint_for_regime_and_missing() -> None:
    store = InMemoryGraphStore(domain="regime-test")
    _checkpoint(store, "trending", 1.0, 1)
    _checkpoint(store, "ranging", 2.0, 1)
    _checkpoint(store, "volatile", 3.0, 1)
    _checkpoint(store, "trending", 4.0, 2)
    latest = store.load_latest_checkpoint_for_regime("regime-test", "trending")
    assert latest is not None
    assert latest["checkpoint_id"] == "cp-trending-2"
    assert store.load_latest_checkpoint_for_regime("regime-test", "missing") is None


def test_reinit_strategy_a_replaces_centroids() -> None:
    store = InMemoryGraphStore(domain="regime-test")
    expected = _checkpoint(store, "trending", 1.0, 1)
    scorer = _make_scorer(store)
    scorer._scorer.centroids = np.full_like(scorer._scorer.centroids, 9.0)
    result = scorer.reinitialize_from_regime("trending", "A")
    assert result["success"] is True
    np.testing.assert_allclose(scorer._scorer.centroids, expected["centroids"])


def test_reinit_strategy_b_blends_centroids() -> None:
    store = InMemoryGraphStore(domain="regime-test")
    expected = _checkpoint(store, "trending", 1.0, 1)
    scorer = _make_scorer(store)
    current = np.full_like(scorer._scorer.centroids, 5.0)
    scorer._scorer.centroids = current.copy()
    scorer.reinitialize_from_regime("trending", "B", blend_weight=0.5)
    np.testing.assert_allclose(scorer._scorer.centroids, (current + expected["centroids"]) / 2.0)


def test_reinit_strategy_c_restores_dk_and_legacy_fallback() -> None:
    store = InMemoryGraphStore(domain="regime-test")
    expected = _checkpoint(store, "trending", 1.0, 1)
    scorer = _make_scorer(store)
    result = scorer.reinitialize_from_regime("trending", "C")
    assert result["success"] is True
    np.testing.assert_allclose(np.asarray(scorer.get_dk_weights()), expected["dk_weights"])

    legacy_store = InMemoryGraphStore(domain="regime-test")
    legacy = _checkpoint(legacy_store, "trending", 1.0, 1)
    checkpoint = legacy_store._protocol_centroid_checkpoints["cp-trending-1"]
    checkpoint["metadata"].pop("dk_weights")
    checkpoint["metadata"].pop("temperature")
    legacy_scorer = _make_scorer(legacy_store)
    fallback = legacy_scorer.reinitialize_from_regime("trending", "C")
    assert fallback["fallback_reason"] == "legacy_checkpoint_missing_model_state"


def test_calibration_overlay_effective_v_and_promotion_block() -> None:
    store = InMemoryGraphStore(domain="regime-test")
    _seed_verified(store, 10)
    _checkpoint(store, "trending", 1.0, 1)
    scorer = _make_scorer(store)
    result = scorer.reinitialize_from_regime("trending", "A", v_discount=0.5)
    assert result["success"] is True
    state = scorer.get_conservation_state()
    assert state["status"] == "CALIBRATING"
    assert state["effective_V"] < state["actual_V"]
    evolution_state = scorer._evolution_conservation_state()
    assert evolution_state is not None
    assert evolution_state["status"] == "CALIBRATING"


def test_calibration_clears_after_threshold() -> None:
    store = InMemoryGraphStore(domain="regime-test")
    _seed_verified(store, 10)
    _checkpoint(store, "trending", 1.0, 1)
    scorer = _make_scorer(store)
    scorer.reinitialize_from_regime("trending", "A")
    _seed_verified(store, 10, start=10)
    state = scorer.get_conservation_state()
    assert state["status"] != "CALIBRATING"


def test_reinit_atomic_rollback() -> None:
    class FailingStore(InMemoryGraphStore):
        async def run_transaction(self, operation):
            operation(None)
            raise RuntimeError("forced reinit failure")

    store = FailingStore(domain="regime-test")
    _checkpoint(store, "trending", 1.0, 1)
    scorer = _make_scorer(store)
    before = scorer._scorer.centroids.copy()
    try:
        scorer.reinitialize_from_regime("trending", "A")
    except RuntimeError:
        pass
    else:
        raise AssertionError("re-init failure was not propagated")
    np.testing.assert_allclose(scorer._scorer.centroids, before)
    assert scorer._calibration_overlay is None


def test_regime_reinit_endpoint() -> None:
    store = InMemoryGraphStore(domain="regime-test")
    _checkpoint(store, "trending", 1.0, 1)
    scorer = _make_scorer(store)
    app = FastAPI()
    app.include_router(
        create_self_computation_router(
            store,
            domain="regime-test",
            scorer_provider=lambda: scorer,
        )
    )
    response = TestClient(app).post("/api/self/regime-reinit?regime_tag=trending&strategy=A")
    assert response.status_code == 200
    assert response.json()["success"] is True
