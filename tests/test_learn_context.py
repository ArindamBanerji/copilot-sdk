from __future__ import annotations

from dataclasses import dataclass
import sqlite3

import numpy as np

from copilot_sdk.graph import InMemoryGraphStore, SQLiteGraphStore
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

    @property
    def bootstrap_centroids(self) -> np.ndarray:
        return np.array([[[0.2, 0.3, 0.4], [0.7, 0.6, 0.5]]], dtype=np.float64)


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
        reward_function=reward_function,
    )


def _build_default_sqlite_scorer(tmp_path) -> CompoundingScorer:
    preset = ContextPreset()
    graph_store = SQLiteGraphStore(tmp_path / "default-sqlite.sqlite", domain="context-test")
    gae_scorer = ProfileScorer(
        mu=preset.bootstrap_centroids.copy(),
        actions=list(preset.shape.action_names),
        categories=list(preset.shape.category_names),
    )
    return CompoundingScorer(preset, gae_scorer, graph_store=graph_store)


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


def test_save_outcome_stores_context(tmp_path):
    store = SQLiteGraphStore(tmp_path / "store.sqlite", domain="mock")
    try:
        store.write_decision(
            "mock",
            category="alpha",
            action="approve",
            confidence=0.75,
            factors={"amount": 0.2, "risk": 0.4, "history": 0.6},
            metadata={
                "decision_id": "d-1",
                "category_index": 0,
                "factor_vector": [0.2, 0.4, 0.6],
                "recommended_index": 0,
                "probabilities": [0.75, 0.25],
            },
        )
        store.write_outcome(
            decision_id="d-1",
            actual_action="approve",
            is_correct=True,
            metadata={
                "actual_index": 0,
                "context": {"invoice_id": "INV-001", "amount": 125.5},
            },
            domain=store.domain,
        )

        verified = store.get_verified_decisions("mock")

        assert verified[0]["context"] == {"amount": 125.5, "invoice_id": "INV-001"}
    finally:
        store.close()


def test_default_sqlite_graph_store_persists_learn_context(tmp_path):
    scorer = _build_default_sqlite_scorer(tmp_path)
    result = _score(scorer)

    scorer.learn(
        result.decision_id,
        result.action,
        context={"invoice_id": "INV-SQLITE-001", "supplier_id": "SUP-1"},
    )

    verified = scorer.graph_store.get_verified_decisions("context-test")

    assert len(verified) == 1
    assert verified[0]["decision_id"] == result.decision_id
    assert verified[0]["context"] == {
        "invoice_id": "INV-SQLITE-001",
        "supplier_id": "SUP-1",
    }
    scorer.graph_store.close()


def test_outcome_context_column_migrates_existing_db(tmp_path):
    db_path = tmp_path / "legacy.sqlite"
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(
            """
            CREATE TABLE decisions (
                decision_id TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                category TEXT NOT NULL,
                category_index INTEGER NOT NULL,
                factors_json TEXT NOT NULL,
                factor_vector_json TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                recommended_index INTEGER NOT NULL,
                confidence REAL NOT NULL,
                probabilities_json TEXT NOT NULL,
                created_at REAL NOT NULL
            );
            CREATE TABLE outcomes (
                decision_id TEXT PRIMARY KEY REFERENCES decisions(decision_id),
                actual_action TEXT NOT NULL,
                actual_index INTEGER NOT NULL,
                is_correct INTEGER NOT NULL,
                verified_at REAL NOT NULL
            );
            """
        )
        connection.commit()
    finally:
        connection.close()

    store = SQLiteGraphStore(db_path, domain="mock")
    try:
        columns = {
            row[1]
            for row in store.connection.execute("PRAGMA table_info(outcomes)").fetchall()
        }

        assert "context_json" in columns
    finally:
        store.close()


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
