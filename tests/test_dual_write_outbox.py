from __future__ import annotations

import sqlite3
from typing import Any

import pytest

from copilot_sdk.graph.dual_write_store import DualWriteStore
from copilot_sdk.graph.outbox import DurableOutbox


class RecordingEndpoint:  # MOCK-OK: protocol delegation boundary spy for durable replay.
    def __init__(self, *, failing_ids: set[str] | None = None) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []
        self.failing_ids = failing_ids or set()
        self.fail_operations: set[str] = set()

    def __getattr__(self, operation: str):
        def call(*args: object, **kwargs: object) -> None:
            self.calls.append((operation, args, kwargs))
            if operation in self.fail_operations:
                raise RuntimeError(f"secondary failed {operation}")
            if operation == "write_governed_decision" and str(args[0]) in self.failing_ids:
                raise RuntimeError(f"secondary failed {args[0]}")

        return call


def _governed_write(store: DualWriteStore, decision_id: str = "DEC-1") -> None:
    store.write_governed_decision(
        decision_id,
        "trading",
        "market",
        2,
        "buy",
        1,
        0.85,
        [0.15, 0.85],
        [1.0, 2.0],
        ["momentum", "volatility"],
        source="test",
        scorer_version="v1",
        preset_version="trading.v1",
        factor_schema_version="schema.v1",
        metadata={"trace_id": decision_id},
    )


def _store(tmp_path, secondary: RecordingEndpoint) -> tuple[DualWriteStore, RecordingEndpoint]:
    primary = RecordingEndpoint()
    return DualWriteStore(primary, secondary, outbox_path=str(tmp_path / "secondary_outbox.db")), primary


def _row_status(path, row_id: int) -> str:
    connection = sqlite3.connect(path)
    try:
        row = connection.execute("SELECT status FROM secondary_outbox WHERE id = ?", (row_id,)).fetchone()
        assert row is not None
        return str(row[0])
    finally:
        connection.close()


def test_append_failure_creates_pending_entry_with_full_payload(tmp_path):
    secondary = RecordingEndpoint()
    secondary.fail_operations.add("write_governed_decision")
    store, _ = _store(tmp_path, secondary)

    _governed_write(store, "DEC-1")

    assert store._durable_outbox is not None
    pending = store._durable_outbox.get_pending()
    assert len(pending) == 1
    assert pending[0]["operation"] == "write_governed_decision"
    assert pending[0]["domain"] == "trading"
    assert pending[0]["payload"]["args"][0:2] == ["DEC-1", "trading"]
    assert pending[0]["payload"]["kwargs"]["metadata"] == {"trace_id": "DEC-1"}


def test_replay_success_reuses_stored_governed_arguments(tmp_path):
    secondary = RecordingEndpoint()
    secondary.fail_operations.add("write_governed_decision")
    store, _ = _store(tmp_path, secondary)
    _governed_write(store, "DEC-2")
    secondary.fail_operations.clear()

    report = store.replay_outbox()

    assert (report.replayed, report.failed, report.remaining) == (1, 0, 0)
    assert store.outbox_empty() is True
    replay_call = secondary.calls[-1]
    assert replay_call[0] == "write_governed_decision"
    assert replay_call[1][0:2] == ("DEC-2", "trading")
    assert replay_call[2]["metadata"] == {"trace_id": "DEC-2"}


def test_replay_failure_marks_entry_failed(tmp_path):
    secondary = RecordingEndpoint()
    secondary.fail_operations.add("write_governed_decision")
    store, _ = _store(tmp_path, secondary)
    _governed_write(store, "DEC-3")
    assert store._durable_outbox is not None
    row_id = store._durable_outbox.get_pending()[0]["id"]

    report = store.replay_outbox()

    assert (report.replayed, report.failed, report.remaining) == (0, 1, 0)
    assert _row_status(tmp_path / "secondary_outbox.db", row_id) == "failed"


def test_multiple_entries_replay_independently(tmp_path):
    secondary = RecordingEndpoint(failing_ids={"DEC-1", "DEC-2", "DEC-3"})
    store, _ = _store(tmp_path, secondary)
    for decision_id in ("DEC-1", "DEC-2", "DEC-3"):
        _governed_write(store, decision_id)
    secondary.failing_ids = {"DEC-3"}

    report = store.replay_outbox()

    assert (report.replayed, report.failed, report.remaining) == (2, 1, 0)


def test_outbox_empty_without_failures(tmp_path):
    store, _ = _store(tmp_path, RecordingEndpoint())

    assert store.outbox_empty() is True


def test_outbox_empty_after_replay(tmp_path):
    secondary = RecordingEndpoint()
    secondary.fail_operations.add("write_governed_decision")
    store, _ = _store(tmp_path, secondary)
    _governed_write(store)
    assert store.outbox_empty() is False

    secondary.fail_operations.clear()
    store.replay_outbox()

    assert store.outbox_empty() is True


def test_outcome_payload_contains_every_replay_argument(tmp_path):
    secondary = RecordingEndpoint()
    secondary.fail_operations.add("write_outcome")
    store, _ = _store(tmp_path, secondary)

    store.write_outcome(
        "DEC-4",
        "buy",
        True,
        metadata={"verified_at": 123.0, "reason": "test"},
        domain="trading",
    )

    assert store._durable_outbox is not None
    payload = store._durable_outbox.get_pending()[0]["payload"]
    assert payload["args"] == ["DEC-4", "buy", True]
    assert payload["kwargs"] == {
        "metadata": {"verified_at": 123.0, "reason": "test"},
        "domain": "trading",
    }


def test_purge_removes_replayed_entries(tmp_path):
    outbox = DurableOutbox(str(tmp_path / "outbox.db"))
    for index in range(3):
        row_id = outbox.append("write_outcome", "trading", {"args": [f"d{index}"], "kwargs": {}}, "down")
        outbox.mark_replayed(row_id)

    assert outbox.purge_replayed(before=float("inf")) == 3
    assert outbox.pending_count() == 0
    outbox.close()


def test_outbox_persists_across_reopen(tmp_path):
    path = tmp_path / "outbox.db"
    outbox = DurableOutbox(str(path))
    outbox.append("write_outcome", "trading", {"args": ["DEC-5"], "kwargs": {}}, "down")
    outbox.close()

    restored = DurableOutbox(str(path))
    assert restored.pending_count() == 1
    assert restored.get_pending()[0]["payload"]["args"] == ["DEC-5"]
    restored.close()


def test_without_outbox_path_failures_remain_in_memory_only():
    secondary = RecordingEndpoint()
    secondary.fail_operations.add("write_governed_decision")
    store = DualWriteStore(RecordingEndpoint(), secondary)
    _governed_write(store)

    assert store.secondary_failure_count == 1
    with pytest.raises(RuntimeError, match="durable outbox is not configured"):
        store.replay_outbox()
