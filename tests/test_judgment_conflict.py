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
from copilot_sdk.scoring.conflict import (
    CONFLICT_HIGH_THRESHOLD,
    CONFLICT_LOW_THRESHOLD,
    JudgmentConflict,
    detect_conflict,
)
from copilot_sdk.scoring.scorer import CompoundingScorer


@dataclass(frozen=True)
class ConflictPreset:
    name: str = "conflict-test"
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


def _build_scorer(tmp_path, graph_store=None) -> CompoundingScorer:
    preset = ConflictPreset()
    scorer = ProfileScorer(
        mu=preset.bootstrap_centroids.copy(),
        actions=list(preset.shape.action_names),
        categories=list(preset.shape.category_names),
    )
    return CompoundingScorer(
        preset,
        scorer,
        graph_store=graph_store or InMemoryGraphStore(),
    )


def test_thresholds_importable():
    assert CONFLICT_LOW_THRESHOLD == 0.30
    assert CONFLICT_HIGH_THRESHOLD == 0.70


def test_detect_conflict_none_when_expected():
    conflict = detect_conflict(
        decision_id="d-1",
        predicted_success=0.5,
        actual_correct=True,
        factors={"amount": 0.2, "risk": 0.8},
        fingerprint_weights={"amount": 1.0, "risk": 0.5},
        factor_names=("amount", "risk"),
    )

    assert conflict is None


def test_detect_conflict_surprising_failure():
    conflict = detect_conflict(
        decision_id="d-1",
        predicted_success=0.91,
        actual_correct=False,
        factors={"amount": 0.2, "risk": 0.8},
        fingerprint_weights={"amount": 1.0, "risk": 0.5},
        factor_names=("amount", "risk"),
    )

    assert isinstance(conflict, JudgmentConflict)
    assert conflict.conflict_type == "surprising_failure"
    assert conflict.predicted_success == pytest.approx(0.91)


def test_detect_conflict_surprising_success():
    conflict = detect_conflict(
        decision_id="d-1",
        predicted_success=0.12,
        actual_correct=True,
        factors={"amount": 0.2, "risk": 0.8},
        fingerprint_weights={"amount": 1.0, "risk": 0.5},
        factor_names=("amount", "risk"),
    )

    assert conflict is not None
    assert conflict.conflict_type == "surprising_success"


def test_detect_conflict_empty_or_zero_fingerprint_returns_empty_contradictions():
    conflict = detect_conflict(
        decision_id="d-1",
        predicted_success=0.9,
        actual_correct=False,
        factors={"amount": 0.2, "risk": 0.8},
        fingerprint_weights={},
        factor_names=("amount", "risk"),
    )

    assert conflict is not None
    assert conflict.contradicting_factors == []


def test_contradicting_factors_sorted_by_contribution():
    conflict = detect_conflict(
        decision_id="d-1",
        predicted_success=0.9,
        actual_correct=False,
        factors={"amount": 0.9, "risk": 0.1, "history": 0.6},
        fingerprint_weights={"amount": 0.4, "risk": 1.0, "history": 0.9},
        factor_names=("amount", "risk", "history"),
    )

    assert conflict is not None
    assert [name for name, _value, _weight in conflict.contradicting_factors] == [
        "risk",
        "amount",
        "history",
    ]


def test_conflict_message_includes_predicted_percentage():
    conflict = detect_conflict(
        decision_id="d-1",
        predicted_success=0.912,
        actual_correct=False,
        factors=[0.2],
        fingerprint_weights={"amount": 1.0},
        factor_names=("amount",),
    )

    assert conflict is not None
    assert "91% success" in conflict.message


def test_factor_dict_conversion():
    conflict = detect_conflict(
        decision_id="d-1",
        predicted_success=0.9,
        actual_correct=False,
        factors={"risk": "0.8"},
        fingerprint_weights={"amount": 1.0, "risk": 1.0},
        factor_names=("amount", "risk"),
    )

    assert conflict is not None
    assert conflict.factors == {"amount": 0.0, "risk": 0.8}


def test_factor_list_tuple_numpy_conversion():
    list_conflict = detect_conflict(
        decision_id="d-list",
        predicted_success=0.9,
        actual_correct=False,
        factors=[0.1, 0.2],
        fingerprint_weights={},
        factor_names=("amount", "risk"),
    )
    tuple_conflict = detect_conflict(
        decision_id="d-tuple",
        predicted_success=0.9,
        actual_correct=False,
        factors=(0.3, 0.4),
        fingerprint_weights={},
        factor_names=("amount", "risk"),
    )
    array_conflict = detect_conflict(
        decision_id="d-array",
        predicted_success=0.9,
        actual_correct=False,
        factors=np.asarray([0.5, 0.6]),
        fingerprint_weights={},
        factor_names=("amount", "risk"),
    )

    assert list_conflict is not None
    assert list_conflict.factors == {"amount": 0.1, "risk": 0.2}
    assert tuple_conflict is not None
    assert tuple_conflict.factors == {"amount": 0.3, "risk": 0.4}
    assert array_conflict is not None
    assert array_conflict.factors == {"amount": 0.5, "risk": 0.6}


def test_factor_sequence_length_must_match_names():
    with pytest.raises(ValueError, match="factor values length"):
        detect_conflict(
            decision_id="d-1",
            predicted_success=0.9,
            actual_correct=False,
            factors=[0.1],
            fingerprint_weights={},
            factor_names=("amount", "risk"),
        )


def test_scorer_last_conflict_resets_on_next_learn(tmp_path):
    graph_store = InMemoryGraphStore()
    scorer = _build_scorer(tmp_path, graph_store=graph_store)
    first = scorer.score({"amount": 0.2, "risk": 0.3, "history": 0.4}, "alpha")
    graph_store._decisions[first.decision_id]["metadata"]["probabilities"] = [0.95, 0.05]

    scorer.learn(first.decision_id, "review")

    assert scorer.last_conflict is not None
    assert scorer.last_conflict.conflict_type == "surprising_failure"

    second = scorer.score({"amount": 0.2, "risk": 0.3, "history": 0.4}, "alpha")
    graph_store._decisions[second.decision_id]["metadata"]["probabilities"] = [0.5, 0.5]

    scorer.learn(second.decision_id, second.action)

    assert scorer.last_conflict is None
    scorer.graph_store.close()


def test_scorer_uses_pre_learn_fingerprint_for_conflict_detection(tmp_path, monkeypatch):
    scorer = _build_scorer(tmp_path)
    result = scorer.score({"amount": 0.9, "risk": 0.1, "history": 0.6}, "alpha")

    calls = []

    def fake_weight_map():
        calls.append(scorer.graph_store.count_verified("test"))
        return {"amount": 1.0, "risk": 0.5, "history": 0.25}

    monkeypatch.setattr(scorer, "_fingerprint_weight_map", fake_weight_map)

    scorer.learn(result.decision_id, result.action)

    assert calls == [0]
    scorer.graph_store.close()


def test_conflict_detection_does_not_block_centroid_update_or_outcome_write(tmp_path):
    scorer = _build_scorer(tmp_path)
    result = scorer.score({"amount": 0.2, "risk": 0.3, "history": 0.4}, "alpha")
    before = scorer.gae_scorer.centroids.copy()

    learn = scorer.learn(result.decision_id, "review")

    assert learn.centroid_delta > 0
    assert not np.array_equal(before, scorer.gae_scorer.centroids)
    assert scorer.graph_store.count_verified("test") == 1
    scorer.graph_store.close()


def test_conflict_detection_runs_before_conservation_pause_without_changing_pause_result(tmp_path):
    graph_store = InMemoryGraphStore()
    scorer = _build_scorer(tmp_path, graph_store=graph_store)
    for index in range(25):
        decision_id = graph_store.write_decision(
            "test",
            category="alpha",
            action="approve",
            confidence=0.9,
            factors={"amount": 0.2, "risk": 0.3, "history": 0.4},
            metadata={
                "decision_id": f"seed-{index}",
                "entity_id": f"seed-{index}",
                "factor_vector": [0.2, 0.3, 0.4],
                "recommended_index": 0,
                "probabilities": [0.9, 0.1],
                "category_index": 0,
            },
        )
        graph_store.write_outcome(
            decision_id=decision_id,
            actual_action="review",
            is_correct=False,
            metadata={"outcome": "overridden", "actual_index": 1},
            domain=graph_store.domain,
        )
    result = scorer.score({"amount": 0.2, "risk": 0.3, "history": 0.4}, "alpha")
    graph_store._decisions[result.decision_id]["metadata"]["probabilities"] = [0.95, 0.05]

    learn = scorer.learn(result.decision_id, "review")

    assert learn["status"] == "paused"
    assert scorer.last_conflict is not None
    assert scorer.last_conflict.conflict_type == "surprising_failure"
    assert graph_store.count_verified("test") == 25
    scorer.graph_store.close()
