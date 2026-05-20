"""In-memory GraphStore implementation for tests and demos."""

from __future__ import annotations

import time
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class InMemoryGraphStore:
    """Dictionary-backed decision and outcome store."""

    def __init__(self, decision_id_prefix: str = "") -> None:
        self._decision_id_prefix = str(decision_id_prefix or "")
        self._decisions: dict[str, dict[str, Any]] = {}
        self._outcomes: dict[str, dict[str, Any]] = {}
        self._edges: list[dict[str, Any]] = []
        self._centroid_checkpoints: list[dict[str, Any]] = []
        self._evolution_events: list[dict[str, Any]] = []
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
        if self._decision_id_prefix and not decision_id.startswith(self._decision_id_prefix):
            decision_id = f"{self._decision_id_prefix}{decision_id}"
        decision_metadata = deepcopy(metadata or {})
        if self._decision_id_prefix or "decision_id" in decision_metadata:
            decision_metadata["decision_id"] = decision_id
        created_at = float((metadata or {}).get("created_at", time.time()))
        self._decisions[decision_id] = {
            "decision_id": decision_id,
            "entity_id": entity_id,
            "category": category,
            "recommended_action": action,
            "confidence": float(confidence),
            "factors": deepcopy(factors),
            "metadata": decision_metadata,
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

    def save_centroids(
        self,
        decision_id: str,
        category: str,
        centroids: Any,
        metadata: dict[str, Any] | None = None,
        *,
        decision_time_start: str | None = None,
        decision_time_end: str | None = None,
        checkpoint_time: str | None = None,
    ) -> None:
        self._centroid_checkpoints.append(
            {
                "decision_id": decision_id,
                "category": category,
                "centroids": deepcopy(centroids),
                "metadata": deepcopy(metadata or {}),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "decision_time_start": decision_time_start,
                "decision_time_end": decision_time_end,
                "checkpoint_time": checkpoint_time or _utc_iso_now(),
            }
        )

    def get_centroid_checkpoints(
        self,
        limit: int = 50,
        *,
        checkpoint_time_start: str | None = None,
        checkpoint_time_end: str | None = None,
        decision_time_start: str | None = None,
        decision_time_end: str | None = None,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        limit_value = max(int(limit), 0)
        if limit_value == 0:
            return []
        checkpoints = [
            checkpoint
            for checkpoint in self._centroid_checkpoints
            if _matches_checkpoint_filters(
                checkpoint,
                checkpoint_time_start=checkpoint_time_start,
                checkpoint_time_end=checkpoint_time_end,
                decision_time_start=decision_time_start,
                decision_time_end=decision_time_end,
                category=category,
            )
        ]
        return deepcopy(checkpoints[-limit_value:])

    def save_evolution_event(
        self,
        event_type: str,
        rule_name: str,
        variant_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._evolution_events.append(
            {
                "event_type": event_type,
                "rule_name": rule_name,
                "variant_id": variant_id,
                "metadata": deepcopy(metadata or {}),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def link_decision_to_entity(
        self,
        decision_id: str,
        entity_id: str,
        edge_type: str = "DECIDED_ON",
    ) -> None:
        self._edges.append(
            {
                "decision_id": decision_id,
                "entity_id": entity_id,
                "edge_type": edge_type,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    def get_decision_links(self, decision_id: str | None = None) -> list[dict[str, Any]]:
        links = [
            edge
            for edge in self._edges
            if decision_id is None or edge["decision_id"] == decision_id
        ]
        return deepcopy(links)

    def reset(self) -> None:
        self._decisions.clear()
        self._outcomes.clear()
        self._edges.clear()
        self._centroid_checkpoints.clear()
        self._evolution_events.clear()
        self._sequence = 0

    def close(self) -> None:
        return None

    def _ordered_decisions(self) -> list[dict[str, Any]]:
        return sorted(
            self._decisions.values(),
            key=lambda decision: (decision["created_at"], decision["_sequence"], decision["decision_id"]),
        )


def _matches_checkpoint_filters(
    checkpoint: dict[str, Any],
    *,
    checkpoint_time_start: str | None,
    checkpoint_time_end: str | None,
    decision_time_start: str | None,
    decision_time_end: str | None,
    category: str | None,
) -> bool:
    if category is not None and checkpoint.get("category") != category:
        return False
    checkpoint_time = checkpoint.get("checkpoint_time")
    if checkpoint_time_start is not None:
        if checkpoint_time is None or checkpoint_time < checkpoint_time_start:
            return False
    if checkpoint_time_end is not None:
        if checkpoint_time is None or checkpoint_time > checkpoint_time_end:
            return False
    stored_decision_start = checkpoint.get("decision_time_start")
    if decision_time_start is not None:
        if stored_decision_start is None or stored_decision_start < decision_time_start:
            return False
    stored_decision_end = checkpoint.get("decision_time_end")
    if decision_time_end is not None:
        if stored_decision_end is None or stored_decision_end > decision_time_end:
            return False
    return True
