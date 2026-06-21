from __future__ import annotations

import os
import threading
import time
from pathlib import Path

import pytest

from copilot_sdk.outbox import OutboxEvent, OutboxStore, OutboxWorker
from copilot_sdk.outbox.cli import process_command, status_command
from copilot_sdk.outbox.models import EVENT_TYPES


@pytest.fixture
def store(tmp_path: Path) -> OutboxStore:
    outbox = OutboxStore(tmp_path / "test_outbox.db")
    try:
        yield outbox
    finally:
        outbox.close()


def _append(store: OutboxStore, payload_id: str = "d1") -> int:
    return store.append("decision_created", "trading", {"decision_id": payload_id})


def test_append_event(store: OutboxStore) -> None:
    event_id = _append(store)

    assert event_id > 0
    assert store.count_total() == 1
    assert store.count_unprocessed() == 1


def test_append_validates_event_type(store: OutboxStore) -> None:
    with pytest.raises(ValueError, match="Unknown event_type"):
        store.append("unknown", "trading", {})


def test_event_types_include_expected_values() -> None:
    assert "decision_created" in EVENT_TYPES
    assert "promotion_event" in EVENT_TYPES


def test_get_unprocessed(store: OutboxStore) -> None:
    first = _append(store, "d1")
    second = _append(store, "d2")
    store.mark_processed(first)

    events = store.get_unprocessed()

    assert [event.event_id for event in events] == [second]
    assert events[0].payload == {"decision_id": "d2"}


def test_get_unprocessed_limit(store: OutboxStore) -> None:
    ids = [_append(store, str(index)) for index in range(3)]

    events = store.get_unprocessed(limit=2)

    assert [event.event_id for event in events] == ids[:2]


def test_mark_processed(store: OutboxStore) -> None:
    event_id = _append(store)

    store.mark_processed(event_id)

    assert store.get_unprocessed() == []
    assert store.count_unprocessed() == 0


def test_mark_dead_letter(store: OutboxStore) -> None:
    event_id = _append(store)

    store.mark_dead_letter(event_id, "boom")

    letters = store.get_dead_letters()
    assert len(letters) == 1
    assert letters[0].event_id == event_id
    assert letters[0].processed is True
    assert letters[0].error == "boom"


def test_get_dead_letters(store: OutboxStore) -> None:
    first = _append(store, "d1")
    second = _append(store, "d2")
    store.mark_dead_letter(first, "first")
    store.mark_dead_letter(second, "second")

    letters = store.get_dead_letters()

    assert [event.error for event in letters] == ["second", "first"]


def test_replay_from_offset(store: OutboxStore) -> None:
    first = _append(store, "d1")
    second = _append(store, "d2")
    third = _append(store, "d3")
    store.mark_processed(first)

    events = store.replay_from(second)

    assert [event.event_id for event in events] == [second, third]


def test_count_unprocessed(store: OutboxStore) -> None:
    first = _append(store, "d1")
    _append(store, "d2")
    store.mark_processed(first)

    assert store.count_unprocessed() == 1
    assert store.count_total() == 2


def test_separate_db(tmp_path: Path) -> None:
    graph_db = tmp_path / "graph.db"
    outbox_db = tmp_path / "graph_outbox.db"
    graph_db.write_text("", encoding="utf-8")

    store = OutboxStore(outbox_db)
    try:
        _append(store)
    finally:
        store.close()

    assert outbox_db.exists()
    assert os.path.abspath(outbox_db) != os.path.abspath(graph_db)


def test_process_batch_calls_handler(store: OutboxStore) -> None:
    event_id = _append(store)
    seen: list[OutboxEvent] = []
    worker = OutboxWorker(store)
    worker.register("decision_created", seen.append)

    processed = worker.process_batch()

    assert processed == 1
    assert [event.event_id for event in seen] == [event_id]
    assert store.count_unprocessed() == 0


def test_process_batch_empty(store: OutboxStore) -> None:
    assert OutboxWorker(store).process_batch() == 0


def test_process_batch_multiple_handlers(store: OutboxStore) -> None:
    _append(store)
    calls: list[str] = []
    worker = OutboxWorker(store)
    worker.register("decision_created", lambda event: calls.append(f"a-{event.event_id}"))
    worker.register("decision_created", lambda event: calls.append(f"b-{event.event_id}"))

    worker.process_batch()

    assert calls == ["a-1", "b-1"]


def test_failed_handler_dead_letters(store: OutboxStore) -> None:
    first = _append(store, "d1")
    second = _append(store, "d2")
    calls: list[int] = []
    worker = OutboxWorker(store)

    def handler(event: OutboxEvent) -> None:
        calls.append(event.event_id)
        if event.event_id == first:
            raise RuntimeError("failed")

    worker.register("decision_created", handler)

    assert worker.run_until_empty() == 2
    assert calls == [first, second]
    assert [event.event_id for event in store.get_dead_letters()] == [first]
    assert store.count_unprocessed() == 0


def test_no_handler_skips(store: OutboxStore) -> None:
    _append(store)

    assert OutboxWorker(store).process_batch() == 0
    assert store.count_unprocessed() == 1


def test_run_until_empty(store: OutboxStore) -> None:
    for index in range(5):
        _append(store, str(index))
    seen: list[int] = []
    worker = OutboxWorker(store, batch_size=2)
    worker.register("decision_created", lambda event: seen.append(event.event_id))

    processed = worker.run_until_empty()

    assert processed == 5
    assert seen == [1, 2, 3, 4, 5]


def test_stop_halts_processing(store: OutboxStore) -> None:
    for index in range(3):
        _append(store, str(index))
    worker = OutboxWorker(store)
    seen: list[int] = []

    def handler(event: OutboxEvent) -> None:
        seen.append(event.event_id)
        worker.stop()

    worker.register("decision_created", handler)

    assert worker.run_until_empty() == 1
    assert seen == [1]
    assert store.count_unprocessed() == 2


def test_replay_from_offset_worker(store: OutboxStore) -> None:
    _append(store, "d1")
    second = _append(store, "d2")
    _append(store, "d3")
    seen: list[int] = []
    worker = OutboxWorker(store)
    worker.register("decision_created", lambda event: seen.append(event.event_id))

    assert worker.replay(second) == 2
    assert seen == [2, 3]


def test_replay_idempotent(store: OutboxStore) -> None:
    _append(store)
    calls: list[int] = []
    worker = OutboxWorker(store)
    worker.register("decision_created", lambda event: calls.append(event.event_id))

    assert worker.replay(0) == 1
    assert worker.replay(0) == 1
    assert calls == [1, 1]


def test_replay_failed_handler_continues(store: OutboxStore) -> None:
    _append(store, "d1")
    _append(store, "d2")
    calls: list[int] = []
    worker = OutboxWorker(store)

    def handler(event: OutboxEvent) -> None:
        calls.append(event.event_id)
        if event.event_id == 1:
            raise RuntimeError("replay failed")

    worker.register("decision_created", handler)

    assert worker.replay(0) == 2
    assert calls == [1, 2]
    assert store.count_unprocessed() == 2


def test_events_processed_oldest_first(store: OutboxStore) -> None:
    for payload_id in ("d1", "d2", "d3"):
        _append(store, payload_id)
    processed_order: list[str] = []
    worker = OutboxWorker(store)
    worker.register(
        "decision_created",
        lambda event: processed_order.append(str(event.payload["decision_id"])),
    )

    worker.run_until_empty()

    assert processed_order == ["d1", "d2", "d3"]


def test_concurrent_appends(tmp_path: Path) -> None:
    store = OutboxStore(tmp_path / "concurrent_outbox.db")
    try:
        errors: list[BaseException] = []

        def append(index: int) -> None:
            try:
                store.append("decision_created", "trading", {"decision_id": index})
            except BaseException as exc:
                errors.append(exc)

        threads = [threading.Thread(target=append, args=(index,)) for index in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        events = store.replay_from(0)
    finally:
        store.close()

    assert errors == []
    assert len(events) == 10
    assert len({event.event_id for event in events}) == 10


def test_large_batch_1000_events(tmp_path: Path) -> None:
    store = OutboxStore(tmp_path / "large_outbox.db")
    try:
        started = time.perf_counter()
        for index in range(1000):
            store.append("decision_created", "trading", {"decision_id": index})
        worker = OutboxWorker(store, batch_size=250)
        worker.register("decision_created", lambda event: None)

        processed = worker.run_until_empty()
        elapsed = time.perf_counter() - started
    finally:
        store.close()

    assert processed == 1000
    assert elapsed < 5.0


def test_cli_status(tmp_path: Path) -> None:
    db_path = tmp_path / "cli_status.db"
    store = OutboxStore(db_path)
    try:
        event_id = _append(store)
        store.mark_dead_letter(event_id, "bad")
        _append(store, "d2")
    finally:
        store.close()

    result = status_command("trading", str(db_path))

    assert result == {
        "domain": "trading",
        "total": 2,
        "pending": 1,
        "dead_letters": 1,
    }


def test_cli_process(tmp_path: Path) -> None:
    db_path = tmp_path / "cli_process.db"
    store = OutboxStore(db_path)
    try:
        _append(store)
        _append(store, "d2")
    finally:
        store.close()

    result = process_command("trading", str(db_path))

    assert result == {"domain": "trading", "processed": 0, "pending": 2}
