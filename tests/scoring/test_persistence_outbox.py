from __future__ import annotations

import sqlite3
import logging
import re
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from gae.profile_scorer import ProfileScorer

from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring.persistence_outbox import CURRENT_PAYLOAD_SCHEMA, PersistenceOutbox
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

    def write_decision(self, **payload):
        self.calls.append(("decision", payload))

    def write_evolution_event(self, **payload):
        self.calls.append(("evolution", payload))


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


def test_outbox_abandons_schema_incompatible_rows(tmp_path: Path) -> None:
    outbox_path = tmp_path / "schema.db"
    outbox = PersistenceOutbox("soc", outbox_path)
    outbox.record_failure(
        "decision-stale",
        "conservation",
        {"status_id": "c1", "domain": "soc", "stale_field": 1},
        "serialization succeeded",
    )

    class _StrictStore:
        def write_conservation_status(self, *, status_id, domain):
            raise AssertionError("unexpectedly replayed")

    assert outbox.drain(_StrictStore()) == (0, 1)
    with sqlite3.connect(outbox_path) as connection:
        row = connection.execute(
            "SELECT status FROM failed_artifacts WHERE decision_id = ?",
            ("decision-stale",),
        ).fetchone()
    assert row == ("abandoned",)


def test_outbox_does_not_abandon_on_runtime_error(tmp_path: Path) -> None:
    outbox = PersistenceOutbox("soc", tmp_path / "runtime.db")
    outbox.record_failure(
        "decision-runtime",
        "conservation",
        {"status_id": "c1", "domain": "soc"},
        "temporary failure",
    )

    class _FailingStore:
        def write_conservation_status(self, **payload):
            raise RuntimeError("timeout")

    assert outbox.drain(_FailingStore()) == (0, 1)
    with sqlite3.connect(outbox.db_path) as connection:
        row = connection.execute(
            "SELECT status FROM failed_artifacts WHERE decision_id = ?",
            ("decision-runtime",),
        ).fetchone()
    assert row == ("failed",)

    store = _ReplayStore()
    assert outbox.drain(store) == (1, 0)


def test_outbox_schema_version_stamped(tmp_path: Path) -> None:
    outbox_path = tmp_path / "schema-version.db"
    outbox = PersistenceOutbox("soc", outbox_path)
    outbox.record_failure("decision-schema", "conservation", {"V": 1}, "offline")

    with sqlite3.connect(outbox_path) as connection:
        row = connection.execute(
            "SELECT schema_version FROM failed_artifacts WHERE decision_id = ?",
            ("decision-schema",),
        ).fetchone()
    assert row == (CURRENT_PAYLOAD_SCHEMA,)


def test_outbox_serializes_datetime_payload(tmp_path: Path) -> None:
    outbox = PersistenceOutbox("soc", tmp_path / "datetime.db")
    outbox.record_failure(
        "decision-datetime",
        "conservation",
        {
            "status_id": "c1",
            "domain": "soc",
            "verified_at": datetime.now(timezone.utc),
        },
        "offline",
    )

    assert outbox.pending_count() == 1


def test_outbox_serializes_decimal_payload(tmp_path: Path) -> None:
    outbox = PersistenceOutbox("soc", tmp_path / "decimal.db")
    outbox.record_failure(
        "decision-decimal",
        "conservation",
        {"status_id": "c1", "domain": "soc", "alpha": Decimal("0.95")},
        "offline",
    )

    assert outbox.pending_count() == 1


def test_outbox_rejects_unserializable_payload(tmp_path: Path) -> None:
    outbox = PersistenceOutbox("soc", tmp_path / "unserializable.db")

    with pytest.raises(TypeError):
        outbox.record_failure(
            "decision-bad",
            "conservation",
            {"bad": object()},
            "offline",
        )

    assert outbox.pending_count() == 0


def test_outbox_deduplicates_pending_artifact(tmp_path: Path) -> None:
    outbox = PersistenceOutbox("soc", tmp_path / "outbox.db")
    outbox.record_failure("decision-3", "conservation", {"V": 1}, "first")
    outbox.record_failure("decision-3", "conservation", {"V": 2}, "second")

    assert outbox.pending_count() == 1
    store = _ReplayStore()
    assert outbox.drain(store) == (1, 0)
    assert store.calls[0][1]["V"] == 2


def test_outbox_replays_decision_before_conservation(tmp_path: Path) -> None:
    outbox = PersistenceOutbox("soc", tmp_path / "ordering.db")
    outbox.record_failure(
        "d-3",
        "conservation",
        {"status_id": "c3", "domain": "soc"},
        "offline",
    )
    outbox.record_failure(
        "d-3",
        "decision",
        {"domain": "soc", "category": "quality", "action": "review", "confidence": 0.8, "factors": {}},
        "offline",
    )

    store = _ReplayStore()
    assert outbox.drain(store) == (2, 0)
    order = [artifact_type for artifact_type, _ in store.calls]
    assert order.index("decision") < order.index("conservation")


def test_outbox_replays_evidence_before_fingerprint(tmp_path: Path) -> None:
    outbox = PersistenceOutbox("soc", tmp_path / "ordering.db")
    outbox.record_failure(
        "d-4",
        "fingerprint",
        {"fingerprint_id": "f4", "domain": "soc"},
        "offline",
    )
    outbox.record_failure(
        "d-4",
        "evidence_receipt",
        {"receipt_intent_id": "r4", "domain": "soc"},
        "offline",
    )

    store = _ReplayStore()
    assert outbox.drain(store) == (2, 0)
    order = [artifact_type for artifact_type, _ in store.calls]
    assert order.index("evidence_receipt") < order.index("fingerprint")


def test_outbox_evolution_replays_before_conservation(tmp_path: Path) -> None:
    outbox = PersistenceOutbox("soc", tmp_path / "ordering.db")
    outbox.record_failure(
        "d-5",
        "conservation",
        {"status_id": "c5", "domain": "soc"},
        "offline",
    )
    outbox.record_failure(
        "d-5",
        "evolution",
        {"event_id": "e5", "domain": "soc"},
        "offline",
    )

    store = _ReplayStore()
    assert outbox.drain(store) == (2, 0)
    order = [artifact_type for artifact_type, _ in store.calls]
    assert order.index("evolution") < order.index("conservation")


def test_outbox_count_and_export_abandoned(tmp_path: Path) -> None:
    outbox = PersistenceOutbox("soc", tmp_path / "abandoned.db")
    expected = {"status_id": "c1", "domain": "soc"}
    outbox.record_failure("decision-abandoned", "conservation", expected, "offline")

    class _FailingStore:
        def write_conservation_status(self, **payload):
            raise RuntimeError("still unavailable")

    for _ in range(PersistenceOutbox.MAX_RETRIES):
        outbox.drain(_FailingStore())

    assert outbox.count_abandoned() == 1
    exported = outbox.export_abandoned()
    assert exported == [
        {
            "decision_id": "decision-abandoned",
            "artifact_type": "conservation",
            "payload": expected,
            "error": "still unavailable",
            "retry_count": PersistenceOutbox.MAX_RETRIES,
        }
    ]


def test_outbox_count_abandoned_when_none(tmp_path: Path) -> None:
    outbox = PersistenceOutbox("soc", tmp_path / "empty.db")

    assert outbox.count_abandoned() == 0
    assert outbox.export_abandoned() == []


def test_outbox_abandoned_warning_logged(tmp_path: Path, caplog) -> None:
    outbox = PersistenceOutbox("soc", tmp_path / "warning.db")
    outbox.record_failure("decision-warning", "conservation", {"V": 1}, "offline")

    class _FailingStore:
        def write_conservation_status(self, **payload):
            raise RuntimeError("still unavailable")

    with caplog.at_level(logging.WARNING):
        for _ in range(PersistenceOutbox.MAX_RETRIES):
            outbox.drain(_FailingStore())

    assert "outbox abandoned artifact" in caplog.text
    assert "decision-warning" in caplog.text


def test_outbox_replay_covers_every_enqueued_artifact() -> None:
    source_root = Path(__file__).parents[2]
    outbox_source = (source_root / "copilot_sdk/scoring/persistence_outbox.py").read_text()
    scorer_source = (source_root / "copilot_sdk/scoring/scorer.py").read_text()
    ledger_source = (source_root / "copilot_sdk/evolution/ledger.py").read_text()
    replay_body = outbox_source.split("    def _replay(", 1)[1].split("    def clear(", 1)[0]
    replayable = set(re.findall(r'artifact_type == "([a-z_]+)"', replay_body))
    enqueued = {
        "decision",
        "conservation",
        "evidence_receipt",
        "fingerprint",
        "centroid_checkpoint",
        "evolution",
    }

    assert enqueued <= replayable
    assert "outcome" not in enqueued
    assert "outcome" not in replayable
    assert '"evidence_receipt"' in scorer_source
    assert '"fingerprint"' in scorer_source
    assert '"centroid_checkpoint"' in scorer_source
    assert '"evolution"' in ledger_source


def test_outcome_is_fail_closed_invariant() -> None:
    source_root = Path(__file__).parents[2]
    outbox_source = (source_root / "copilot_sdk/scoring/persistence_outbox.py").read_text()
    scorer_source = (source_root / "copilot_sdk/scoring/scorer.py").read_text()
    replay_body = outbox_source.split("    def _replay(", 1)[1].split("    def clear(", 1)[0]

    assert "outcome" not in replay_body
    assert not re.search(
        r"record_failure\([\s\S]{0,240}[\"']outcome[\"']",
        scorer_source,
    )


def test_replay_handles_all_declared_types(tmp_path: Path) -> None:
    payloads = {
        "conservation": {"status_id": "c1", "domain": "soc"},
        "fingerprint": {"fingerprint_id": "f1", "domain": "soc"},
        "evidence_receipt": {"receipt_intent_id": "r1", "domain": "soc"},
        "centroid_checkpoint": {"checkpoint_id": "k1", "domain": "soc"},
        "decision": {"domain": "soc", "category": "quality", "action": "review"},
        "evolution": {"event_id": "e1", "domain": "soc"},
    }
    outbox = PersistenceOutbox("soc", tmp_path / "all-types.db")
    for index, (artifact_type, payload) in enumerate(payloads.items()):
        outbox.record_failure(f"decision-{index}", artifact_type, payload, "offline")

    assert outbox.drain(_ReplayStore()) == (len(payloads), 0)


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
