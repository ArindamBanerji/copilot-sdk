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
    """Dictionary-backed domain-aware decision and outcome store."""

    def __init__(self, domain: str = "test", decision_id_prefix: str = "") -> None:
        self.domain = str(domain)
        self._decision_id_prefix = str(decision_id_prefix or "")
        self._decisions: dict[str, dict[str, Any]] = {}
        self._outcomes: dict[str, dict[str, Any]] = {}
        self._edges: list[dict[str, Any]] = []
        self._centroid_checkpoints: list[dict[str, Any]] = []
        self._evolution_events: list[dict[str, Any]] = []
        self._archive: list[dict[str, Any]] = []
        self._sequence = 0

    def write_decision(
        self,
        domain: str,
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
        entity_id = str(decision_metadata.get("entity_id") or decision_id)
        if "entity_id" not in decision_metadata:
            decision_metadata["entity_id"] = entity_id
        created_at = float((metadata or {}).get("created_at", time.time()))
        category_index = int((metadata or {}).get("category_index", 0))
        recommended_index = int((metadata or {}).get("recommended_index", 0))
        factor_vector = deepcopy((metadata or {}).get("factor_vector"))
        if factor_vector is None:
            factor_vector = [float(factors[name]) for name in factors]
        probabilities = deepcopy((metadata or {}).get("probabilities"))
        if probabilities is None:
            probabilities = [float(confidence)]
        self._decisions[decision_id] = {
            "decision_id": decision_id,
            "domain": str(domain),
            "entity_id": entity_id,
            "category": category,
            "category_index": category_index,
            "recommended_action": action,
            "recommended_index": recommended_index,
            "confidence": float(confidence),
            "factors": deepcopy(factors),
            "factor_vector": factor_vector,
            "probabilities": probabilities,
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
        meta = metadata or {}
        self._outcomes[decision_id] = {
            "decision_id": decision_id,
            "domain": self._decisions[decision_id].get("domain", self.domain),
            "actual_action": actual_action,
            "actual_index": int(meta.get("actual_index", 0)),
            "is_correct": bool(is_correct),
            "metadata": deepcopy(meta),
            "context": deepcopy(meta.get("context", {})),
            "verified_at": float(meta.get("verified_at", time.time())),
        }

    def get_decision(self, decision_id: str) -> dict[str, Any] | None:
        decision = self._decisions.get(decision_id)
        return deepcopy(decision) if decision is not None else None

    def get_decisions(
        self,
        domain: str,
        category: str | None = None,
        limit: int = 400,
    ) -> list[dict[str, Any]]:
        decisions = [
            decision
            for decision in self._ordered_decisions()
            if decision.get("domain") == domain
            and (category is None or decision["category"] == category)
        ]
        return deepcopy(decisions[: max(int(limit), 0)])

    def get_all_decisions(self, domain: str) -> list[dict[str, Any]]:
        return self.get_decisions(domain, category=None, limit=len(self._decisions))

    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]:
        verified = []
        for decision in self._ordered_decisions():
            if decision.get("domain") != domain:
                continue
            outcome = self._outcomes.get(decision["decision_id"])
            if outcome is None:
                continue
            merged = dict(decision)
            merged.update({
                "actual_action": outcome["actual_action"],
                "actual_index": outcome["actual_index"],
                "is_correct": outcome["is_correct"],
                "verified_at": outcome["verified_at"],
                "context": deepcopy(outcome["context"]),
                "outcome_metadata": deepcopy(outcome["metadata"]),
            })
            verified.append(merged)
        return deepcopy(verified)

    def count_verified(self, domain: str) -> int:
        return len(self.get_verified_decisions(domain))

    def count_correct(self, domain: str) -> int:
        return sum(
            1
            for outcome in self._outcomes.values()
            if outcome.get("domain") == domain and outcome["is_correct"]
        )

    def count_decisions(self, domain: str) -> int:
        return sum(1 for decision in self._decisions.values() if decision.get("domain") == domain)

    def save_centroids(
        self,
        domain: str,
        category: str,
        centroids: Any,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self._centroid_checkpoints.append(
            {
                "domain": str(domain),
                "decision_id": kwargs.get("decision_id"),
                "category": category,
                "centroids": deepcopy(centroids),
                "decisions_count": self.count_decisions(str(domain)),
                "iks": float((metadata or {}).get("iks", 0.0)),
                "metadata": deepcopy(metadata or {}),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "decision_time_start": kwargs.get("decision_time_start"),
                "decision_time_end": kwargs.get("decision_time_end"),
                "checkpoint_time": kwargs.get("checkpoint_time") or _utc_iso_now(),
            }
        )

    def load_latest_centroids(self, domain: str) -> Any | None:
        checkpoints = [
            checkpoint
            for checkpoint in self._centroid_checkpoints
            if checkpoint.get("domain") == domain
        ]
        if not checkpoints:
            return None
        return deepcopy(checkpoints[-1]["centroids"])

    def get_centroid_checkpoints(
        self,
        domain: str,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        limit_value = kwargs.get("limit", 50)
        checkpoints = [
            checkpoint
            for checkpoint in self._centroid_checkpoints
            if checkpoint.get("domain") == domain
            and _matches_checkpoint_filters(
                checkpoint,
                checkpoint_time_start=kwargs.get("checkpoint_time_start"),
                checkpoint_time_end=kwargs.get("checkpoint_time_end"),
                decision_time_start=kwargs.get("decision_time_start"),
                decision_time_end=kwargs.get("decision_time_end"),
                category=kwargs.get("category"),
            )
        ]
        if limit_value is None:
            return deepcopy(checkpoints)
        limit_value = max(int(limit_value), 0)
        if limit_value == 0:
            return []
        return deepcopy(checkpoints[-limit_value:])

    def save_evolution_event(
        self,
        domain: str,
        event_type: str,
        rule_name: str = "",
        variant_id: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._evolution_events.append(
            {
                "domain": str(domain),
                "event_type": event_type,
                "rule_name": rule_name,
                "variant_id": variant_id,
                "metadata": deepcopy(metadata or {}),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def get_evolution_events(self, domain: str, **kwargs: Any) -> list[dict[str, Any]]:
        rule_name = kwargs.get("rule_name")
        limit = max(int(kwargs.get("limit", 100)), 0)
        events = [
            event
            for event in self._evolution_events
            if event.get("domain") == domain
            and (rule_name is None or event.get("rule_name") == rule_name)
        ]
        return deepcopy(events[-limit:] if limit else [])

    def archive_old_decisions(self, domain: str, keep_recent: int = 800) -> int:
        keep_recent = max(int(keep_recent), 0)
        decisions = [
            decision
            for decision in self._ordered_decisions()
            if decision.get("domain") == domain
        ]
        if len(decisions) <= keep_recent:
            return 0
        to_archive = decisions[: len(decisions) - keep_recent]
        archived_at = time.time()
        for decision in to_archive:
            decision_id = decision["decision_id"]
            outcome = self._outcomes.get(decision_id)
            self._archive.append(
                {
                    "decision": deepcopy(decision),
                    "outcome": deepcopy(outcome),
                    "domain": domain,
                    "archived_at": archived_at,
                    "archive_reason": "retention_window",
                }
            )
            self._outcomes.pop(decision_id, None)
            self._decisions.pop(decision_id, None)
            self._edges = [
                edge for edge in self._edges if edge.get("decision_id") != decision_id
            ]
        return len(to_archive)

    def count_archived(self, domain: str) -> int:
        return sum(1 for row in self._archive if row.get("domain") == domain)

    def link_decision_to_entity(
        self,
        decision_id: str,
        entity_id: str,
        edge_type: str = "DECIDED_ON",
    ) -> None:
        decision = self._decisions.get(decision_id)
        domain = str((decision or {}).get("domain") or self.domain)
        self._edges.append(
            {
                "domain": domain,
                "decision_id": decision_id,
                "entity_id": entity_id,
                "edge_type": edge_type,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    def get_decision_links(self, decision_id: str | None = None) -> list[dict[str, Any]]:
        links = [
            {
                key: value
                for key, value in edge.items()
                if key != "domain"
            }
            for edge in self._edges
            if edge.get("domain") == self.domain
            and (decision_id is None or edge["decision_id"] == decision_id)
        ]
        return deepcopy(links)

    def reset(self) -> None:
        self._decisions.clear()
        self._outcomes.clear()
        self._edges.clear()
        self._centroid_checkpoints.clear()
        self._evolution_events.clear()
        self._archive.clear()
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
