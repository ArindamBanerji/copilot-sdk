"""In-memory GraphStore implementation for tests and demos."""

from __future__ import annotations

import time
import uuid
from copy import deepcopy
from typing import Any


class InMemoryGraphStore:
    """Dictionary-backed decision and outcome store."""

    def __init__(self) -> None:
        self._decisions: dict[str, dict[str, Any]] = {}
        self._outcomes: dict[str, dict[str, Any]] = {}
        self._sequence = 0

    def write_decision(
        self,
        entity_id: str,
        category: str,
        action: str,
        confidence: float,
        factors: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        self._sequence += 1
        decision_id = str((metadata or {}).get("decision_id") or uuid.uuid4().hex[:12])
        created_at = float((metadata or {}).get("created_at", time.time()))
        self._decisions[decision_id] = {
            "decision_id": decision_id,
            "entity_id": entity_id,
            "category": category,
            "recommended_action": action,
            "confidence": float(confidence),
            "factors": deepcopy(factors),
            "metadata": deepcopy(metadata or {}),
            "created_at": created_at,
            "_sequence": self._sequence,
        }
        return decision_id

    def write_outcome(
        self,
        decision_id: str,
        actual_action: str,
        is_correct: bool,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if decision_id not in self._decisions:
            raise KeyError(decision_id)
        self._outcomes[decision_id] = {
            "decision_id": decision_id,
            "actual_action": actual_action,
            "is_correct": bool(is_correct),
            "metadata": deepcopy(metadata or {}),
            "verified_at": float((metadata or {}).get("verified_at", time.time())),
        }

    def get_decision(self, decision_id: str) -> dict[str, Any] | None:
        decision = self._decisions.get(decision_id)
        return deepcopy(decision) if decision is not None else None

    def get_decisions(
        self,
        category: str | None = None,
        limit: int = 400,
    ) -> list[dict[str, Any]]:
        decisions = [
            decision
            for decision in self._ordered_decisions()
            if category is None or decision["category"] == category
        ]
        return deepcopy(decisions[: max(int(limit), 0)])

    def get_verified_decisions(self) -> list[dict[str, Any]]:
        verified = []
        for decision in self._ordered_decisions():
            outcome = self._outcomes.get(decision["decision_id"])
            if outcome is None:
                continue
            merged = dict(decision)
            merged.update({
                "actual_action": outcome["actual_action"],
                "is_correct": outcome["is_correct"],
                "verified_at": outcome["verified_at"],
                "outcome_metadata": deepcopy(outcome["metadata"]),
            })
            verified.append(merged)
        return deepcopy(verified)

    def count_verified(self) -> int:
        return len(self._outcomes)

    def count_correct(self) -> int:
        return sum(1 for outcome in self._outcomes.values() if outcome["is_correct"])

    def get_all_decisions(self) -> list[dict[str, Any]]:
        return self.get_decisions(category=None, limit=len(self._decisions))

    def reset(self) -> None:
        self._decisions.clear()
        self._outcomes.clear()
        self._sequence = 0

    def close(self) -> None:
        return None

    def _ordered_decisions(self) -> list[dict[str, Any]]:
        return sorted(
            self._decisions.values(),
            key=lambda decision: (decision["created_at"], decision["_sequence"], decision["decision_id"]),
        )
