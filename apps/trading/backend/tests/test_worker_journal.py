"""Exercise journal read/modify/write from independent spawned workers."""

from __future__ import annotations

import json
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from app.routers.journal import _locked_append

_barrier: Any = None


def _initialize(barrier: Any) -> None:
    global _barrier
    _barrier = barrier


def _append(args: tuple[str, int]) -> None:
    path, worker = args
    _barrier.wait(timeout=30)
    for index in range(20):
        _locked_append(Path(path), {"id": f"{worker}-{index}"})


def test_spawn_journal_preserves_both_workers_entries(tmp_path: Path) -> None:
    path = tmp_path / "journal.json"
    context = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(
        max_workers=2, mp_context=context,
        initializer=_initialize, initargs=(context.Barrier(2),),
    ) as pool:
        list(pool.map(_append, [(str(path), worker) for worker in range(2)]))
    rows = json.loads(path.read_text())
    assert len(rows) == 40
    assert len({row["id"] for row in rows}) == 40
