"""WP-0: formal conservation-state contract for evolution gating.

Providers are synchronous at promotion time.  Unknown, stale, or failed
reads are represented as UNKNOWN so the promotion gate fails closed.
"""

from __future__ import annotations

import inspect
import logging
import time
from datetime import datetime, timezone
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


def normalize_conservation_state(
    raw: Any,
    *,
    domain: str,
    source: str,
    observed_at: str | None = None,
) -> ConservationState:
    """Normalize provider output without changing its computed status."""
    payload = raw if isinstance(raw, dict) else {"status": raw}
    status = _status(payload.get("status") or payload.get("state"))
    state: ConservationState = {
        "status": status,
        "overallSafe": status == "GREEN",
        "domain": domain,
        "source": source,
        "observed_at": observed_at
        or str(payload.get("observed_at") or datetime.now(timezone.utc).isoformat()),
    }
    if "verified_count" in payload:
        state["verified_count"] = int(payload["verified_count"] or 0)
    if "correct_count" in payload:
        state["correct_count"] = int(payload["correct_count"] or 0)
    if "total_decisions" in payload:
        state["total_decisions"] = int(payload["total_decisions"] or 0)
    if "penalty_ratio" in payload:
        state["penalty_ratio"] = float(payload["penalty_ratio"] or 0.0)
    if "reason" in payload:
        state["reason"] = str(payload["reason"]) if payload["reason"] is not None else None
    return state


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
                return normalize_conservation_state(
                    "UNKNOWN", domain=self._domain, source="scorer"
                )
            state = normalize_conservation_state(
                raw, domain=self._domain, source="scorer"
            )
            state["verified_count"] = int(raw.get("verified_count") or 0)
            state["correct_count"] = int(raw.get("correct_count") or 0)
            return state
        except Exception as exc:
            logger.warning("[EVOLUTION] Conservation read failed: %s", exc)
            return normalize_conservation_state(
                {"status": "UNKNOWN", "reason": str(exc)},
                domain=self._domain,
                source="scorer",
            )

    def __call__(self) -> ConservationState:
        return self.get_state()


class CachedAsyncProvider:
    """Synchronous snapshot adapter for an async-origin conservation source."""

    def __init__(
        self,
        snapshot_fn: Any,
        freshness_ttl: float = 30.0,
        clock: Any = time.time,
    ) -> None:
        self._snapshot_fn = snapshot_fn
        self._ttl = float(freshness_ttl)
        self._clock = clock
        self._cached: ConservationState | None = None
        self._cached_at = 0.0

    def get_state(self) -> ConservationState:
        now = float(self._clock())
        if self._cached is not None and now - self._cached_at <= self._ttl:
            return self._cached
        try:
            raw = self._snapshot_fn()
            if inspect.isawaitable(raw):
                raw.close() if hasattr(raw, "close") else None
                raise RuntimeError("async snapshot requires a synchronous adapter")
            if not isinstance(raw, dict):
                raise TypeError("conservation snapshot must be a mapping")
            self._cached = normalize_conservation_state(
                raw,
                domain=str(raw.get("domain") or "unknown"),
                source=str(raw.get("source") or "learning_health_monitor"),
            )
            self._cached_at = now
            return self._cached
        except Exception as exc:
            logger.warning(
                "[EVOLUTION] domain conservation stale, returning UNKNOWN: %s", exc
            )
            return normalize_conservation_state(
                {"status": "UNKNOWN", "reason": "stale_or_error"},
                domain="unknown",
                source="learning_health_monitor",
            )

    def invalidate(self) -> None:
        """Discard the synchronous cache after an async source refreshes."""
        self._cached = None
        self._cached_at = 0.0

    def __call__(self) -> ConservationState:
        return self.get_state()
