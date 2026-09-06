"""Serialize local demo initialization before each worker restores its runtime."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from copilot_sdk.process_lock import file_lock


@contextmanager
def startup_lock(db_path: str) -> Iterator[None]:
    """Protect the seed check and writes together for cooperating app workers."""
    if db_path == ":memory:":
        yield
    else:
        with file_lock(str(Path(db_path).resolve()) + ".startup.lock"):
            yield
