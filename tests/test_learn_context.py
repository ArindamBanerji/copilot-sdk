from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from typing import cast

import numpy as np

from copilot_sdk.graph import InMemoryGraphStore
from tests.graph_store_test_helpers import make_memory_store
from copilot_sdk.scoring.config import DomainShape
from copilot_sdk.scoring.scorer import CompoundingScorer

from gae.profile_scorer import ProfileScorer


@dataclass(frozen=True)
class ContextPreset:
    name: str = "context-test"
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
        return cast(
            np.ndarray,
            np.array([[[0.2, 0.3, 0.4], [0.7, 0.6, 0.5]]], dtype=np.float64),
        )


class RecordingReward:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def compute(self, recommended_action: str, actual_action: str, outcome: dict) -> float:
        self.calls.append(
            {
                "recommended_action": recommended_action,
                "actual_action": actual_action,
                "outcome": dict(outcome),
            }
        )
        return 1.0


def _build_scorer(tmp_path, reward_function=None) -> CompoundingScorer:
    preset = ContextPreset()
    graph_store = InMemoryGraphStore()
    gae_scorer = ProfileScorer(
        mu=preset.bootstrap_centroids.copy(),
        actions=list(preset.shape.action_names),
        categories=list(preset.shape.category_names),
    )
    return CompoundingScorer(
        preset,
        gae_scorer,
        graph_store=graph_store,
        profile="test",
        reward_function=reward_function,
    )


def _build_default_sqlite_scorer(tmp_path) -> CompoundingScorer:
    preset = ContextPreset()
    graph_store = make_memory_store(tmp_path / "default-sqlite.sqlite", domain="context-test")
    gae_scorer = ProfileScorer(
        mu=preset.bootstrap_centroids.copy(),
        actions=list(preset.shape.action_names),
        categories=list(preset.shape.category_names),
    )
    return CompoundingScorer(preset, gae_scorer, graph_store=graph_store, profile="test")


def _score(scorer: CompoundingScorer):
    return scorer.score({"amount": 0.2, "risk": 0.4, "history": 0.6}, "alpha")


def test_learn_accepts_context(tmp_path):
    scorer = _build_scorer(tmp_path)
    result = _score(scorer)

    learn = scorer.learn(result.decision_id, result.action, context={"invoice_id": "INV-001"})

    assert learn.decision_id == result.decision_id
    verified = scorer.graph_store.get_verified_decisions("test")
    assert verified[0]["outcome_metadata"]["context"] == {"invoice_id": "INV-001"}
    scorer.graph_store.close()


def test_learn_without_context_backward_compatible(tmp_path):
    scorer = _build_scorer(tmp_path)
    result = _score(scorer)

    learn = scorer.learn(result.decision_id, result.action)

    assert learn.decision_id == result.decision_id
    verified = scorer.graph_store.get_verified_decisions("test")
    assert "context" not in verified[0]["outcome_metadata"]
    scorer.graph_store.close()








def test_context_available_in_reward_function(tmp_path):
    reward = RecordingReward()
    scorer = _build_scorer(tmp_path, reward_function=reward)
    result = _score(scorer)

    learn = scorer.learn(
        result.decision_id,
        result.action,
        context={"invoice_id": "INV-001", "recovery_pct": 80},
    )

    assert learn.reward_raw == 1.0
    assert reward.calls[0]["outcome"] == {
        "invoice_id": "INV-001",
        "outcome": "confirmed",
        "recovery_pct": 80,
    }
    scorer.graph_store.close()


def test_existing_reward_function_without_context_still_works(tmp_path):
    reward = RecordingReward()
    scorer = _build_scorer(tmp_path, reward_function=reward)
    result = _score(scorer)

    learn = scorer.learn(result.decision_id, result.action)

    assert learn.reward_raw == 1.0
    assert reward.calls[0]["outcome"] == {"outcome": "confirmed"}
    scorer.graph_store.close()

