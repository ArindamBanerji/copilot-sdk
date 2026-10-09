from __future__ import annotations

from dataclasses import replace

import numpy as np

from gae.profile_scorer import ProfileScorer

from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring.config import DomainShape
from copilot_sdk.scoring.persistence_outbox import PersistenceOutbox
from copilot_sdk.scoring.scorer import CompoundingScorer


def _make_scorer(mock_preset, store: InMemoryGraphStore, *, domain: str = "mock") -> CompoundingScorer:
    preset = replace(mock_preset, name=domain)
    engine = ProfileScorer(
        mu=np.zeros(preset.shape.tensor_shape, dtype=np.float64),
        actions=list(preset.shape.action_names),
        categories=list(preset.shape.category_names),
    )
    return CompoundingScorer(preset, engine, graph_store=store, profile="test")


def _add_verified(
    store: InMemoryGraphStore,
    domain: str,
    category: str,
    count: int,
    *,
    correct: bool = True,
) -> None:
    for index in range(count):
        decision_id = store.write_decision(
            domain=domain,
            category=category,
            action="approve",
            confidence=0.8,
            factors={"amount": 0.2, "risk": 0.3, "history": 0.4},
            metadata={"factor_vector": [0.2, 0.3, 0.4]},
        )
        store.write_outcome(
            decision_id,
            actual_action="approve" if correct else "review",
            is_correct=correct,
            metadata={"verified_at": float(index)},
            domain=domain,
        )


def test_conservation_rejection_performs_no_graph_writes(mock_preset):
    store = InMemoryGraphStore(domain="mock")
    _add_verified(store, "mock", "alpha", 10, correct=False)
    scorer = _make_scorer(mock_preset, store)
    result = scorer.score({"amount": 0.2, "risk": 0.3, "history": 0.4}, "alpha")

    learned = scorer.learn(result.decision_id, result.action)

    assert learned["status"] == "paused"
    assert learned["reason"] == "conservation_red"
    assert f"mock:conservation:{result.decision_id}" not in store._conservation_snapshots
    assert store.count_verified("mock") == 10
    assert not store._evidence_receipts
    assert not store._protocol_centroid_checkpoints
    assert not store._fingerprints


def test_conservation_alpha_is_category_coverage(mock_preset):
    shape = DomainShape(
        n_categories=5,
        n_actions=2,
        n_factors=3,
        category_names=("a", "b", "c", "d", "e"),
        action_names=mock_preset.shape.action_names,
        factor_names=mock_preset.shape.factor_names,
    )
    preset = replace(mock_preset, name="mock", shape=shape)
    store = InMemoryGraphStore(domain="mock")
    for category, count in (("a", 20), ("b", 15), ("d", 10), ("e", 8)):
        _add_verified(store, "mock", category, count)
    scorer = _make_scorer(preset, store)

    state = scorer._evolution_conservation_state()

    assert state is not None
    assert state["alpha"] == 0.8
    assert state["category_coverage"] == 0.8
    assert state["alpha"] != state["override_rate"]


def test_conservation_snapshot_written_on_success(mock_preset):
    store = InMemoryGraphStore(domain="mock")
    scorer = _make_scorer(mock_preset, store)
    result = scorer.score({"amount": 0.2, "risk": 0.3, "history": 0.4}, "alpha")

    learned = scorer.learn(result.decision_id, result.action)

    assert not isinstance(learned, dict) or learned.get("paused") is not True
    assert f"mock:conservation:{result.decision_id}" in store._conservation_snapshots
    assert store.count_verified("mock") == 1
    assert store._evidence_receipts
    assert store._protocol_centroid_checkpoints
    assert store._fingerprints


class _FailingConservationStore(InMemoryGraphStore):
    def write_conservation_status(self, *args, **kwargs) -> None:
        raise RuntimeError("snapshot unavailable")


class _OrderedHistoryStore(InMemoryGraphStore):
    def __init__(self, rows: list[dict[str, object]]) -> None:
        super().__init__(domain="mock")
        self.rows = list(rows)

    def get_verified_decisions(self, domain: str) -> list[dict[str, object]]:
        assert domain == "mock"
        return list(self.rows)


def _history_rows(
    *, old_correct: int, recent_correct: int, old_total: int = 2000
) -> list[dict[str, object]]:
    outcomes = ([True] * old_correct) + ([False] * (old_total - old_correct))
    outcomes += ([True] * recent_correct) + ([False] * (400 - recent_correct))
    return [
        {
            "decision_id": f"history-{index:04d}",
            "created_at": float(index),
            "category": "alpha",
            "outcome": "confirmed" if correct else "overridden",
            "is_correct": correct,
        }
        for index, correct in enumerate(outcomes)
    ]


def test_conservation_rejection_does_not_enqueue_snapshot(mock_preset, tmp_path):
    store = _FailingConservationStore(domain="mock")
    _add_verified(store, "mock", "alpha", 10, correct=False)
    scorer = _make_scorer(mock_preset, store)
    scorer._outbox = PersistenceOutbox("mock", db_path=tmp_path / "outbox.db")
    result = scorer.score({"amount": 0.2, "risk": 0.3, "history": 0.4}, "alpha")

    learned = scorer.learn(result.decision_id, result.action)

    assert learned["status"] == "paused"
    assert scorer._outbox.pending_count() == 0


def test_all_five_domains_conservation_status(mock_preset):
    for domain in ("soc", "s2p", "trading", "purchasing", "dataops"):
        store = InMemoryGraphStore(domain=domain)
        _add_verified(store, domain, "alpha", 5)
        scorer = _make_scorer(mock_preset, store, domain=domain)

        state = scorer._evolution_conservation_state()

        assert state is not None
        assert state["alpha"] == 1 / 3
        assert state["alpha"] != state["override_rate"]


def test_recent_degradation_closes_gate_despite_high_lifetime_accuracy(mock_preset):
    rows = _history_rows(old_correct=2000, recent_correct=0)
    store = _OrderedHistoryStore(rows)
    scorer = _make_scorer(mock_preset, store)

    pause = scorer._conservation_pause()

    assert sum(bool(row["is_correct"]) for row in rows) / len(rows) > 0.8
    assert pause is not None
    assert pause["conservation_status"] == "RED"
    assert pause["q"] == 0.0
    assert pause["verified_count"] == 2400


def test_scorer_gate_sorts_before_rolling_q(mock_preset):
    chronological = _history_rows(
        old_correct=500,
        recent_correct=0,
        old_total=500,
    )
    store = _OrderedHistoryStore(list(reversed(chronological)))
    scorer = _make_scorer(mock_preset, store)

    pause = scorer._conservation_pause()

    assert pause is not None
    assert pause["conservation_status"] == "RED"
    assert pause["q"] == 0.0
    assert pause["verified_count"] == 900


def test_status_and_gate_use_identical_rolling_q_v_and_alpha(mock_preset):
    rows = [
        {
            "decision_id": f"parity-{index:04d}",
            "created_at": float(index),
            "category": "alpha",
            "outcome": "overridden" if index == 0 else "confirmed",
            "is_correct": index != 0,
        }
        for index in range(401)
    ]
    rows.extend(
        [
            {
                "decision_id": "pending-observation-like-row",
                "created_at": 402.0,
                "category": "alpha",
                "outcome": None,
            },
            {
                "decision_id": "benchmark-row",
                "created_at": 403.0,
                "category": "alpha",
                "outcome": "confirmed",
                "is_correct": True,
                "context": {"benchmark": True},
            },
        ]
    )
    store = _OrderedHistoryStore(rows)
    scorer = _make_scorer(mock_preset, store)

    gate_state = scorer._evolution_conservation_state()
    status = scorer.get_conservation_state()

    assert gate_state is not None
    assert gate_state["q"] == status["q"] == 1.0
    assert gate_state["verified_count"] == status["V"] == 401
    assert gate_state["alpha"] == status["alpha"] == 1 / 3
