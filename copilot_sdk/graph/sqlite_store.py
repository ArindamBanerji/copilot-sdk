"""SQLite GraphStore adapter backed by DecisionStore."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from copilot_sdk.scoring.storage import DecisionStore


class SQLiteGraphStore:
    """Open-call-close adapter over the existing SQLite DecisionStore."""

    def __init__(self, db_path: str | Path, domain: str = "graph") -> None:
        self.db_path = str(db_path)
        self.domain = domain

    def write_decision(
        self,
        entity_id: str,
        category: str,
        action: str,
        confidence: float,
        factors: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> str:
        meta = metadata or {}
        decision_id = str(meta.get("decision_id") or uuid.uuid4().hex[:12])
        factor_names = list(factors)
        factor_vector = [float(factors[name]) for name in factor_names]
        recommended_index = int(meta.get("recommended_index", 0))
        category_index = int(meta.get("category_index", 0))
        probabilities = meta.get("probabilities")
        if probabilities is None:
            probabilities = [float(confidence)]

        store = DecisionStore(self.db_path)
        try:
            store.save_decision(
                decision_id=decision_id,
                domain=str(meta.get("domain", self.domain)),
                category=category,
                category_index=category_index,
                factors={
                    **factors,
                    "entity_id": entity_id,
                    "metadata": meta,
                },
                factor_vector=factor_vector,
                recommended_action=action,
                recommended_index=recommended_index,
                confidence=float(confidence),
                probabilities=probabilities,
                created_at=float(meta.get("created_at", time.time())),
            )
        finally:
            store.close()
        return decision_id

    def write_outcome(
        self,
        decision_id: str,
        actual_action: str,
        is_correct: bool,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        meta = metadata or {}
        store = DecisionStore(self.db_path)
        try:
            store.save_outcome(
                decision_id=decision_id,
                actual_action=actual_action,
                actual_index=int(meta.get("actual_index", 0)),
                is_correct=bool(is_correct),
                verified_at=float(meta.get("verified_at", time.time())),
            )
        finally:
            store.close()

    def get_decision(self, decision_id: str) -> dict[str, Any] | None:
        store = DecisionStore(self.db_path)
        try:
            try:
                return self._normalize_decision(store.get_decision(decision_id))
            except KeyError:
                return None
        finally:
            store.close()

    def get_decisions(
        self,
        category: str | None = None,
        limit: int = 400,
    ) -> list[dict[str, Any]]:
        store = DecisionStore(self.db_path)
        try:
            decisions = [
                self._normalize_decision(decision)
                for decision in store.get_all_decisions()
                if category is None or decision["category"] == category
            ]
            return decisions[: max(int(limit), 0)]
        finally:
            store.close()

    def get_verified_decisions(self) -> list[dict[str, Any]]:
        store = DecisionStore(self.db_path)
        try:
            return [
                self._normalize_decision(decision)
                for decision in store.get_verified_decisions()
            ]
        finally:
            store.close()

    def count_verified(self) -> int:
        store = DecisionStore(self.db_path)
        try:
            return store.count_verified()
        finally:
            store.close()

    def count_correct(self) -> int:
        store = DecisionStore(self.db_path)
        try:
            return store.count_correct()
        finally:
            store.close()

    def get_all_decisions(self) -> list[dict[str, Any]]:
        return self.get_decisions(category=None, limit=10**12)

    def save_centroids(
        self,
        decision_id: str,
        category: str,
        centroids: Any,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        meta = metadata or {}
        store = DecisionStore(self.db_path)
        try:
            store.save_centroids(
                centroids,
                iks=float(meta.get("iks", 0.0)),
                decision_id=decision_id,
                category=category,
                metadata=meta,
            )
        finally:
            store.close()

    def get_centroid_checkpoints(self, limit: int = 50) -> list[dict[str, Any]]:
        store = DecisionStore(self.db_path)
        try:
            return store.get_centroid_checkpoints(limit=max(int(limit), 0))
        finally:
            store.close()

    def save_evolution_event(
        self,
        event_type: str,
        rule_name: str,
        variant_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        store = DecisionStore(self.db_path)
        try:
            store.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS evolution_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    rule_name TEXT NOT NULL,
                    variant_id TEXT NOT NULL,
                    metadata TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            store.connection.execute(
                """
                INSERT INTO evolution_events (
                    event_type, rule_name, variant_id, metadata
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    event_type,
                    rule_name,
                    variant_id,
                    json.dumps(metadata or {}),
                ),
            )
            store.connection.commit()
        finally:
            store.close()

    def close(self) -> None:
        return None

    def _normalize_decision(self, decision: dict[str, Any]) -> dict[str, Any]:
        factors = dict(decision.get("factors") or {})
        metadata = factors.get("metadata") if isinstance(factors.get("metadata"), dict) else {}
        entity_id = str(factors.get("entity_id") or metadata.get("entity_id") or decision["decision_id"])
        normalized = dict(decision)
        normalized.update({
            "entity_id": entity_id,
            "metadata": metadata,
        })
        return normalized
