"""WP-0: formal conservation-state contract for evolution gating.

Providers are synchronous at promotion time.  Unknown, stale, or failed
reads are represented as UNKNOWN so the promotion gate fails closed.
"""

from __future__ import annotations

import inspect
import logging
import time
from typing import Any, Literal, Protocol, TypedDict


logger = logging.getLogger(__name__)

ConservationStatus = Literal["GREEN", "AMBER", "RED", "CALIBRATING", "UNKNOWN"]


class ConservationState(TypedDict, total=False):
    status: ConservationStatus
    overallSafe: bool
    domain: str
    verified_count: int
    correct_count: int
    total_decisions: int
    penalty_ratio: float
    source: str
    observed_at: str
    reason: str | None


class ConservationStateProvider(Protocol):
    """Synchronous provider required by the evolution gate."""

    def get_state(self) -> ConservationState:
        """Return a current state; stale/error reads must be UNKNOWN."""
        ...

    def __call__(self) -> ConservationState:
        ...


def _status(value: Any) -> ConservationStatus:
    normalized = str(value or "UNKNOWN").strip().upper()
    if normalized in {"GREEN", "AMBER", "RED", "CALIBRATING", "UNKNOWN"}:
        return normalized  # type: ignore[return-value]
    return "UNKNOWN"


class ScorerBackedProvider:
    """Provider for SDK copilots backed by their live scorer/graph state."""

    def __init__(self, scorer: Any, domain: str) -> None:
        self._scorer = scorer
        self._domain = str(domain)

    def get_state(self) -> ConservationState:
        try:
            getter = getattr(self._scorer, "get_conservation_state", None)
            if getter is None:
                getter = getattr(self._scorer, "_evolution_conservation_state")
            raw = getter()
            if isinstance(raw, str):
                raw = {"status": raw}
            if not isinstance(raw, dict):
                return {"status": "UNKNOWN", "domain": self._domain, "source": "scorer"}
            return {
                "status": _status(raw.get("status") or raw.get("state")),
                "domain": self._domain,
                "verified_count": int(raw.get("verified_count") or 0),
                "correct_count": int(raw.get("correct_count") or 0),
                "source": "scorer",
                "observed_at": str(time.time()),
            }
        except Exception as exc:
            logger.warning("[EVOLUTION] Conservation read failed: %s", exc)
            return {
                "status": "UNKNOWN",
                "domain": self._domain,
                "source": "scorer",
                "observed_at": str(time.time()),
                "reason": str(exc),
            }

    def __call__(self) -> ConservationState:
        return self.get_state()


class CachedAsyncProvider:
    """Synchronous snapshot adapter for an async-origin conservation source."""

    def __init__(self, snapshot_fn: Any, freshness_ttl: float = 30.0) -> None:
        self._snapshot_fn = snapshot_fn
        self._ttl = float(freshness_ttl)
        self._cached: ConservationState | None = None
        self._cached_at = 0.0

    def get_state(self) -> ConservationState:
        now = time.time()
        if self._cached is not None and now - self._cached_at <= self._ttl:
            return self._cached
        try:
            raw = self._snapshot_fn()
            if inspect.isawaitable(raw):
                raw.close() if hasattr(raw, "close") else None
                raise RuntimeError("async snapshot requires a synchronous adapter")
            if not isinstance(raw, dict):
                raise TypeError("conservation snapshot must be a mapping")
            self._cached = {
                "status": _status(raw.get("status") or raw.get("state")),
                "source": "learning_health_monitor",
                "observed_at": str(time.time()),
            }
            self._cached_at = now
            return self._cached
        except Exception as exc:
            logger.warning(
                "[EVOLUTION] SOC conservation stale, returning UNKNOWN: %s", exc
            )
            return {"status": "UNKNOWN", "reason": "stale_or_error"}

    def __call__(self) -> ConservationState:
        return self.get_state()
