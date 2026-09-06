"""Advisory locks for cooperating processes on one host and local filesystem."""

from __future__ import annotations

import errno
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def file_lock(path: str | Path, *, timeout: float = 120.0) -> Iterator[None]:
    """Hold an OS lock; process exit releases it without deleting the lock file.

    All participants must use the same path. This is deliberately non-reentrant;
    callers must hold it around the whole read/modify/write operation.
    """
    lock_path = Path(path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout
    with lock_path.open("a+b") as handle:
        if sys.platform == "win32":
            import msvcrt

            # Lock byte zero, including for a newly created empty file.
            def acquire() -> None:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)

            def release() -> None:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            def acquire() -> None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

            def release() -> None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

        while True:
            try:
                acquire()
                break
            except OSError as exc:
                if exc.errno not in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                    raise
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"Timed out acquiring {lock_path}") from exc
                time.sleep(0.025)
        try:
            yield
        finally:
            release()
