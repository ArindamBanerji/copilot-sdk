"""Legacy signal filtering wrapper for GraphStore.

This wrapper hides decisions whose metadata contains both signal marker keys.
The filtering rule is independent of category and marker value truthiness.
Reads use the public GraphStore and optional traversal protocols; capabilities
that a store does not declare are logged and skipped.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from copilot_sdk.timestamps import normalize_timestamp

from copilot_sdk.graph.production import GraphStoreWrapper
from copilot_sdk.graph.protocol import GraphStore, GraphTraversalStore, ProtocolV2GraphStore

logger = logging.getLogger(__name__)


def is_legacy_signal_decision(decision: Any) -> bool:
    """Match only the two metadata keys always written by legacy signal publishing."""
    if not isinstance(decision, dict):
        return False
    metadata = decision.get("metadata")
    return isinstance(metadata, dict) and {
        "signal_detail", "signal_timestamp",
    }.issubset(metadata)


class LegacySignalFilteringGraphStore(GraphStoreWrapper):
    """Filter decision views while delegating writes and verified statistics."""

    def __init__(self, store: GraphStore, *, domain: str = "") -> None:
        self._store = store
        self.domain = domain

    def get_decision(
        self, decision_id: str, domain: str, *, include_outcome: bool = False,
    ) -> dict[str, Any] | None:
        decision = self._store.get_decision(decision_id, domain, include_outcome=include_outcome)
        return None if is_legacy_signal_decision(decision) else decision

    def get_decisions(
        self, domain: str, category: str | None = None, limit: int = 400,
        *, offset: int = 0,
    ) -> list[dict[str, Any]]:
        rows = [
            row for row in self._store.get_all_decisions(domain)
            if (category is None or row.get("category") == category)
            and not is_legacy_signal_decision(row)
        ]
        rows.sort(key=lambda row: (normalize_timestamp(row.get("created_at") or 0.0), str(row.get("decision_id") or "")))
        start = max(int(offset), 0)
        return rows[start:start + max(int(limit), 0)]

    def get_all_decisions(self, domain: str) -> list[dict[str, Any]]:
        return [
            row for row in self._store.get_all_decisions(domain)
            if not is_legacy_signal_decision(row)
        ]

    def get_archived_decisions(self, domain: str) -> list[dict[str, Any]]:
        return [
            row for row in self._store.get_archived_decisions(domain)
            if not is_legacy_signal_decision(row)
        ]

    def count_decisions(self, domain: str) -> int:
        return self._count(domain, archived=False)

    def count_archived(self, domain: str) -> int:
        return self._count(domain, archived=True)

    def _entity_links(self, entity_id: str, *, domain: str, limit: int = 100) -> list[dict[str, Any]]:
        if limit <= 0:
            return []
        if not isinstance(self._store, GraphTraversalStore):
            logger.warning("Entity-link traversal unavailable: store lacks GraphTraversalStore")
            return []
        return [
            edge for edge in self._store.get_decision_links(domain=domain, limit=None)
            if str(edge.get("entity_id") or "") == str(entity_id)
            and self.get_decision(str(edge.get("decision_id")), domain) is not None
        ]

    def _get_entity_links(self, entity_id: str, *, domain: str, limit: int = 100) -> list[dict[str, Any]]:
        return self._entity_links(entity_id, domain=domain, limit=limit)

    def _contains_legacy_decision(self, value: Any) -> bool:
        # AGE paths may nest vertices and JSON-encoded properties. Drop a path
        # containing a hidden decision as a unit rather than inventing new edges.
        if isinstance(value, str):
            try:
                return self._contains_legacy_decision(json.loads(value))
            except ValueError:
                # AGE may retain type annotations inside path strings. Strip
                # only tokens outside JSON strings, preserving user text.
                decoded = re.sub(
                    r'("(?:[^"\\]|\\.)*")|::[A-Za-z_]\w*',
                    lambda match: match.group(1) or "", value,
                )
                if decoded == value:
                    return False
                try:
                    return self._contains_legacy_decision(json.loads(decoded))
                except ValueError:
                    return False
        if isinstance(value, dict):
            metadata = value.get("metadata")
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except ValueError:
                    metadata = None
            if "decision_id" in value and is_legacy_signal_decision({"metadata": metadata}):
                return True
            return any(self._contains_legacy_decision(item) for item in value.values())
        if isinstance(value, (list, tuple)):
            return any(self._contains_legacy_decision(item) for item in value)
        return False

    def query_context(self, entity_id: str, max_depth: int, *, domain: str) -> list[dict[str, Any]]:
        if not isinstance(self._store, GraphTraversalStore):
            logger.warning("Context traversal unavailable: store lacks GraphTraversalStore")
            return []
        rows = self._store.query_context(entity_id, max_depth, domain=domain)
        return [row for row in rows if not self._contains_legacy_decision(row)]

    def decision_movement(self, domain: str, decision_id: str) -> list[dict[str, Any]]:
        if self.get_decision(decision_id, domain) is None:
            return []
        if not isinstance(self._store, ProtocolV2GraphStore):
            logger.warning("Decision movement unavailable: store lacks ProtocolV2GraphStore")
            return []
        rows = self._store.decision_movement(domain, decision_id)
        return [row for row in rows if not self._contains_legacy_decision(row)]

    def contextual_judgment(self, domain: str, entity_group: str, category: str) -> list[dict[str, Any]]:
        if not isinstance(self._store, ProtocolV2GraphStore):
            logger.warning("Contextual judgment unavailable: store lacks ProtocolV2GraphStore")
            return []
        rows = self._store.contextual_judgment(domain, entity_group, category)
        return [row for row in rows if not self._contains_legacy_decision(row)]

    def query_similar(self, entity_id: str, limit: int, *, domain: str) -> list[dict[str, Any]]:
        if limit <= 0:
            return []
        # An explicitly hidden decision cannot serve as a source for similarity.
        source = self._store.get_decision(entity_id, domain)
        if is_legacy_signal_decision(source):
            return []
        if not isinstance(self._store, GraphTraversalStore):
            logger.warning("Similarity traversal unavailable: store lacks GraphTraversalStore")
            return []
        rows = self._store.query_similar(entity_id, limit, domain=domain)
        visible = [row for row in rows if not is_legacy_signal_decision(row)]
        if len(rows) >= limit and len(visible) < limit:
            logger.warning(
                "Similarity results underfilled after legacy filtering; "
                "GraphTraversalStore does not expose offset paging"
            )
        return visible

    def get_checkpoint_lineage(self, domain: str, checkpoint_id: str) -> dict[str, Any] | None:
        decision = self._store.get_checkpoint_lineage(domain, checkpoint_id)
        return None if is_legacy_signal_decision(decision) else decision

    def promotion_basis(self, domain: str, rule_id: str) -> list[dict[str, Any]]:
        if not isinstance(self._store, ProtocolV2GraphStore):
            logger.warning("Promotion basis unavailable: store lacks ProtocolV2GraphStore")
            return []
        rows = self._store.promotion_basis(domain, rule_id)
        return [row for row in rows if not self._contains_legacy_decision(row)]

    def save_centroids(
        self, domain: str, category: str, centroids: Any,
        metadata: dict[str, Any] | None = None, **kwargs: Any,
    ) -> None:
        # New snapshots use visible counts; explicit historical counts are authoritative.
        if "decisions_count" not in kwargs:
            kwargs["decisions_count"] = self.count_decisions(domain)
        self._store.save_centroids(domain, category, centroids, metadata, **kwargs)

    def _count(self, domain: str, *, archived: bool) -> int:
        rows = (
            self._store.get_archived_decisions(domain)
            if archived else self._store.get_all_decisions(domain)
        )
        return sum(not is_legacy_signal_decision(row) for row in rows)

    def __getattr__(self, name: str) -> Any:
        # Methods returning decisions must have explicit filtered overrides;
        # this keeps non-decision GraphStore capabilities delegated unchanged.
        return getattr(self._store, name)
