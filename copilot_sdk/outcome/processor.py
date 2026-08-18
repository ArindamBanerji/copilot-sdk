"""Exactly-once verified-outcome processing and learning integration."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Callable

import numpy as np

from .ledger import OutcomeLedger
from .models import VerifiedOutcome


@dataclass(frozen=True)
class ProcessResult:
    processed: bool
    reason: str
    receipt_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "processed": self.processed,
            "reason": self.reason,
            "receipt_id": self.receipt_id,
        }


class OutcomeProcessor:
    """Validate receipts, apply learning once, and persist the audit receipt."""

    def __init__(
        self,
        ledger: OutcomeLedger,
        *,
        scorer: Any | None = None,
        conservation_updater: Callable[[VerifiedOutcome], Any] | None = None,
    ) -> None:
        self.ledger = ledger
        self.scorer = scorer
        self.conservation_updater = conservation_updater
        self._lock = threading.RLock()

    def process(self, outcome: VerifiedOutcome) -> ProcessResult:
        if not isinstance(outcome, VerifiedOutcome):
            raise TypeError("process requires a VerifiedOutcome")
        receipt_id = outcome.receipt_id()
        with self._lock:
            if self.ledger.exists(receipt_id):
                return ProcessResult(False, "already_processed", receipt_id)
            self._apply_learning(outcome)
            if self.conservation_updater is not None:
                self.conservation_updater(outcome)
            inserted = self.ledger.append(outcome)
            if not inserted:
                return ProcessResult(False, "already_processed", receipt_id)
            return ProcessResult(True, "processed", receipt_id)

    def process_batch(self, outcomes: list[VerifiedOutcome]) -> list[ProcessResult]:
        return [self.process(outcome) for outcome in outcomes]

    def get_receipt(self, receipt_id: str) -> VerifiedOutcome | None:
        return self.ledger.get(receipt_id)

    def count_verified(self, copilot: str, category: str | None = None) -> int:
        return self.ledger.count(copilot, category)

    def _apply_learning(self, outcome: VerifiedOutcome) -> None:
        if self.scorer is None:
            return
        learn = getattr(self.scorer, "learn", None)
        if callable(learn):
            actual_action = outcome.override_action if outcome.human_disposition == "override" else outcome.predicted_action
            learn(
                outcome.decision_id,
                actual_action,
                "confirmed" if outcome.correct else "overridden",
                context={"evidence_provenance": outcome.evidence_provenance, **(outcome.measured_impact or {})},
            )
            return
        update = getattr(self.scorer, "update", None)
        if not callable(update):
            raise TypeError("scorer must expose learn() or update()")
        actions = list(getattr(self.scorer, "actions", []))
        if outcome.predicted_action not in actions:
            raise ValueError(f"predicted action is not present in scorer actions: {outcome.predicted_action}")
        category_index = _category_index(self.scorer, outcome.category)
        action_index = actions.index(outcome.predicted_action)
        actual_action = outcome.override_action if outcome.human_disposition == "override" else outcome.predicted_action
        gt_action_index = None if actual_action not in actions else actions.index(actual_action)
        update(
            np.asarray(outcome.factor_vector, dtype=np.float64),
            category_index,
            action_index,
            outcome.correct,
            gt_action_index=gt_action_index,
        )


def _category_index(scorer: Any, category: str) -> int:
    categories = list(getattr(scorer, "categories", []) or [])
    if category in categories:
        return categories.index(category)
    try:
        return int(category)
    except (TypeError, ValueError) as error:
        raise ValueError(f"category is not present in scorer categories: {category}") from error

