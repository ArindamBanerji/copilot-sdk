"""CC-1/CC-2 canonical convergence measurement tests."""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.self_computation_router import mount_self_computation_router
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer


@pytest.fixture(autouse=True)
def isolate_outbox(tmp_path, monkeypatch) -> Iterator[None]:
    monkeypatch.setenv("CI_PERSISTENCE_OUTBOX_PATH", str(tmp_path / "outbox.db"))
    yield


def _scorer() -> CompoundingScorer:
    return CompoundingScorer.from_preset(
        "trading",
        graph_store=InMemoryGraphStore(domain="trading"),
        profile="test",
    )


def _factors(scorer: CompoundingScorer, value: float) -> dict[str, float]:
    return {name: value for name in scorer._preset.shape.factor_names}


def _score_and_learn(scorer: CompoundingScorer, value: float = 0.1) -> None:
    category = scorer._preset.shape.category_names[0]
    result = scorer.score(_factors(scorer, value), category)
    scorer.learn(result.decision_id, result.action)


def test_centroid_distance_decreases_after_learning() -> None:
    scorer = _scorer()
    _score_and_learn(scorer, 0.1)
    distance_before = scorer.compute_centroid_distance_to_canonical()

    category_index = 0
    action_index = scorer._preset.shape.action_names.index("skip_recommended")
    canonical = scorer._canonical_mu[category_index, action_index]
    near_canonical = {
        name: float(canonical[index])
        for index, name in enumerate(scorer._preset.shape.factor_names)
    }
    for _ in range(20):
        result = scorer.score(near_canonical, scorer._preset.shape.category_names[0])
        scorer.learn(result.decision_id, result.action)

    distance_after = scorer.compute_centroid_distance_to_canonical()
    assert distance_before is not None
    assert distance_after is not None
    assert distance_after < distance_before


def test_centroid_distance_zero_at_canonical() -> None:
    scorer = _scorer()
    assert scorer.compute_centroid_distance_to_canonical() == pytest.approx(0.0)


def test_epsilon_firm_above_threshold_after_learning() -> None:
    scorer = _scorer()
    # A known non-default canonical prior makes the threshold assertion
    # deterministic while still using the real scorer learning path.
    scorer._canonical_mu = np.zeros_like(scorer._canonical_mu)
    for _ in range(20):
        _score_and_learn(scorer, 0.9)

    epsilon = scorer.compute_epsilon_firm()
    assert epsilon is not None
    assert epsilon["epsilon_firm"] > 0.128
    assert epsilon["clears_threshold"] is True


def test_epsilon_firm_below_threshold_at_canonical() -> None:
    epsilon = _scorer().compute_epsilon_firm()
    assert epsilon is not None
    assert epsilon["epsilon_firm"] == pytest.approx(0.0)
    assert epsilon["clears_threshold"] is False


def test_epsilon_firm_returns_none_without_canonical() -> None:
    scorer = _scorer()
    setattr(scorer, "_canonical_mu", None)
    assert scorer.compute_epsilon_firm() is None


def test_distance_on_checkpoint_metadata() -> None:
    scorer = _scorer()
    _score_and_learn(scorer)
    checkpoints = scorer._graph_store.get_centroid_checkpoints("trading", include_v2=True)
    assert checkpoints
    metadata = checkpoints[-1].get("metadata", {})
    assert "centroid_distance_to_canonical" in metadata
    assert metadata["centroid_distance_to_canonical"] is not None


def test_diagnostics_endpoint_200() -> None:
    scorer = _scorer()
    app = FastAPI()
    mount_self_computation_router(
        app,
        scorer._graph_store,
        domain="trading",
        scorer_provider=lambda: scorer,
    )

    response = TestClient(app).get("/api/self/diagnostics")
    payload = response.json()

    assert response.status_code == 200
    assert payload["domain"] == "trading"
    assert payload["centroid_distance_to_canonical"] == pytest.approx(0.0)
    assert payload["epsilon_firm"]["epsilon_firm"] == pytest.approx(0.0)
    assert "iks" in payload
    assert "measurement_state" in payload
    assert "provenance" in payload["measurement_state"]


def test_iks_and_distance_consistent() -> None:
    scorer = _scorer()
    baseline_iks = scorer._compute_checkpoint_iks()
    _score_and_learn(scorer, 0.1)
    distance = scorer.compute_centroid_distance_to_canonical()
    learned_iks = scorer._compute_checkpoint_iks()

    assert distance is not None and distance > 0
    assert learned_iks >= baseline_iks
