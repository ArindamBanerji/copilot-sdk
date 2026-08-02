from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest
from gae.profile_scorer import ProfileScorer

from copilot_sdk.evolution.ledger import InMemoryEvolutionLedger
from copilot_sdk.evolution.protocol import EvolutionEvent, EvolutionStore
from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring.persistence_outbox import PersistenceOutbox
from copilot_sdk.scoring.scorer import CompoundingScorer


class FailingGraphStore(InMemoryGraphStore):
    """Stateful test double that can be repaired without replacing the store."""

    def __init__(self, *, domain: str) -> None:
        super().__init__(domain=domain)
        self.fail_decision = False
        self.fail_outcome = False
        self.fail_evolution = False

    def write_decision(self, *args: Any, **kwargs: Any) -> str:
        if self.fail_decision:
            raise ConnectionError("AGE unavailable for Decision write")
        return super().write_decision(*args, **kwargs)

    def write_outcome(self, *args: Any, **kwargs: Any) -> None:
        if self.fail_outcome:
            raise ConnectionError("AGE unavailable for Outcome write")
        super().write_outcome(*args, **kwargs)

    def write_evolution_event(
        self,
        event_id: str,
        domain: str,
        event_type: str,
        rule_name: str,
        variant_id: str,
        source_copilot: str | None = None,
        source_rule: str | None = None,
        metric: float | None = None,
        shadow_batch_size: int | None = None,
        min_shadow_batches: int | None = None,
        metadata: dict[str, Any] | None = None,
        decision_id: str | None = None,
    ) -> None:
        if self.fail_evolution:
            raise ConnectionError("AGE unavailable for evolution write")
        super().write_evolution_event(
            event_id=event_id,
            domain=domain,
            event_type=event_type,
            rule_name=rule_name,
            variant_id=variant_id,
            source_copilot=source_copilot,
            source_rule=source_rule,
            metric=metric,
            shadow_batch_size=shadow_batch_size,
            min_shadow_batches=min_shadow_batches,
            metadata=metadata,
            decision_id=decision_id,
        )


def _scorer(mock_preset, store: InMemoryGraphStore) -> CompoundingScorer:
    engine = ProfileScorer(
        mu=mock_preset.bootstrap_centroids.copy(),
        actions=list(mock_preset.shape.action_names),
        categories=list(mock_preset.shape.category_names),
    )
    return CompoundingScorer(mock_preset, engine, graph_store=store)


def _payload(decision_id: str) -> dict[str, Any]:
    return {
        "domain": "mock",
        "category": "alpha",
        "action": "approve",
        "confidence": 0.8,
        "factors": {"amount": 0.2, "risk": 0.3, "history": 0.4},
        "metadata": {"decision_id": decision_id},
    }


def test_score_queues_decision_on_store_failure(mock_preset, tmp_path: Path) -> None:
    store = FailingGraphStore(domain="mock")
    store.fail_decision = True
    scorer = _scorer(mock_preset, store)
    scorer._outbox = PersistenceOutbox("mock", tmp_path / "outbox.db")

    result = scorer.score({"amount": 0.2, "risk": 0.3, "history": 0.4}, "alpha")

    assert result.confidence >= 0.0
    assert result.action
    assert scorer._outbox.pending_count() == 1


def test_score_decision_drain_replays(mock_preset, tmp_path: Path) -> None:
    store = FailingGraphStore(domain="mock")
    scorer = _scorer(mock_preset, store)
    outbox = PersistenceOutbox("mock", tmp_path / "outbox.db")
    scorer._outbox = outbox
    decision_id = "queued-decision"
    outbox.record_failure(decision_id, "decision", _payload(decision_id), "AGE unavailable")

    assert outbox.drain(store) == (1, 0)
    assert outbox.pending_count() == 0
    assert store.get_decision(decision_id, domain="mock") is not None


def test_score_outbox_replay_preserves_decision_id(mock_preset, tmp_path: Path) -> None:
    store = FailingGraphStore(domain="mock")
    store.fail_decision = True
    scorer = _scorer(mock_preset, store)
    outbox = PersistenceOutbox("mock", tmp_path / "outbox.db")
    scorer._outbox = outbox

    result = scorer.score({"amount": 0.2, "risk": 0.3, "history": 0.4}, "alpha")
    store.fail_decision = False

    assert outbox.drain(store) == (1, 0)
    persisted = store.get_decision(result.decision_id, domain="mock")
    assert persisted is not None
    assert persisted["decision_id"] == result.decision_id


def test_learn_finds_replayed_decision(mock_preset, tmp_path: Path) -> None:
    store = FailingGraphStore(domain="mock")
    store.fail_decision = True
    scorer = _scorer(mock_preset, store)
    outbox = PersistenceOutbox("mock", tmp_path / "outbox.db")
    scorer._outbox = outbox

    result = scorer.score({"amount": 0.2, "risk": 0.3, "history": 0.4}, "alpha")
    store.fail_decision = False
    assert outbox.drain(store) == (1, 0)

    learned = scorer.learn(result.decision_id, result.action)

    assert not isinstance(learned, dict)
    assert learned.decision_id == result.decision_id


def test_outbox_cleared_on_reset(mock_preset, tmp_path: Path) -> None:
    store = FailingGraphStore(domain="mock")
    scorer = _scorer(mock_preset, store)
    outbox = PersistenceOutbox("mock", tmp_path / "outbox.db")
    scorer._outbox = outbox
    outbox.record_failure("stale-decision", "decision", _payload("stale-decision"), "AGE unavailable")

    assert outbox.pending_count() == 1
    scorer.domain_scoped_reset()

    assert outbox.pending_count() == 0
    new_scorer = _scorer(mock_preset, store)
    new_scorer._outbox = PersistenceOutbox("mock", tmp_path / "outbox.db")
    assert new_scorer._outbox.pending_count() == 0


def test_evolution_queues_on_failure(tmp_path: Path) -> None:
    store = FailingGraphStore(domain="mock")
    store.fail_evolution = True
    outbox = PersistenceOutbox("mock", tmp_path / "outbox.db")
    ledger = InMemoryEvolutionLedger(
        evolution_store=cast(EvolutionStore, store),
        domain="mock",
        outbox=outbox,
    )

    ledger.append(EvolutionEvent(event_type="rejected", rule_name="rule", variant_id="v1"))

    assert ledger.event_count == 1
    assert outbox.pending_count() == 1


def test_evolution_drain_replays(tmp_path: Path) -> None:
    store = FailingGraphStore(domain="mock")
    outbox = PersistenceOutbox("mock", tmp_path / "outbox.db")
    payload = {
        "event_id": "event-1",
        "domain": "mock",
        "event_type": "rejected",
        "rule_name": "rule",
        "variant_id": "v1",
        "metadata": {"reason": "test"},
    }
    outbox.record_failure("event-1", "evolution", payload, "AGE unavailable")

    assert outbox.drain(store) == (1, 0)
    assert outbox.pending_count() == 0
    assert store.get_evolution_events("mock")


def test_evolution_ledger_wires_decision_edge(tmp_path: Path) -> None:
    store = FailingGraphStore(domain="mock")
    store.write_decision(**_payload("decision-1"))
    ledger = InMemoryEvolutionLedger(
        evolution_store=cast(EvolutionStore, store),
        domain="mock",
        outbox=PersistenceOutbox("mock", tmp_path / "outbox.db"),
    )

    ledger.append(
        EvolutionEvent(event_type="promoted", rule_name="rule", variant_id="v1"),
        decision_id="decision-1",
    )

    assert any(
        edge["edge_type"] == "TRIGGERED_EVOLUTION"
        and edge["decision_id"] == "decision-1"
        for edge in store._edges
    )


def test_learn_remains_fail_closed(mock_preset, tmp_path: Path) -> None:
    store = FailingGraphStore(domain="mock")
    scorer = _scorer(mock_preset, store)
    scorer._outbox = PersistenceOutbox("mock", tmp_path / "outbox.db")
    result = scorer.score({"amount": 0.2, "risk": 0.3, "history": 0.4}, "alpha")
    store.fail_outcome = True

    with pytest.raises(ConnectionError, match="Outcome write"):
        scorer.learn(result.decision_id, result.action)

    assert scorer._outbox.pending_count() == 0
