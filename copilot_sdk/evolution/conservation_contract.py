"""WP-0: formal conservation-state contract for evolution gating.

Providers are synchronous at promotion time.  Unknown, stale, or failed
reads are represented as UNKNOWN so the promotion gate fails closed.
"""

from __future__ import annotations

import inspect
import logging
import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal, Protocol, TypedDict, cast


logger = logging.getLogger(__name__)

ConservationStatus = Literal[
    "GREEN",
    "VERIFIED",
    "ACTIVE",
    "PRESEED",
    "COLD_START",
    "BOOTSTRAP",
    "AMBER",
    "RED",
    "CALIBRATING",
    "UNKNOWN",
    "CONSERVATION_UNAVAILABLE",
]

_LEARNING_AND_PROMOTION_SAFE = frozenset({"GREEN", "VERIFIED", "ACTIVE"})
_LEARNING_ONLY_SAFE = frozenset({"PRESEED", "COLD_START", "BOOTSTRAP"})
_AVAILABLE_UNSAFE = frozenset({"AMBER", "RED", "CALIBRATING"})
_UNAVAILABLE = frozenset({"UNKNOWN", "CONSERVATION_UNAVAILABLE"})
_RECOGNIZED = (
    _LEARNING_AND_PROMOTION_SAFE
    | _LEARNING_ONLY_SAFE
    | _AVAILABLE_UNSAFE
    | _UNAVAILABLE
)


@dataclass(frozen=True)
class ConservationSafety:
    """Immutable C-17 decision shared by governed mutation loops."""

    status: str
    available: bool
    learning_allowed: bool
    promotion_allowed: bool
    reason: str


def evaluate_conservation_safety(raw_state: object) -> ConservationSafety:
    """Return the canonical C-17 safety decision for a state snapshot.

    This function is side-effect-free and total for arbitrary input. Provider
    failures are converted to unavailable input at the transaction boundary.
    """

    if isinstance(raw_state, ConservationSafety):
        return raw_state

    try:
        explicit: object = raw_state
        if isinstance(raw_state, Mapping):
            explicit = None
            for key in ("status", "state", "phase"):
                if key in raw_state and raw_state.get(key) is not None:
                    explicit = raw_state.get(key)
                    break
            if explicit is None:
                compatibility: object | None = None
                if "overallSafe" in raw_state:
                    compatibility = raw_state.get("overallSafe")
                elif "overall_safe" in raw_state:
                    compatibility = raw_state.get("overall_safe")
                if compatibility is True:
                    explicit = "GREEN"
                elif compatibility is False:
                    explicit = "RED"

        if not isinstance(explicit, str) or not explicit.strip():
            return ConservationSafety(
                "UNKNOWN", False, False, False, "conservation_state_unavailable"
            )

        status = explicit.strip().upper()
        if status not in _RECOGNIZED:
            return ConservationSafety(
                "UNKNOWN", False, False, False, "conservation_state_malformed"
            )
        if status in _LEARNING_AND_PROMOTION_SAFE:
            return ConservationSafety(status, True, True, True, "conservation_safe")
        if status in _LEARNING_ONLY_SAFE:
            return ConservationSafety(
                status, True, True, False, "conservation_learning_only"
            )
        if status in _AVAILABLE_UNSAFE:
            return ConservationSafety(
                status, True, False, False, "conservation_unsafe"
            )
        return ConservationSafety(
            status, False, False, False, "conservation_state_unavailable"
        )
    except Exception:
        return ConservationSafety(
            "UNKNOWN", False, False, False, "conservation_state_malformed"
        )


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
    if normalized in _RECOGNIZED:
        return cast(ConservationStatus, normalized)
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
