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
from dataclasses import replace
from typing import Any

from copilot_sdk.graph.production import GraphStoreWrapper
from copilot_sdk.graph.protocol import (
    BoundedProjectionStore,
    GraphStore,
    GraphTraversalStore,
    ProtocolV2GraphStore,
)
from copilot_sdk.graph.query import (
    DecisionAggregate,
    DecisionChangePage,
    DecisionFilter,
    DecisionGroup,
    DecisionMetric,
    DecisionPageRequest,
    DecisionPageResult,
    DecisionProjection,
)

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
    """Filter decision views while delegating writes and verified statistics.

    TODO(DESIGN-GAP-R5): Wrapper permanence is undecided. No deprecation
    plan exists. If legacy signal decisions will be purged, this wrapper
    becomes dead code. If they persist indefinitely, the pagination
    limitation in ``query_similar`` needs addressing before production use.
    """

    _BOUNDED_ONLY_READS = frozenset({
        "query_decisions", "aggregate_decisions", "get_decision_changes",
    })

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
        *, offset: int = 0, chronological: bool = True,
    ) -> list[dict[str, Any]]:
        wanted_offset = max(int(offset), 0)
        wanted_limit = max(int(limit), 0)
        if wanted_limit == 0:
            return []
        page_size = max(100, wanted_limit)
        source_offset = 0
        visible: list[dict[str, Any]] = []
        while len(visible) < wanted_offset + wanted_limit:
            page = self._store.get_decisions(
                domain, category, page_size, offset=source_offset,
                chronological=chronological,
            )
            if not page:
                break
            visible.extend(row for row in page if not is_legacy_signal_decision(row))
            source_offset += len(page)
            if len(page) < page_size:
                break
        return visible[wanted_offset:wanted_offset + wanted_limit]

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
        """Return similar decisions after filtering legacy signal records.

        The traversal protocol has no cursor, so progressively larger prefixes
        are fetched and decision IDs are deduplicated across reads. Snapshot
        isolation would still be required to guarantee a stable result during
        concurrent deletions or reordering.
        """
        if limit <= 0:
            return []
        # An explicitly hidden decision cannot serve as a source for similarity.
        source = self._store.get_decision(entity_id, domain)
        if is_legacy_signal_decision(source):
            return []
        if not isinstance(self._store, GraphTraversalStore):
            logger.warning("Similarity traversal unavailable: store lacks GraphTraversalStore")
            return []
        fetch_limit = limit
        seen_ids: set[str] = set()
        visible: list[dict[str, Any]] = []
        while len(visible) < limit:
            rows = self._store.query_similar(entity_id, fetch_limit, domain=domain)
            added = 0
            for row in rows:
                decision_id = str(row.get("decision_id") or "")
                if not decision_id or decision_id in seen_ids:
                    continue
                seen_ids.add(decision_id)
                added += 1
                if not is_legacy_signal_decision(row):
                    visible.append(row)
                    if len(visible) >= limit:
                        break
            if len(rows) < fetch_limit or added == 0:
                break
            fetch_limit *= 2
        if len(visible) < limit:
            logger.warning(
                "Similarity results underfilled after legacy filtering; "
                "GraphTraversalStore does not expose offset paging"
            )
        return visible[:limit]

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
        if name in self._BOUNDED_ONLY_READS:
            raise AttributeError(
                f"{type(self).__name__} does not support bounded projection "
                f"method {name!r}; use BoundedLegacySignalFilteringGraphStore"
            )
        return getattr(self._store, name)

class BoundedLegacySignalFilteringGraphStore(LegacySignalFilteringGraphStore):
    """Legacy-signal policy wrapper for a bounded projection primary."""

    _bounded_store: BoundedProjectionStore

    def __init__(self, store: BoundedProjectionStore, *, domain: str = "") -> None:
        if not isinstance(store, BoundedProjectionStore):
            raise TypeError(
                "BoundedLegacySignalFilteringGraphStore requires a "
                "BoundedProjectionStore primary"
            )
        super().__init__(store, domain=domain)
        self._bounded_store = store

    @staticmethod
    def _inject_legacy_filter(filters: DecisionFilter | None) -> DecisionFilter:
        if filters is None:
            return DecisionFilter(exclude_legacy_signals=True)
        return replace(filters, exclude_legacy_signals=True)

    def query_decisions(
        self,
        domain: str,
        *,
        filters: DecisionFilter | None = None,
        projection: DecisionProjection = "summary",
        page: DecisionPageRequest | None = None,
        as_of_generation: int | None = None,
    ) -> DecisionPageResult:
        result: DecisionPageResult = self._bounded_store.query_decisions(
            domain,
            filters=self._inject_legacy_filter(filters),
            projection=projection,
            page=page,
            as_of_generation=as_of_generation,
        )
        return result

    def count_decisions(
        self, domain: str, *, filters: DecisionFilter | None = None,
    ) -> int:
        result: int = self._bounded_store.count_decisions(
            domain, filters=self._inject_legacy_filter(filters),
        )
        return result

    def aggregate_decisions(
        self,
        domain: str,
        *,
        filters: DecisionFilter | None = None,
        group_by: tuple[DecisionGroup, ...] = (),
        metrics: tuple[DecisionMetric, ...] = ("count",),
    ) -> tuple[DecisionAggregate, ...]:
        result: tuple[DecisionAggregate, ...] = self._bounded_store.aggregate_decisions(
            domain,
            filters=self._inject_legacy_filter(filters),
            group_by=group_by,
            metrics=metrics,
        )
        return result

    def get_decision_changes(
        self,
        domain: str,
        *,
        after_generation: int,
        limit: int = 1_000,
        projection: DecisionProjection = "full",
        filters: DecisionFilter | None = None,
    ) -> DecisionChangePage:
        result: DecisionChangePage = self._bounded_store.get_decision_changes(
            domain,
            after_generation=after_generation,
            limit=limit,
            projection=projection,
            filters=self._inject_legacy_filter(filters),
        )
        return result
