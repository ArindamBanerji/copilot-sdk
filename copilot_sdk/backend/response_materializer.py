"""Small app-scoped response materializer for read-only display endpoints."""

from __future__ import annotations

import copy
import logging
import threading
import time
from collections.abc import Callable, Mapping
from typing import Any

from fastapi.encoders import jsonable_encoder

from copilot_sdk.scoring.measurement_state import compute_measurement_state
from copilot_sdk.scoring.trajectory import compute_trajectory


SharedInput = dict[str, Any]
Computation = Callable[[SharedInput], Any]
log = logging.getLogger(__name__)


def conservation_state_from_shared(shared: SharedInput, preset: Any) -> dict[str, Any]:
    """Build conservation inputs from the generation's verified rows."""
    verified = [dict(row) for row in shared.get("verified", [])]
    return {
        "verified_decisions": verified,
        "verified_outcomes": verified,
        "verified_count": len(verified),
        "correct_count": sum(row.get("is_correct") is True for row in verified),
        "total_decisions": len(verified),
        "total_categories": int(preset.shape.n_categories),
        "penalty_ratio": float(preset.penalty_ratio),
        "w_short": int(preset.w_short),
        "m_rate": float(preset.m_rate),
    }


def trajectory_response_from_shared(
    shared: SharedInput, preset: Any
) -> dict[str, Any]:
    """Build the trajectory response from a generation's verified rows."""
    result = compute_trajectory(
        [],
        [dict(row) for row in shared.get("verified", [])],
        preset.shape,
    )
    encoded = jsonable_encoder(result)
    return dict(encoded) if isinstance(encoded, dict) else {}


def measurement_state_response_from_shared(
    shared: SharedInput, scorer: Any, preset: Any
) -> dict[str, Any]:
    """Build measurement state without another graph history read."""
    verified = [dict(row) for row in shared.get("verified", [])]
    trajectory = compute_trajectory([], verified, preset.shape)
    return compute_measurement_state(
        scorer,
        verified_decisions=verified,
        current_iks=trajectory.current_iks,
    ).to_dict()


class ResponseMaterializer:
    """Publish one bounded display generation from one graph snapshot."""

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
        self._condition = threading.Condition(threading.RLock())
        self._last_refresh: float | None = None
        self._ttl = float(ttl)
        self._refreshing = False
        self._generation = 0
        self._published_generation = 0
        self._failure: BaseException | None = None
        self._mutation_pending = False
        self._last_refresh_ms = 0.0
        self._last_refresh_query_count = 0
        self._fallback_count = 0

    @property
    def generation_id(self) -> int:
        """Return the last atomically published generation identifier."""
        with self._condition:
            return self._published_generation

    @property
    def ttl_seconds(self) -> float:
        """Return the configured generation lifetime."""
        return self._ttl

    def refresh(self, *, if_stale: bool = False) -> None:
        """Fetch graph rows once, compute every response, and publish atomically.

        The condition protects only generation bookkeeping. Store reads and
        computations intentionally run outside it so stale readers never wait
        on graph I/O.
        """
        with self._condition:
            if self._refreshing:
                if if_stale and self._materialized:
                    return
                self._condition.wait_for(lambda: not self._refreshing)
                if self._failure is not None and not self._materialized:
                    raise RuntimeError("Response refresh failed") from self._failure
                return
            if if_stale and self._is_fresh_locked():
                return
            self._refreshing = True
            self._failure = None
            requested_generation = self._generation + 1

        refresh_started = time.monotonic()
        query_count = 0
        try:
            store = self._store_provider()
            decisions = list(store.get_all_decisions(self._domain))
            query_count += 1
            verified = list(store.get_verified_decisions(self._domain))
            query_count += 1
            shared: SharedInput = {
                "decisions": decisions,
                "verified": verified,
                "store": store,
                "domain": self._domain,
            }
            results: dict[str, Any] = {}
            for key, computation in self._computations.items():
                results[key] = computation(shared)

            with self._condition:
                # A mutation that arrives during graph I/O advances the
                # generation and makes this snapshot ineligible for publish.
                if self._generation < requested_generation:
                    self._generation = requested_generation
                    self._published_generation = requested_generation
                    self._materialized = results
                    self._last_refresh = time.monotonic()
                    self._mutation_pending = False
                    self._last_refresh_ms = (
                        time.monotonic() - refresh_started
                    ) * 1000.0
                    self._last_refresh_query_count = query_count
        except BaseException as exc:
            with self._condition:
                self._failure = exc
            if not self._materialized:
                raise
        finally:
            with self._condition:
                self._refreshing = False
                self._condition.notify_all()

    def invalidate(self) -> None:
        """Mark the generation stale while retaining its last good payload."""
        with self._condition:
            self._generation += 1
            self._last_refresh = None

    def invalidate_mutation(self) -> None:
        """Discard pre-mutation data and require a fresh graph generation."""
        with self._condition:
            old_generation = self._generation
            self._generation += 1
            new_generation = self._generation
            self._last_refresh = None
            self._materialized = {}
            self._mutation_pending = True
            self._condition.notify_all()
        log.info(
            "[MATERIALIZER] Mutation invalidation. Generation %d→%d. "
            "mutation_pending=True.",
            old_generation,
            new_generation,
        )

    def record_fallback(self) -> None:
        """Record a display read that bypassed the materialized generation."""
        with self._condition:
            self._fallback_count += 1

    def status(self) -> dict[str, Any]:
        """Return bounded materializer diagnostics without graph I/O."""
        with self._condition:
            age_seconds = (
                0.0
                if self._last_refresh is None
                else max(0.0, time.monotonic() - self._last_refresh)
            )
            return {
                "generation": self._published_generation,
                "age_seconds": age_seconds,
                "mutation_pending": self._mutation_pending,
                "payload_keys": sorted(self._materialized),
                "last_refresh_ms": self._last_refresh_ms,
                "last_refresh_query_count": self._last_refresh_query_count,
                "fallback_count": self._fallback_count,
            }

    def _is_fresh_locked(self) -> bool:
        """Check freshness while holding the condition lock."""
        return (
            self._last_refresh is not None
            and time.monotonic() - self._last_refresh < self._ttl
        )

    def _copy_locked(self, key: str) -> Any | None:
        if key not in self._materialized:
            return None
        return copy.deepcopy(self._materialized[key])

    def get(self, key: str) -> Any | None:
        """Read without graph I/O; return stale data during a refresh."""
        with self._condition:
            if self._mutation_pending:
                return None
            if self._refreshing:
                log.debug(
                    "[MATERIALIZER] Serving stale generation %d while refreshing.",
                    self._published_generation,
                )
                return self._copy_locked(key)
            if not self._is_fresh_locked():
                return None
            return self._copy_locked(key)

    def get_or_refresh(self, key: str) -> Any | None:
        """Return a fresh generation, or stale data while another refresh runs."""
        if key not in self._computations:
            return None
        for _ in range(3):
            with self._condition:
                if self._mutation_pending and self._refreshing:
                    self._condition.wait_for(lambda: not self._refreshing)
                    continue
                if self._is_fresh_locked():
                    return self._copy_locked(key)
                if (
                    not self._mutation_pending
                    and self._refreshing
                    and key in self._materialized
                ):
                    log.debug(
                        "[MATERIALIZER] Serving stale generation %d while refreshing.",
                        self._published_generation,
                    )
                    return self._copy_locked(key)
            self.refresh(if_stale=True)
            with self._condition:
                if self._failure is not None and key in self._materialized:
                    return self._copy_locked(key)
        with self._condition:
            return self._copy_locked(key) if self._materialized else None
