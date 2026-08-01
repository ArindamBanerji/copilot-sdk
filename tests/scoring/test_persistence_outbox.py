from __future__ import annotations

import sqlite3
from pathlib import Path

from gae.profile_scorer import ProfileScorer

from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring.persistence_outbox import PersistenceOutbox
from copilot_sdk.scoring.scorer import CompoundingScorer


class _ReplayStore:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def write_conservation_status(self, **payload):
        self.calls.append(("conservation", payload))

    def write_fingerprint(self, **payload):
        self.calls.append(("fingerprint", payload))

    def append_evidence_receipt(self, **payload):
        self.calls.append(("evidence_receipt", payload))

    def write_centroid_checkpoint(self, **payload):
        self.calls.append(("centroid_checkpoint", payload))


def test_outbox_records_and_replays_each_artifact(tmp_path: Path) -> None:
    outbox = PersistenceOutbox("trading", tmp_path / "outbox.db")
    payloads = {
        "conservation": {"status_id": "c1", "domain": "trading"},
        "fingerprint": {"fingerprint_id": "f1", "domain": "trading"},
        "evidence_receipt": {"receipt_intent_id": "r1", "domain": "trading"},
        "centroid_checkpoint": {"checkpoint_id": "k1", "domain": "trading"},
    }
    for artifact_type, payload in payloads.items():
        outbox.record_failure("decision-1", artifact_type, payload, "AGE unavailable")

    assert outbox.pending_count() == 4
    store = _ReplayStore()
    assert outbox.drain(store) == (4, 0)
    assert outbox.pending_count() == 0
    assert {artifact for artifact, _ in store.calls} == set(payloads)


def test_outbox_failed_replay_remains_pending(tmp_path: Path) -> None:
    outbox = PersistenceOutbox("s2p", tmp_path / "outbox.db")
    outbox.record_failure(
        "decision-2",
        "evidence_receipt",
        {"receipt_intent_id": "r2", "domain": "s2p"},
        "AGE unavailable",
    )

    class _FailingStore:
        def append_evidence_receipt(self, **payload):
            raise RuntimeError("still unavailable")

    assert outbox.drain(_FailingStore()) == (0, 1)
    assert outbox.pending_count() == 1


def test_outbox_abandons_after_max_retries(tmp_path: Path) -> None:
    outbox_path = tmp_path / "retry-limit.db"
    outbox = PersistenceOutbox("trading", outbox_path)
    outbox.record_failure("decision-retry", "conservation", {"V": 1}, "offline")

    class _FailingStore:
        def write_conservation_status(self, **payload):
            raise RuntimeError("still unavailable")

    for _ in range(PersistenceOutbox.MAX_RETRIES):
        assert outbox.drain(_FailingStore()) == (0, 1)

    assert outbox.pending_count() == 0
    with sqlite3.connect(outbox_path) as connection:
        row = connection.execute(
            "SELECT retry_count, status FROM failed_artifacts WHERE decision_id = ?",
            ("decision-retry",),
        ).fetchone()
    assert row == (PersistenceOutbox.MAX_RETRIES, "abandoned")


def test_outbox_abandons_legacy_incompatible_rows(tmp_path: Path) -> None:
    outbox_path = tmp_path / "legacy.db"
    outbox = PersistenceOutbox("soc", outbox_path)
    outbox.record_failure(
        "decision-legacy",
        "conservation",
        {"V": 1},
        "write_conservation_status() missing 10 required positional arguments",
    )

    restored = PersistenceOutbox("soc", outbox_path)

    assert restored.pending_count() == 0
    with sqlite3.connect(outbox_path) as connection:
        row = connection.execute(
            "SELECT status FROM failed_artifacts WHERE decision_id = ?",
            ("decision-legacy",),
        ).fetchone()
    assert row == ("abandoned",)


def test_outbox_deduplicates_pending_artifact(tmp_path: Path) -> None:
    outbox = PersistenceOutbox("soc", tmp_path / "outbox.db")
    outbox.record_failure("decision-3", "conservation", {"V": 1}, "first")
    outbox.record_failure("decision-3", "conservation", {"V": 2}, "second")

    assert outbox.pending_count() == 1
    store = _ReplayStore()
    assert outbox.drain(store) == (1, 0)
    assert store.calls[0][1]["V"] == 2


class _FailingConservationStore(InMemoryGraphStore):
    def write_conservation_status(self, **payload):
        raise RuntimeError("AGE unavailable")


def test_scorer_records_failed_conservation_write(mock_preset, tmp_path: Path, monkeypatch) -> None:
    outbox_path = tmp_path / "scorer-outbox.db"
    monkeypatch.setenv("CI_PERSISTENCE_OUTBOX_PATH", str(outbox_path))
    store = _FailingConservationStore(domain="mock")
    engine = ProfileScorer(
        mu=mock_preset.bootstrap_centroids.copy(),
        actions=list(mock_preset.shape.action_names),
        categories=list(mock_preset.shape.category_names),
    )
    scorer = CompoundingScorer(mock_preset, engine, graph_store=store)
    result = scorer.score(
        {"amount": 0.25, "risk": 0.35, "history": 0.45},
        mock_preset.shape.category_names[0],
    )
    alternate = next(action for action in mock_preset.shape.action_names if action != result.action)
    store.write_outcome(result.decision_id, alternate, False, domain="mock")

    scorer._persist_learning_artifacts(
        result.decision_id,
        actual_action=alternate,
        is_correct=False,
        outcome="overridden",
        category=mock_preset.shape.category_names[0],
    )

    assert PersistenceOutbox("mock", outbox_path).pending_count() == 1
