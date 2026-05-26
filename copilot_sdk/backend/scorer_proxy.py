"""Cached scorer proxy for app backends.

Each proxy lazily constructs one scorer against its shared graph store and
serializes access through a reentrant lock.
"""

from __future__ import annotations

from pathlib import Path
import threading
from typing import Any, Callable

from copilot_sdk.scoring import CompoundingScorer


class FreshScorerProxy:
    def __init__(
        self,
        preset_name: str,
        db_path: str | Path,
        graph_store_factory: Callable[[str | Path], Any],
    ) -> None:
        self._preset_name = preset_name
        self._db_path = str(db_path)
        self.graph_store = graph_store_factory(db_path)
        self._lock = threading.RLock()
        self._scorer_instance: CompoundingScorer | None = None

    def _scorer(self) -> CompoundingScorer:
        with self._lock:
            if self._scorer_instance is None:
                self._scorer_instance = CompoundingScorer.from_preset(
                    self._preset_name,
                    graph_store=self.graph_store,
                )
            return self._scorer_instance

    def score(
        self,
        factors: dict[str, float],
        category: str,
        metadata: dict[str, Any] | None = None,
    ):
        with self._lock:
            scorer = self._scorer()
            try:
                return scorer.score(factors, category, metadata=metadata)
            finally:
                self._close_scorer_store(scorer)

    def learn(self, decision_id: str, actual_action: str, outcome: str = "confirmed"):
        with self._lock:
            scorer = self._scorer()
            try:
                return scorer.learn(decision_id, actual_action, outcome)
            finally:
                self._close_scorer_store(scorer)

    def fingerprint(self):
        with self._lock:
            scorer = self._scorer()
            try:
                return scorer.fingerprint()
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

    @staticmethod
    def _close_scorer_store(scorer: CompoundingScorer) -> None:
        # Scorers borrow the proxy-owned graph store; the proxy controls its lifecycle.
        return None
