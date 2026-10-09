"""Fresh graph-backed response computation for read-only display endpoints."""

from __future__ import annotations

import copy
from collections.abc import Callable, Mapping
from typing import Any


SharedInput = dict[str, Any]
Computation = Callable[[SharedInput], Any]


class ResponseMaterializer:
    """Compatibility facade that never retains graph-derived responses."""

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

    def _compute(self, key: str) -> Any | None:
        computation = self._computations.get(key)
        if computation is None:
            return None
        store = self._store_provider()
        shared: SharedInput = {
            "decisions": list(store.get_all_decisions(self._domain)),
            "verified": list(store.get_verified_decisions(self._domain)),
            "store": store,
            "domain": self._domain,
        }
        return copy.deepcopy(computation(shared))

    def refresh(self, *, if_stale: bool = False) -> None:
        """Compatibility no-op; each read computes from the current graph."""

    def invalidate(self) -> None:
        """Compatibility no-op; no response survives its request."""

    def get(self, key: str) -> Any | None:
        """Compute a response from a fresh graph snapshot."""
        return self._compute(key)

    def get_or_refresh(self, key: str) -> Any | None:
        """Compute a response from a fresh graph snapshot."""
        return self._compute(key)
