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
    return CompoundingScorer(preset, engine, graph_store=store)


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


def test_conservation_snapshot_written_when_paused(mock_preset):
    store = InMemoryGraphStore(domain="mock")
    _add_verified(store, "mock", "alpha", 10, correct=False)
    scorer = _make_scorer(mock_preset, store)
    result = scorer.score({"amount": 0.2, "risk": 0.3, "history": 0.4}, "alpha")

    learned = scorer.learn(result.decision_id, result.action)

    assert learned["status"] == "paused"
    assert learned["reason"] == "conservation_red"
    snapshot = store._conservation_snapshots[f"mock:conservation:{result.decision_id}"]
    assert snapshot["status"] == "RED"
    assert snapshot["V"] == 10
    assert snapshot["q"] == 0.0
    assert snapshot["alpha"] == 1 / 3
    assert store.count_verified("mock") == 10
    assert not store._evidence_receipts
    assert store._protocol_centroid_checkpoints
    assert store._fingerprints


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


def test_conservation_outbox_on_snapshot_failure(mock_preset, tmp_path):
    store = _FailingConservationStore(domain="mock")
    _add_verified(store, "mock", "alpha", 10, correct=False)
    scorer = _make_scorer(mock_preset, store)
    scorer._outbox = PersistenceOutbox("mock", db_path=tmp_path / "outbox.db")
    result = scorer.score({"amount": 0.2, "risk": 0.3, "history": 0.4}, "alpha")

    learned = scorer.learn(result.decision_id, result.action)

    assert learned["status"] == "paused"
    assert scorer._outbox.pending_count() == 1


def test_all_five_domains_conservation_status(mock_preset):
    for domain in ("soc", "s2p", "trading", "purchasing", "dataops"):
        store = InMemoryGraphStore(domain=domain)
        _add_verified(store, domain, "alpha", 5)
        scorer = _make_scorer(mock_preset, store, domain=domain)

        state = scorer._evolution_conservation_state()

        assert state is not None
        assert state["alpha"] == 1 / 3
        assert state["alpha"] != state["override_rate"]
