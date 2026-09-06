"""Share overlapping reads without retaining data after the read completes."""

from __future__ import annotations

import threading
from concurrent.futures import Future
from copy import deepcopy
from typing import Any, Callable, Hashable, TypeVar, cast

T = TypeVar("T")


class CoalescedRead:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pending: dict[Hashable, Future[Any]] = {}

    def run(self, key: Hashable, load: Callable[[], T]) -> T:
        with self._lock:
            pending = self._pending.get(key)
            leader = pending is None
            if pending is None:
                pending = Future()
                self._pending[key] = pending
        if leader:
            try:
                pending.set_result(load())
            except BaseException as error:
                pending.set_exception(error)
            finally:
                with self._lock:
                    del self._pending[key]
        # Each caller owns its result. A completed read is never a cache hit.
        return cast(T, deepcopy(pending.result()))
