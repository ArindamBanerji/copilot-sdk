"""Use independent spawn processes and real stores to test worker mitigations."""

from __future__ import annotations

import multiprocessing
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Callable

from copilot_sdk.graph.sqlite_store import SQLiteGraphStore
from copilot_sdk.process_lock import file_lock
from copilot_sdk.scoring.persistence_outbox import PersistenceOutbox
from copilot_sdk.atomic_json import write_json_atomic
from copilot_sdk.demo.bundle import restore_bundle_if_empty
from copilot_sdk.demo.startup import startup_lock

_barrier: Any = None


def _initialize(barrier: Any) -> None:
    global _barrier
    _barrier = barrier


def _parallel(worker: Callable[[tuple[str, int]], Any], path: Path) -> list[Any]:
    context = multiprocessing.get_context("spawn")
    # Integration suites prepend other repositories with their own tests package.
    # Spawn must resolve this module from this repository when unpickling workers.
    original_path = sys.path[:]
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    try:
        with ProcessPoolExecutor(
            max_workers=2, mp_context=context,
            initializer=_initialize, initargs=(context.Barrier(2),),
        ) as pool:
            return list(pool.map(worker, [(str(path), index) for index in range(2)]))
    finally:
        sys.path[:] = original_path


def _write_decisions(args: tuple[str, int]) -> int:
    path, worker = args
    _barrier.wait(timeout=30)
    store = SQLiteGraphStore(path, domain="purchasing")
    try:
        for index in range(20):
            store.write_decision(
                "purchasing", "produce", "order_less", 0.8, {"demand": 0.2},
                metadata={"decision_id": f"worker-{worker}-{index}"},
            )
        return worker
    finally:
        store.close()


def test_spawn_workers_initialize_and_write_same_sqlite_database(tmp_path: Path) -> None:
    path = tmp_path / "decisions.db"
    assert sorted(_parallel(_write_decisions, path)) == [0, 1]
    store = SQLiteGraphStore(path, domain="purchasing")
    try:
        assert store.count_decisions("purchasing") == 40
        assert store.connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert store.connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        store.close()


def _drain(args: tuple[str, int]) -> tuple[int, int]:
    path, _ = args
    outbox = PersistenceOutbox("purchasing", Path(path))
    store = SQLiteGraphStore(path + ".target", domain="purchasing")
    try:
        _barrier.wait(timeout=30)
        succeeded, failed = outbox.drain(store)
        return int(succeeded), int(failed)
    finally:
        store.close()


def test_spawn_workers_claim_outbox_batch_once(tmp_path: Path) -> None:
    path = tmp_path / "outbox.db"
    outbox = PersistenceOutbox("purchasing", path)
    for index in range(30):
        outbox.record_failure(
            f"deferred-{index}", "decision",
            {"decision_id": f"deferred-{index}", "domain": "purchasing",
             "category": "produce", "action": "order_less", "confidence": 0.8,
             "factors": {"demand": 0.2}},
            "retry",
        )
    results = _parallel(_drain, path)
    assert sum(result[0] for result in results) == 30
    assert sum(result[1] for result in results) == 0
    assert outbox.pending_count() == 0
    store = SQLiteGraphStore(str(path) + ".target", domain="purchasing")
    try:
        assert store.count_decisions("purchasing") == 30
    finally:
        store.close()


def _increment(args: tuple[str, int]) -> None:
    path, _ = args
    target = Path(path)
    _barrier.wait(timeout=30)
    for _ in range(20):
        with file_lock(path + ".lock"):
            value = int(target.read_text())
            target.write_text(str(value + 1))


def test_spawn_file_lock_prevents_lost_updates(tmp_path: Path) -> None:
    path = tmp_path / "counter"
    path.write_text("0")
    _parallel(_increment, path)
    assert path.read_text() == "40"


def test_file_lock_released_after_exception(tmp_path: Path) -> None:
    path = tmp_path / "failure.lock"
    try:
        with file_lock(path):
            raise ValueError("abort mutation")
    except ValueError:
        pass
    with file_lock(path, timeout=0):
        assert path.exists()


def _restore_bundle(args: tuple[str, int]) -> bool:
    path, _ = args
    store = SQLiteGraphStore(path, domain="purchasing")
    try:
        _barrier.wait(timeout=30)
        with startup_lock(path):
            return bool(restore_bundle_if_empty(store, Path(path + ".json"), domain="purchasing"))
    finally:
        store.close()


def test_spawn_startup_restores_bundle_once(tmp_path: Path) -> None:
    path = tmp_path / "startup.db"
    write_json_atomic(Path(str(path) + ".json"), {
        "domain": "purchasing", "min_decisions_to_skip": 1,
        "decisions": [{"decision_id": "seed-1", "category": "produce",
                       "recommended_action": "order_less", "confidence": 0.8}],
        "centroid_checkpoints": [{"centroids": [[[0.5]]], "decisions_count": 1}],
    })
    assert sorted(_parallel(_restore_bundle, path)) == [False, True]
    store = SQLiteGraphStore(path, domain="purchasing")
    try:
        assert store.count_decisions("purchasing") == 1
        assert len(store.get_centroid_checkpoints("purchasing")) == 1
    finally:
        store.close()


def _publish_json(args: tuple[str, int]) -> None:
    path, worker = args
    target = Path(path)
    _barrier.wait(timeout=30)
    for index in range(20):
        if worker == 0:
            write_json_atomic(target, {"version": index, "body": "x" * 10000})
        else:
            payload = json.loads(target.read_text())
            assert len(payload["body"]) == 10000


def test_spawn_atomic_json_readers_never_see_partial_payload(tmp_path: Path) -> None:
    path = tmp_path / "snapshot.json"
    write_json_atomic(path, {"version": -1, "body": "x" * 10000})
    _parallel(_publish_json, path)
    assert json.loads(path.read_text())["version"] == 19
