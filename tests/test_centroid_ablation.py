from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.self_computation_router import mount_self_computation_router
from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer, ScoreResult


DOMAIN = "trading"


def _factor_hash(names: list[str]) -> str:
    return hashlib.sha256(
        json.dumps(names, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _scorer_and_store() -> tuple[CompoundingScorer, InMemoryGraphStore]:
    store = InMemoryGraphStore(domain=DOMAIN)
    scorer = CompoundingScorer.from_preset(DOMAIN, graph_store=store, profile="test")
    return scorer, store


def _factors(scorer: CompoundingScorer, value: float = 0.5) -> dict[str, float]:
    return {name: value for name in scorer._preset.shape.factor_names}


def _write_checkpoint(
    store: InMemoryGraphStore,
    scorer: CompoundingScorer,
    checkpoint_id: str = "cf-checkpoint",
    centroids: np.ndarray | None = None,
    factor_hash: str | None = None,
) -> None:
    tensor = (
        np.asarray(centroids, dtype=np.float64)
        if centroids is not None
        else scorer._scorer.centroids.copy()
    )
    shape = scorer._preset.shape
    store.write_centroid_checkpoint(
        checkpoint_id=checkpoint_id,
        domain=DOMAIN,
        category=shape.category_names[0],
        action=shape.action_names[0],
        centroids=tensor,
        decisions_count=0,
        verified_count=0,
        iks=0.0,
        shape=list(tensor.shape),
        factor_names_hash=factor_hash
        or _factor_hash(list(shape.factor_names)),
    )


def _client(
    store: InMemoryGraphStore,
    scorer: Any,
) -> TestClient:
    app = FastAPI()
    mount_self_computation_router(
        app,
        store,
        scorer_provider=lambda: scorer,
        domain=DOMAIN,
    )
    return TestClient(app)


def _verified_decision(
    store: InMemoryGraphStore,
    scorer: CompoundingScorer,
    decision_id: str,
    value: float = 0.5,
) -> None:
    shape = scorer._preset.shape
    decision = store.write_decision(
        DOMAIN,
        category=shape.category_names[0],
        action=shape.action_names[0],
        confidence=0.9,
        factors=_factors(scorer, value),
        metadata={"decision_id": decision_id},
    )
    store.write_outcome(decision, shape.action_names[0], True, domain=DOMAIN)


def test_ablation_identity_zero() -> None:
    scorer, store = _scorer_and_store()
    _write_checkpoint(store, scorer)
    for index in range(3):
        _verified_decision(store, scorer, f"identity-{index}", 0.4 + index * 0.1)

    response = _client(store, scorer).get(
        "/api/self/centroid-history/cf-checkpoint/counterfactual?window=20"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["decisions_rescored"] == 3
    assert payload["would_change"] == 0
    assert payload["change_rate"] == 0.0
    assert all(detail["changed"] is False for detail in payload["details"])


def test_ablation_exact_change_count() -> None:
    class FakeScorer:
        _preset = SimpleNamespace(
            shape=SimpleNamespace(
                n_categories=1,
                n_actions=2,
                n_factors=1,
                factor_names=["signal"],
                category_names=["category"],
                action_names=["hold", "approve"],
            )
        )

        def score_read_only(self, factors: dict[str, float], category: str) -> ScoreResult:
            action = "approve" if factors["signal"] > 0.5 else "hold"
            return ScoreResult("preview", action, int(action == "approve"), 1.0, [1.0, 0.0], category, factors)

        def score_with_centroids(
            self, centroids: np.ndarray, factors: dict[str, float], category: str
        ) -> ScoreResult:
            action = "approve" if centroids[0, 0, 0] > 0.5 else "hold"
            return ScoreResult("cf", action, int(action == "approve"), 1.0, [1.0, 0.0], category, factors)

    store = InMemoryGraphStore(domain=DOMAIN)
    fake = FakeScorer()
    _write_checkpoint(
        store,
        fake,  # type: ignore[arg-type]
        centroids=np.asarray([[[0.0], [0.0]]]),
        factor_hash=_factor_hash(["signal"]),
    )
    for decision_id, value in [("flip", 0.8), ("same-1", 0.2), ("same-2", 0.1)]:
        decision = store.write_decision(
            DOMAIN,
            category="category",
            action="hold",
            confidence=0.9,
            factors={"signal": value},
            metadata={"decision_id": decision_id},
        )
        store.write_outcome(decision, "hold", True, domain=DOMAIN)

    payload = _client(store, fake).get(
        "/api/self/centroid-history/cf-checkpoint/counterfactual"
    ).json()
    assert payload["would_change"] == 1
    assert payload["change_rate"] == pytest.approx(1 / 3)


def test_score_with_centroids_does_not_mutate_mu() -> None:
    scorer, store = _scorer_and_store()
    before = scorer._scorer.mu.copy()
    checkpoint_count = len(store.get_centroid_checkpoints(DOMAIN, include_v2=True, limit=None))
    scorer.score_with_centroids(
        before.copy(), _factors(scorer), scorer._preset.shape.category_names[0]
    )
    np.testing.assert_array_equal(scorer._scorer.mu, before)
    assert len(store.get_centroid_checkpoints(DOMAIN, include_v2=True, limit=None)) == checkpoint_count


def test_counterfactual_is_read_only() -> None:
    scorer, store = _scorer_and_store()
    _write_checkpoint(store, scorer)
    _verified_decision(store, scorer, "readonly")
    counts_before = (
        store.count_decisions(DOMAIN),
        store.count_verified(DOMAIN),
        len(store.get_centroid_checkpoints(DOMAIN, include_v2=True, limit=None)),
    )
    client = _client(store, scorer)
    assert client.get("/api/self/centroid-history/cf-checkpoint/counterfactual").status_code == 200
    assert client.get("/api/self/centroid-history/cf-checkpoint/counterfactual").status_code == 200
    counts_after = (
        store.count_decisions(DOMAIN),
        store.count_verified(DOMAIN),
        len(store.get_centroid_checkpoints(DOMAIN, include_v2=True, limit=None)),
    )
    assert counts_after == counts_before


def test_counterfactual_factor_mismatch_409() -> None:
    scorer, store = _scorer_and_store()
    _write_checkpoint(store, scorer, factor_hash="abc")
    response = _client(store, scorer).get(
        "/api/self/centroid-history/cf-checkpoint/counterfactual"
    )
    assert response.status_code == 409


def test_counterfactual_legacy_no_tensor_422() -> None:
    scorer, store = _scorer_and_store()
    store.save_centroids(DOMAIN, "legacy", [0.1], {"iks": 0.0})
    response = _client(store, scorer).get(
        "/api/self/centroid-history/None/counterfactual"
    )
    assert response.status_code == 404

    store.write_centroid_checkpoint(
        "legacy-id",
        DOMAIN,
        scorer._preset.shape.category_names[0],
        scorer._preset.shape.action_names[0],
        None,
        0,
        0,
        0.0,
        list(scorer._scorer.centroids.shape),
        _factor_hash(list(scorer._preset.shape.factor_names)),
    )
    response = _client(store, scorer).get(
        "/api/self/centroid-history/legacy-id/counterfactual"
    )
    assert response.status_code == 422


def test_counterfactual_empty_window() -> None:
    scorer, store = _scorer_and_store()
    _write_checkpoint(store, scorer)
    payload = _client(store, scorer).get(
        "/api/self/centroid-history/cf-checkpoint/counterfactual"
    ).json()
    assert payload["decisions_rescored"] == 0
    assert payload["change_rate"] is None


def test_counterfactual_response_labels() -> None:
    scorer, store = _scorer_and_store()
    _write_checkpoint(store, scorer)
    payload = _client(store, scorer).get(
        "/api/self/centroid-history/cf-checkpoint/counterfactual"
    ).json()
    assert payload["analysis_type"] == "centroid_ablation"
    assert {"dk_weights", "temperature"} <= set(payload["held_fixed"])
    assert "replay" not in payload["description"].lower()


def test_counterfactual_checkpoint_not_found_404() -> None:
    scorer, store = _scorer_and_store()
    assert _client(store, scorer).get(
        "/api/self/centroid-history/missing/counterfactual"
    ).status_code == 404


def test_counterfactual_window_bounds() -> None:
    scorer, store = _scorer_and_store()
    _write_checkpoint(store, scorer)
    client = _client(store, scorer)
    assert client.get("/api/self/centroid-history/cf-checkpoint/counterfactual?window=0").status_code == 422
    assert client.get("/api/self/centroid-history/cf-checkpoint/counterfactual?window=401").status_code == 422
    assert client.get("/api/self/centroid-history/cf-checkpoint/counterfactual?window=200").status_code == 200
