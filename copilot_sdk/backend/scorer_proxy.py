"""Fresh scorer proxy for app backends.

Each request opens its own scorer so FastAPI worker threads do not share
SQLite handles.
"""

from __future__ import annotations

from pathlib import Path
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
        self.store = graph_store_factory(db_path)

    def _scorer(self) -> CompoundingScorer:
        return CompoundingScorer.from_preset(self._preset_name, db_path=self._db_path)

    def score(
        self,
        factors: dict[str, float],
        category: str,
        metadata: dict[str, Any] | None = None,
    ):
        scorer = self._scorer()
        try:
            return scorer.score(factors, category, metadata=metadata)
        finally:
            self._close_scorer_store(scorer)

    def learn(self, decision_id: str, actual_action: str, outcome: str = "confirmed"):
        scorer = self._scorer()
        try:
            return scorer.learn(decision_id, actual_action, outcome)
        finally:
            self._close_scorer_store(scorer)

    def fingerprint(self):
        scorer = self._scorer()
        try:
            return scorer.fingerprint()
        finally:
            self._close_scorer_store(scorer)

    def trajectory(self):
        scorer = self._scorer()
        try:
            return scorer.trajectory()
        finally:
            self._close_scorer_store(scorer)

    def get_phase(self):
        scorer = self._scorer()
        try:
            return scorer.get_phase()
        finally:
            self._close_scorer_store(scorer)

    def get_alpha(self):
        scorer = self._scorer()
        try:
            return scorer.get_alpha()
        finally:
            self._close_scorer_store(scorer)

    @staticmethod
    def _close_scorer_store(scorer: CompoundingScorer) -> None:
        store = getattr(scorer, "_store", None)
        close = getattr(store, "close", None)
        if callable(close):
            close()
