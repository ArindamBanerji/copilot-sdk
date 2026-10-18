"""Cached scorer proxy for app backends.

Each proxy lazily constructs one scorer against its shared graph store and
serializes access through a reentrant lock.
"""

from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
import inspect
import threading
from typing import Any, Callable

from copilot_sdk.scoring import CompoundingScorer
from copilot_sdk.scoring.scorer import PreparedScore


class StalePreparedScoreError(RuntimeError):
    """Prediction snapshot changed before its durable commit."""


@dataclass(frozen=True)
class _PreparedProxyScore:
    prepared: PreparedScore
    epoch: int


class FreshScorerProxy:
    def __init__(
        self,
        preset_name: str,
        db_path: str | Path,
        graph_store_factory: Callable[[str | Path], Any],
        profile: str = "production",
    ) -> None:
        self._preset_name = preset_name
        self.graph_store = graph_store_factory(db_path)
        self._profile = profile
        self._lock = threading.RLock()
        self._scorer_instance: CompoundingScorer | None = None
        self._mutation_epoch = 0

    def _scorer(self) -> CompoundingScorer:
        with self._lock:
            if self._scorer_instance is None:
                self._scorer_instance = CompoundingScorer.from_preset(
                    self._preset_name,
                    graph_store=self.graph_store,
                    evolve=True,
                    consolidation_enabled=True,
                    profile=self._profile,
                )
            return self._scorer_instance

    def score(
        self,
        factors: dict[str, float],
        category: str,
        metadata: dict[str, Any] | None = None,
    ):
        scorer = self._scorer()
        if not callable(getattr(scorer, "prepare_score", None)):
            with self._lock:
                return scorer.score(factors, category, metadata=metadata)
        return self.persist_prepared_score(self.prepare_score(factors, category, metadata=metadata))

    def prepare_score(
        self,
        factors: dict[str, float],
        category: str,
        metadata: dict[str, Any] | None = None,
    ) -> _PreparedProxyScore:
        """Predict under the scorer lock without performing durable I/O."""
        with self._lock:
            scorer = self._scorer()
            return _PreparedProxyScore(
                prepared=scorer.prepare_score(factors, category, metadata=metadata),
                epoch=self._mutation_epoch,
            )

    def persist_prepared_score(self, prepared: _PreparedProxyScore):
        """Persist a prepared prediction after releasing the scorer lock."""
        with self._lock:
            if prepared.epoch != self._mutation_epoch:
                raise StalePreparedScoreError("scorer changed after prediction")
            scorer = self._scorer()
        try:
            return scorer.persist_prepared_score(prepared.prepared)
        finally:
            self._close_scorer_store(scorer)

    def learn(
        self,
        decision_id: str,
        actual_action: str,
        outcome: str = "confirmed",
        *,
        consolidate: bool = False,
        context: dict[str, Any] | None = None,
    ):
        with self._lock:
            scorer = self._scorer()
            try:
                result = scorer.learn(
                    decision_id,
                    actual_action,
                    outcome,
                    consolidate=consolidate,
                    context=context,
                )
                self._mutation_epoch += 1
                return result
            finally:
                self._close_scorer_store(scorer)

    def score_read_only(self, factors: dict[str, float], category: str):
        with self._lock:
            scorer = self._scorer()
            try:
                return scorer.score_read_only(factors, category)
            finally:
                self._close_scorer_store(scorer)

    def fingerprint(self, *, persist: bool = False):
        with self._lock:
            scorer = self._scorer()
            try:
                fingerprint = scorer.fingerprint
                if "persist" in inspect.signature(fingerprint).parameters:
                    return fingerprint(persist=persist)
                return fingerprint()
            finally:
                self._close_scorer_store(scorer)

    def trajectory(self):
        with self._lock:
            scorer = self._scorer()
            try:
                return scorer.trajectory()
            finally:
                self._close_scorer_store(scorer)

    def get_phase(self):
        with self._lock:
            scorer = self._scorer()
            try:
                return scorer.get_phase()
            finally:
                self._close_scorer_store(scorer)

    def get_alpha(self):
        with self._lock:
            scorer = self._scorer()
            try:
                return scorer.get_alpha()
            finally:
                self._close_scorer_store(scorer)

    def get_dk_weights(self):
        with self._lock:
            scorer = self._scorer()
            try:
                return scorer.get_dk_weights()
            finally:
                self._close_scorer_store(scorer)

    def get_verified_count(self) -> int:
        with self._lock:
            scorer = self._scorer()
            try:
                return scorer.get_verified_count()
            finally:
                self._close_scorer_store(scorer)

    def get_conservation_state(self) -> dict[str, Any]:
        """Return the scorer-backed conservation state for evolution gates."""

        with self._lock:
            return dict(self._scorer()._evolution_conservation_state() or {"status": "UNKNOWN"})

    def get_category_phase(self, category: str):
        with self._lock:
            scorer = self._scorer()
            try:
                return scorer.get_category_phase(category)
            finally:
                self._close_scorer_store(scorer)

    def get_centroid(self, category: str, action: str):
        with self._lock:
            scorer = self._scorer()
            try:
                return scorer.get_centroid(category, action)
            finally:
                self._close_scorer_store(scorer)

    def reestimate_dk_if_due(self):
        with self._lock:
            scorer = self._scorer()
            try:
                return scorer.reestimate_dk_if_due()
            finally:
                self._close_scorer_store(scorer)

    @staticmethod
    def _close_scorer_store(scorer: CompoundingScorer) -> None:
        # Scorers borrow the proxy-owned graph store; the proxy controls its lifecycle.
        return None
