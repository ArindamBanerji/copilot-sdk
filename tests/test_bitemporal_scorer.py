from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

GAE_PATH = Path(__file__).resolve().parents[1] / "graph-attention-engine-v50"
if str(GAE_PATH) not in sys.path:
    sys.path.insert(0, str(GAE_PATH))

profile_module = pytest.importorskip("gae.profile_scorer")
ProfileScorer = profile_module.ProfileScorer

from copilot_sdk.backend.self_computation_router import mount_self_computation_router
from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring.config import DomainShape
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.scoring.storage import DecisionStore
from copilot_sdk.transfer import TransferPattern


@dataclass(frozen=True)
class BitemporalPreset:
    name: str = "bitemporal-test"
    shape: DomainShape = DomainShape(
        n_categories=1,
        n_actions=2,
        n_factors=3,
        category_names=("alpha",),
        action_names=("approve", "review"),
        factor_names=("amount", "risk", "history"),
    )
    penalty_ratio: float = 5.0
    eta_confirm: float = 0.05
    eta_override: float = 0.01
    temperature: float = 0.1

    @property
    def bootstrap_centroids(self) -> np.ndarray:
        return np.array([[[0.2, 0.3, 0.4], [0.8, 0.7, 0.6]]], dtype=np.float64)


def _build_scorer(
    tmp_path: Path,
    *,
    consolidation_enabled: bool = False,
) -> tuple[CompoundingScorer, InMemoryGraphStore]:
    preset = BitemporalPreset()
    graph_store = InMemoryGraphStore()
    scorer = ProfileScorer(
        mu=preset.bootstrap_centroids.copy(),
        actions=list(preset.shape.action_names),
        categories=list(preset.shape.category_names),
    )
    wrapper = CompoundingScorer(
        preset,
        DecisionStore(tmp_path / "bitemporal.sqlite"),
        scorer,
        graph_store=graph_store,
        consolidation_enabled=consolidation_enabled,
    )
    wrapper._conservation_pause = lambda: None
    return wrapper, graph_store


def _score(
    scorer: CompoundingScorer,
    *,
    amount: float = 0.2,
    metadata: dict | None = None,
):
    return scorer.score(
        {"amount": amount, "risk": 0.3, "history": 0.4},
        "alpha",
        metadata=metadata,
    )


def test_extract_decision_timestamp_from_created_at(tmp_path: Path) -> None:
    scorer, _graph_store = _build_scorer(tmp_path)

    assert scorer._extract_decision_timestamp({"created_at": 1_779_148_800.0}) == "2026-05-19T00:00:00Z"
    scorer.store.close()


def test_extract_decision_timestamp_from_explicit_key(tmp_path: Path) -> None:
    scorer, _graph_store = _build_scorer(tmp_path)
    decision = {
        "decision_time": "2026-05-20T12:00:00+02:00",
        "created_at": 1_779_148_800.0,
    }

    assert scorer._extract_decision_timestamp(decision) == "2026-05-20T10:00:00Z"
    scorer.store.close()


def test_extract_decision_timestamp_missing_returns_none(tmp_path: Path) -> None:
    scorer, _graph_store = _build_scorer(tmp_path)

    assert scorer._extract_decision_timestamp({"metadata": {"note": "no timestamp"}}) is None
    scorer.store.close()


def test_learn_checkpoint_has_per_decision_time_range(tmp_path: Path) -> None:
    scorer, graph_store = _build_scorer(tmp_path)
    result = _score(scorer, metadata={"decision_time": "2026-05-19T10:00:00Z"})

    scorer.learn(result.decision_id, result.action)

    checkpoint = graph_store.get_centroid_checkpoints()[0]
    assert checkpoint["decision_time_start"] == "2026-05-19T10:00:00Z"
    assert checkpoint["decision_time_end"] == "2026-05-19T10:00:00Z"
    scorer.store.close()


def test_non_consolidated_no_timestamp_passes_none(tmp_path: Path) -> None:
    scorer, graph_store = _build_scorer(tmp_path)
    scorer._batch_decision_time_start = "2026-05-19T10:00:00Z"
    scorer._batch_decision_time_end = "2026-05-19T10:00:00Z"

    second = _score(scorer, amount=0.25)
    decision = graph_store._decisions[second.decision_id]
    decision["created_at"] = None
    decision["metadata"].pop("created_at", None)
    scorer.learn(second.decision_id, second.action)

    checkpoint = graph_store.get_centroid_checkpoints()[-1]
    assert checkpoint["decision_time_start"] is None
    assert checkpoint["decision_time_end"] is None
    scorer.store.close()


def test_consolidation_flush_passes_batch_time_range(tmp_path: Path) -> None:
    scorer, graph_store = _build_scorer(tmp_path, consolidation_enabled=True)
    first = _score(scorer, metadata={"decision_time": "2026-05-20T10:00:00Z"})
    second = _score(scorer, amount=0.25, metadata={"decision_time": "2026-05-19T10:00:00Z"})

    scorer.learn(first.decision_id, first.action)
    scorer.learn(second.decision_id, second.action)
    assert scorer.flush_centroids(reason="end-of-batch") == 2

    checkpoint = graph_store.get_centroid_checkpoints()[0]
    assert checkpoint["decision_time_start"] == "2026-05-19T10:00:00Z"
    assert checkpoint["decision_time_end"] == "2026-05-20T10:00:00Z"
    scorer.store.close()


def test_consolidate_true_passes_batch_time_range(tmp_path: Path) -> None:
    scorer, graph_store = _build_scorer(tmp_path, consolidation_enabled=True)
    first = _score(scorer, metadata={"decision_time": "2026-05-18T10:00:00Z"})
    second = _score(scorer, amount=0.25, metadata={"decision_time": "2026-05-19T10:00:00Z"})

    scorer.learn(first.decision_id, first.action)
    scorer.learn(second.decision_id, second.action, consolidate=True)

    checkpoint = graph_store.get_centroid_checkpoints()[0]
    assert checkpoint["decision_time_start"] == "2026-05-18T10:00:00Z"
    assert checkpoint["decision_time_end"] == "2026-05-19T10:00:00Z"
    scorer.store.close()


def test_batch_range_resets_after_flush(tmp_path: Path) -> None:
    scorer, _graph_store = _build_scorer(tmp_path, consolidation_enabled=True)
    result = _score(scorer, metadata={"decision_time": "2026-05-19T10:00:00Z"})

    scorer.learn(result.decision_id, result.action)
    scorer.flush_centroids()

    assert scorer._batch_decision_time_start is None
    assert scorer._batch_decision_time_end is None
    scorer.store.close()


def test_batch_range_resets_after_consolidate_true(tmp_path: Path) -> None:
    scorer, _graph_store = _build_scorer(tmp_path, consolidation_enabled=True)
    result = _score(scorer, metadata={"decision_time": "2026-05-19T10:00:00Z"})

    scorer.learn(result.decision_id, result.action, consolidate=True)

    assert scorer._batch_decision_time_start is None
    assert scorer._batch_decision_time_end is None
    scorer.store.close()


def test_warm_start_checkpoint_has_null_decision_range(tmp_path: Path) -> None:
    scorer = CompoundingScorer.from_preset(
        "s2p",
        db_path=str(tmp_path / "s2p.sqlite"),
        graph_store=InMemoryGraphStore(),
    )
    pattern = TransferPattern(
        pattern_id="p1",
        source_copilot="dataops",
        pattern_type="centroid_delta",
        category="price_variance",
        action="auto_approve",
        win_rate=0.8,
        centroid_delta=[0.05 for _ in range(7)],
        confidence=0.9,
    )

    scorer.warm_start([pattern])

    checkpoint = scorer.graph_store.get_centroid_checkpoints(limit=1)[0]
    assert checkpoint["decision_time_start"] is None
    assert checkpoint["decision_time_end"] is None
    scorer.store.close()


def test_centroid_history_accepts_checkpoint_time_filters() -> None:
    class CapturingStore(InMemoryGraphStore):
        def __init__(self) -> None:
            super().__init__()
            self.kwargs: dict | None = None

        def get_centroid_checkpoints(self, limit: int = 50, **kwargs) -> list[dict]:
            self.kwargs = {"limit": limit, **kwargs}
            return []

    store = CapturingStore()
    app = FastAPI()
    mount_self_computation_router(app, store)

    response = TestClient(app).get(
        "/api/self/centroid-history?checkpoint_time_start=2026-05-19T00:00:00Z"
        "&checkpoint_time_end=2026-05-20T00:00:00Z"
    )

    assert response.status_code == 200
    assert store.kwargs == {
        "limit": 50,
        "checkpoint_time_start": "2026-05-19T00:00:00Z",
        "checkpoint_time_end": "2026-05-20T00:00:00Z",
    }


def test_centroid_history_accepts_decision_time_filters() -> None:
    class CapturingStore(InMemoryGraphStore):
        def __init__(self) -> None:
            super().__init__()
            self.kwargs: dict | None = None

        def get_centroid_checkpoints(self, limit: int = 50, **kwargs) -> list[dict]:
            self.kwargs = {"limit": limit, **kwargs}
            return []

    store = CapturingStore()
    app = FastAPI()
    mount_self_computation_router(app, store)

    response = TestClient(app).get(
        "/api/self/centroid-history?decision_time_start=2026-05-19T00:00:00Z"
        "&decision_time_end=2026-05-20T00:00:00Z&category=alpha"
    )

    assert response.status_code == 200
    assert store.kwargs == {
        "limit": 50,
        "decision_time_start": "2026-05-19T00:00:00Z",
        "decision_time_end": "2026-05-20T00:00:00Z",
        "category": "alpha",
    }


def test_centroid_history_without_filters_unchanged() -> None:
    store = InMemoryGraphStore()
    store.save_centroids("decision-1", "alpha", {"alpha": [0.1]}, metadata={"iks": 1.0})
    app = FastAPI()
    mount_self_computation_router(app, store)

    payload = TestClient(app).get("/api/self/centroid-history").json()

    assert payload["total"] == 1
    assert payload["checkpoints"][0]["decision_id"] == "decision-1"
