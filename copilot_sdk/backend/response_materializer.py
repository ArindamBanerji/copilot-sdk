"""Small app-scoped response materializer for read-only display endpoints."""

from __future__ import annotations

import copy
import threading
import time
from collections.abc import Callable, Mapping
from typing import Any


SharedInput = dict[str, Any]
Computation = Callable[[SharedInput], Any]


class ResponseMaterializer:
    """Precompute a bounded set of display responses from one graph snapshot."""

    def __init__(
        self,
        domain: str,
        store_provider: Callable[[], Any],
        computations: Mapping[str, Computation],
        ttl: float = 5.0,
    ) -> None:
        if ttl <= 0:
            raise ValueError("ttl must be positive")
        self._domain = domain
        self._store_provider = store_provider
        self._computations = dict(computations)
        self._materialized: dict[str, Any] = {}
        self._lock = threading.Condition(threading.RLock())
        self._last_refresh: float | None = None
        self._ttl = float(ttl)
        self._refreshing = False
        self._generation = 0
        self._failure: BaseException | None = None

    def refresh(self, *, if_stale: bool = False) -> None:
        """Fetch graph rows once, compute all registered responses, publish atomically."""
        with self._lock:
            if self._refreshing:
                self._lock.wait_for(lambda: not self._refreshing)
                if self._failure is not None:
                    raise RuntimeError("Response refresh failed") from self._failure
                return
            if if_stale and self._is_fresh():
                return
            self._refreshing = True
            self._failure = None
            generation = self._generation
        try:
            store = self._store_provider()
            decisions = list(store.get_all_decisions(self._domain))
            verified = list(store.get_verified_decisions(self._domain))
            shared: SharedInput = {
                "decisions": decisions,
                "verified": verified,
                "store": store,
                "domain": self._domain,
            }
            results: dict[str, Any] = {}
            for key, fn in self._computations.items():
                try:
                    results[key] = fn(shared)
                except Exception as exc:
                    results[key] = {"error": str(exc), "status": "unavailable"}
            with self._lock:
                if generation == self._generation:
                    self._materialized = results
                    self._last_refresh = time.monotonic()
        except BaseException as exc:
            with self._lock:
                self._failure = exc
            raise
        finally:
            with self._lock:
                self._refreshing = False
                self._lock.notify_all()

    def invalidate(self) -> None:
        """Discard published/in-flight responses without waiting for a rebuild."""
        with self._lock:
            self._generation += 1
            self._last_refresh = None
            self._materialized = {}

    def _is_fresh(self) -> bool:
        """Check freshness while holding the condition lock."""
        return self._last_refresh is not None and time.monotonic() - self._last_refresh < self._ttl

    def get(self, key: str) -> Any | None:
        """Read without blocking; retain prior data during refresh until invalidated."""
        with self._lock:
            if self._refreshing:
                result = self._materialized.get(key)
                return copy.deepcopy(result) if result is not None else None
            if not self._is_fresh():
                return None
            result = self._materialized.get(key)
            if result is None:
                return None
            return copy.deepcopy(result)

    def get_or_refresh(self, key: str) -> Any:
        """Join or build a fresh generation; return None under repeated invalidation."""
        if key not in self._computations:
            return None
        # Bound retries under continuous mutations, as in the S2P materializer.
        for _ in range(3):
            with self._lock:
                if self._is_fresh():
                    return copy.deepcopy(self._materialized.get(key))
            self.refresh(if_stale=True)
        with self._lock:
            return copy.deepcopy(self._materialized.get(key)) if self._is_fresh() else None
