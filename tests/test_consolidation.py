from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pytest

GAE_PATH = Path(__file__).resolve().parents[1] / "graph-attention-engine-v50"
if str(GAE_PATH) not in sys.path:
    sys.path.insert(0, str(GAE_PATH))

profile_module = pytest.importorskip("gae.profile_scorer")
ProfileScorer = profile_module.ProfileScorer

from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring.config import DomainShape
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.scoring.storage import DecisionStore


@dataclass(frozen=True)
class ConsolidationPreset:
    name: str = "consolidation-test"
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


def _build_scorer(tmp_path, *, consolidation_enabled=False) -> tuple[CompoundingScorer, InMemoryGraphStore]:
    preset = ConsolidationPreset()
    store = DecisionStore(tmp_path / "consolidation.sqlite")
    graph_store = InMemoryGraphStore()
    scorer = ProfileScorer(
        mu=preset.bootstrap_centroids.copy(),
        actions=list(preset.shape.action_names),
        categories=list(preset.shape.category_names),
    )
    wrapper = CompoundingScorer(
        preset,
        store,
        scorer,
        graph_store=graph_store,
        consolidation_enabled=consolidation_enabled,
    )
    wrapper._conservation_pause = lambda: None
    return wrapper, graph_store


def _score(scorer: CompoundingScorer, amount: float = 0.2):
    return scorer.score({"amount": amount, "risk": 0.3, "history": 0.4}, "alpha")


def test_default_behavior_saves_centroids_every_successful_learn(tmp_path):
    scorer, graph_store = _build_scorer(tmp_path)
    first = _score(scorer, 0.2)
    second = _score(scorer, 0.25)

    scorer.learn(first.decision_id, first.action)
    scorer.learn(second.decision_id, second.action)

    checkpoints = graph_store.get_centroid_checkpoints()
    assert len(checkpoints) == 2
    assert checkpoints[0]["metadata"] == {"iks": checkpoints[0]["metadata"]["iks"]}
    assert "consolidation" not in checkpoints[0]["metadata"]
    scorer.store.close()


def test_consolidation_enabled_buffers_persistence(tmp_path):
    scorer, graph_store = _build_scorer(tmp_path, consolidation_enabled=True)
    first = _score(scorer, 0.2)
    second = _score(scorer, 0.25)

    scorer.learn(first.decision_id, first.action)
    scorer.learn(second.decision_id, second.action)

    assert graph_store.get_centroid_checkpoints() == []
    assert graph_store.count_verified() == 2
    scorer.store.close()


def test_consolidation_in_memory_centroids_update_while_buffered(tmp_path):
    scorer, graph_store = _build_scorer(tmp_path, consolidation_enabled=True)
    result = _score(scorer)
    before = scorer.gae_scorer.centroids.copy()

    learn = scorer.learn(result.decision_id, "review")

    assert learn.centroid_delta > 0
    assert not np.array_equal(before, scorer.gae_scorer.centroids)
    assert graph_store.get_centroid_checkpoints() == []
    scorer.store.close()


def test_consolidate_true_saves_checkpoint_with_metadata(tmp_path):
    scorer, graph_store = _build_scorer(tmp_path, consolidation_enabled=True)
    first = _score(scorer, 0.2)
    second = _score(scorer, 0.25)

    scorer.learn(first.decision_id, first.action)
    scorer.learn(second.decision_id, second.action, consolidate=True)

    checkpoints = graph_store.get_centroid_checkpoints()
    assert len(checkpoints) == 1
    assert checkpoints[0]["decision_id"] == second.decision_id
    assert checkpoints[0]["metadata"]["boundary"] == "learn"
    assert checkpoints[0]["metadata"]["decisions_in_batch"] == 2
    assert checkpoints[0]["metadata"]["consolidation"] is True
    assert "iks" in checkpoints[0]["metadata"]
    assert scorer.flush_centroids() == 0
    scorer.store.close()


def test_flush_centroids_saves_and_resets_count(tmp_path):
    scorer, graph_store = _build_scorer(tmp_path, consolidation_enabled=True)
    first = _score(scorer, 0.2)
    second = _score(scorer, 0.25)

    scorer.learn(first.decision_id, first.action)
    scorer.learn(second.decision_id, second.action)
    flushed = scorer.flush_centroids(reason="end-of-batch")

    checkpoints = graph_store.get_centroid_checkpoints()
    assert flushed == 2
    assert len(checkpoints) == 1
    assert checkpoints[0]["decision_id"] == second.decision_id
    assert checkpoints[0]["metadata"]["boundary"] == "end-of-batch"
    assert checkpoints[0]["metadata"]["decisions_in_batch"] == 2
    assert scorer.flush_centroids() == 0
    scorer.store.close()


def test_flush_centroids_empty_returns_zero_without_save(tmp_path):
    scorer, graph_store = _build_scorer(tmp_path, consolidation_enabled=True)

    assert scorer.flush_centroids() == 0
    assert graph_store.get_centroid_checkpoints() == []
    scorer.store.close()


def test_flush_centroids_disabled_returns_zero_without_changing_default_behavior(tmp_path):
    scorer, graph_store = _build_scorer(tmp_path)
    result = _score(scorer)
    scorer.learn(result.decision_id, result.action)

    assert scorer.flush_centroids() == 0
    assert len(graph_store.get_centroid_checkpoints()) == 1
    scorer.store.close()


def test_conflict_detection_not_delayed_by_consolidation(tmp_path):
    scorer, graph_store = _build_scorer(tmp_path, consolidation_enabled=True)
    result = _score(scorer)
    graph_store._decisions[result.decision_id]["metadata"]["probabilities"] = [0.95, 0.05]

    scorer.learn(result.decision_id, "review")

    assert scorer.last_conflict is not None
    assert scorer.last_conflict.conflict_type == "surprising_failure"
    assert graph_store.get_centroid_checkpoints() == []
    scorer.store.close()


def test_write_outcome_still_runs_every_learn_when_buffered(tmp_path):
    scorer, graph_store = _build_scorer(tmp_path, consolidation_enabled=True)
    first = _score(scorer, 0.2)
    second = _score(scorer, 0.25)

    scorer.learn(first.decision_id, first.action)
    scorer.learn(second.decision_id, second.action)

    verified = graph_store.get_verified_decisions()
    assert len(verified) == 2
    assert {decision["decision_id"] for decision in verified} == {
        first.decision_id,
        second.decision_id,
    }
    scorer.store.close()


def test_existing_callers_remain_compatible(tmp_path):
    scorer, _graph_store = _build_scorer(tmp_path)
    result = _score(scorer)

    learn = scorer.learn(result.decision_id, result.action)

    assert learn.decision_id == result.decision_id
    scorer.store.close()


def test_consolidated_learn_context_keyword_remains_compatible(tmp_path):
    scorer, graph_store = _build_scorer(tmp_path, consolidation_enabled=True)
    result = _score(scorer)

    learn = scorer.learn(
        result.decision_id,
        result.action,
        consolidate=True,
        context={"invoice_id": "INV-001"},
    )

    assert learn.decision_id == result.decision_id
    verified = graph_store.get_verified_decisions()
    assert verified[0]["outcome_metadata"]["context"] == {"invoice_id": "INV-001"}
    assert len(graph_store.get_centroid_checkpoints()) == 1
    scorer.store.close()
