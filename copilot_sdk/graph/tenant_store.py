"""Tenant-scoped GraphStore decorator with backward-compatible signatures."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import Any, cast

from copilot_sdk.config.tenant import current_tenant_id, validate_tenant_id
from copilot_sdk.graph.protocol import BoundedProjectionStore, GraphStore
from copilot_sdk.graph.production import GraphStoreWrapper
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


class TenantScopedGraphStore(GraphStoreWrapper):
    """Apply tenant scope to an existing domain-scoped GraphStore.

    The wrapped store remains the source of truth (AGE in production). Tenant
    identity is stored as a property inside each record's metadata/state while
    reads are filtered before they reach callers. This keeps the frozen
    GraphStore method signatures compatible with existing copilot services.
    """

    _BOUNDED_ONLY_READS = frozenset({
        "query_decisions", "aggregate_decisions", "get_decision_changes",
    })

    def __init__(self, store: GraphStore, tenant_id: str | None = None) -> None:
        self._store = store
        self._fixed_tenant = validate_tenant_id(tenant_id) if tenant_id else None
        self.domain = str(getattr(store, "domain", ""))

    @property
    def tenant_id(self) -> str:
        return self._fixed_tenant or str(current_tenant_id())

    def _stamp(self, payload: dict[str, Any] | None) -> dict[str, Any]:
        stamped = deepcopy(payload or {})
        stamped["tenant_id"] = self.tenant_id
        return stamped

    def _belongs(self, row: Any) -> bool:
        if not isinstance(row, dict):
            return False
        metadata = row.get("metadata")
        stored_tenant = row.get("tenant_id")
        if stored_tenant is None and isinstance(metadata, dict):
            stored_tenant = metadata.get("tenant_id")
        return str(stored_tenant or "default") == self.tenant_id

    def _filter(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [row for row in rows if self._belongs(row)]

    def write_decision(self, domain: str, category: str, action: str, confidence: float, factors: dict[str, Any], metadata: dict[str, Any] | None = None) -> str:
        return str(self._store.write_decision(domain, category, action, confidence, factors, self._stamp(metadata)))

    def write_outcome(self, decision_id: str, actual_action: str, is_correct: bool, metadata: dict[str, Any] | None = None, **kwargs: Any) -> None:
        self._store.write_outcome(decision_id, actual_action, is_correct, self._stamp(metadata), **kwargs)

    def get_decision(
        self,
        decision_id: str,
        domain: str,
        *,
        include_outcome: bool = False,
    ) -> dict[str, Any] | None:
        row = self._store.get_decision(
            decision_id,
            domain,
            include_outcome=include_outcome,
        )
        return row if self._belongs(row) else None

    def get_decisions(self, domain: str, category: str | None = None, limit: int = 400, *, offset: int = 0, chronological: bool = False) -> list[dict[str, Any]]:
        return self._filtered_page(
            lambda page_offset, page_limit: self._store.get_decisions(
                domain, category, page_limit, offset=page_offset,
                chronological=chronological,
            ),
            offset=offset,
            limit=limit,
        )

    def get_all_decisions(self, domain: str) -> list[dict[str, Any]]:
        return self._filter(self._store.get_all_decisions(domain))

    def get_archived_decisions(self, domain: str) -> list[dict[str, Any]]:
        return self._filter(self._store.get_archived_decisions(domain))

    def get_verified_decisions(self, domain: str, *, offset: int = 0, limit: int | None = None, chronological: bool = False, verified_after: tuple[float, str] | None = None) -> list[dict[str, Any]]:
        if limit is None:
            return self._filter(self._store.get_verified_decisions(
                domain, chronological=chronological, verified_after=verified_after,
            ))[
                max(int(offset), 0):
            ]
        return self._filtered_page(
            lambda page_offset, page_limit: self._store.get_verified_decisions(
                domain, offset=page_offset, limit=page_limit,
                chronological=chronological,
                verified_after=verified_after,
            ),
            offset=offset,
            limit=limit,
        )

    def _filtered_page(
        self,
        reader: Any,
        *,
        offset: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Page tenant-visible rows without materializing an unbounded read."""
        wanted_offset = max(int(offset), 0)
        wanted_limit = max(int(limit), 0)
        if wanted_limit == 0:
            return []
        page_size = max(100, wanted_limit)
        source_offset = 0
        visible: list[dict[str, Any]] = []
        while len(visible) < wanted_offset + wanted_limit:
            page = list(reader(source_offset, page_size))
            if not page:
                break
            visible.extend(self._filter(page))
            source_offset += len(page)
            if len(page) < page_size:
                break
        return visible[wanted_offset:wanted_offset + wanted_limit]

    def count_verified(self, domain: str) -> int:
        return len(self.get_verified_decisions(domain))

    def count_verified_decisions(self, domain: str) -> int:
        return len(self.get_verified_decisions(domain))

    def count_correct(self, domain: str) -> int:
        return sum(1 for row in self.get_verified_decisions(domain) if bool(row.get("is_correct", row.get("correct"))))

    def count_decisions(self, domain: str) -> int:
        return len(self.get_all_decisions(domain))

    def update_centroid(self, domain: str, category: str, action: str, centroid_vector: list[float], delta_norm: float, caused_by_decision_id: str | None = None) -> None:
        updater = cast(Any, getattr(self._store, "update_centroid"))
        updater(domain, category, action, centroid_vector, delta_norm, caused_by_decision_id)

    def get_centroids(self, domain: str) -> list[dict[str, object]]:
        reader = cast(Any, getattr(self._store, "get_centroids"))
        return self._filter(reader(domain))

    def update_dk_weights(self, domain: str, weight_tensor: list[list[float]], n_decisions_used: int, computed_at: float, **kwargs: Any) -> None:
        updater = cast(Any, getattr(self._store, "update_dk_weights"))
        updater(domain, weight_tensor, n_decisions_used, computed_at, **kwargs)

    def get_dk_weights(self, domain: str) -> dict[str, object] | None:
        reader = cast(Any, getattr(self._store, "get_dk_weights"))
        row = reader(domain)
        return row if self._belongs(row) else None

    def update_conservation_state(self, domain: str, status: str, alpha: float, q: float, V: int, theta_min: float, product: float, categories_total: int, categories_with_data: int, baseline_product: float, relative_threshold: float, complacency_flag: str, caused_by_decision_id: str | None = None, old_status: str | None = None) -> str:
        updater = getattr(self._store, "update_conservation_state")
        return str(updater(domain, status, alpha, q, V, theta_min, product, categories_total, categories_with_data, baseline_product, relative_threshold, complacency_flag, caused_by_decision_id, old_status))

    def get_conservation_state(self, domain: str) -> dict[str, object] | None:
        reader = cast(Any, getattr(self._store, "get_conservation_state"))
        row = reader(domain)
        return row if self._belongs(row) else None

    def save_evolution(self, domain: str, variant_id: str, state: dict[str, Any]) -> None:
        self._store.save_evolution(domain, variant_id, self._stamp(state))

    def get_evolution(self, domain: str, variant_id: str) -> dict[str, Any] | None:
        row = self._store.get_evolution(domain, variant_id)
        return row if self._belongs(row) else None

    def list_evolutions(self, domain: str) -> list[dict[str, Any]]:
        return self._filter(self._store.list_evolutions(domain))

    def delete_evolution(self, domain: str, variant_id: str) -> None:
        self._store.delete_evolution(domain, variant_id)

    def prune_evolution_events(self, domain: str, keep_recent: int = 10_000) -> int:
        pruner = getattr(cast(Any, self._store), "prune_evolution_events", None)
        if not callable(pruner):
            return 0
        return int(pruner(domain, keep_recent=keep_recent))

    def save_evolution_state(self, domain: str, variant_id: str, state: dict[str, Any]) -> None:
        self._store.save_evolution_state(domain, variant_id, self._stamp(state))

    def get_evolution_state(self, domain: str, variant_id: str) -> dict[str, Any] | None:
        row = self._store.get_evolution_state(domain, variant_id)
        return row if self._belongs(row) else None

    def save_posterior(self, domain: str, key: str, state: dict[str, Any]) -> None:
        self._store.save_posterior(domain, key, self._stamp(state))

    def get_posterior(self, domain: str, key: str) -> dict[str, Any] | None:
        row = self._store.get_posterior(domain, key)
        return row if self._belongs(row) else None

    def save_promotion(self, domain: str, rule_id: str, state: dict[str, Any]) -> None:
        self._store.save_promotion(domain, rule_id, self._stamp(state))

    def get_promotion(self, domain: str, rule_id: str) -> dict[str, Any] | None:
        row = self._store.get_promotion(domain, rule_id)
        return row if self._belongs(row) else None

    def list_promotions(self, domain: str) -> list[dict[str, Any]]:
        return self._filter(self._store.list_promotions(domain))

    def save_ledger(self, domain: str, entry_id: str, state: dict[str, Any]) -> None:
        self._store.save_ledger(domain, entry_id, self._stamp(state))

    def get_ledger(self, domain: str, entry_id: str) -> dict[str, Any] | None:
        row = self._store.get_ledger(domain, entry_id)
        return row if self._belongs(row) else None

    def list_ledgers(self, domain: str) -> list[dict[str, Any]]:
        return self._filter(self._store.list_ledgers(domain))

    def save_governance(self, domain: str, key: str, state: dict[str, Any]) -> None:
        self._store.save_governance(domain, key, self._stamp(state))

    def get_governance(self, domain: str, key: str) -> dict[str, Any] | None:
        row = self._store.get_governance(domain, key)
        return row if self._belongs(row) else None

    def list_governance(self, domain: str) -> list[dict[str, Any]]:
        return self._filter(self._store.list_governance(domain))

    def get_centroid_checkpoints(self, domain: str, include_v2: bool = False, **kwargs: Any) -> list[dict[str, Any]]:
        return [row for row in self._store.get_centroid_checkpoints(domain, include_v2, **kwargs) if self._belongs(row.get("metadata", row))]

    def load_latest_centroids(self, domain: str) -> Any | None:
        checkpoints = self.get_centroid_checkpoints(domain, include_v2=True, limit=None)
        if not checkpoints:
            return None
        latest = max(checkpoints, key=lambda row: float(row.get("created_at", row.get("created_at_epoch", 0.0)) or 0.0))
        return deepcopy(latest.get("centroids"))

    def save_centroids(self, domain: str, category: str, centroids: Any, metadata: dict[str, Any] | None = None, **kwargs: Any) -> None:
        self._store.save_centroids(domain, category, centroids, self._stamp(metadata), **kwargs)

    def __getattr__(self, name: str) -> Any:
        # Preserve non-state traversal helpers while the explicit methods above
        # enforce tenant filtering for all decision/control-plane state.
        if name in self._BOUNDED_ONLY_READS:
            raise AttributeError(
                f"{type(self).__name__} does not support bounded projection "
                f"method {name!r}; use BoundedTenantScopedGraphStore"
            )
        return getattr(self._store, name)


class BoundedTenantScopedGraphStore(TenantScopedGraphStore):
    """Tenant policy wrapper for a bounded projection primary."""

    _bounded_store: BoundedProjectionStore

    def __init__(
        self, store: BoundedProjectionStore, tenant_id: str | None = None,
    ) -> None:
        if not isinstance(store, BoundedProjectionStore):
            raise TypeError(
                "BoundedTenantScopedGraphStore requires a "
                "BoundedProjectionStore primary"
            )
        super().__init__(store, tenant_id=tenant_id)
        self._bounded_store = store

    def _inject_tenant_filter(
        self, filters: DecisionFilter | None,
    ) -> DecisionFilter:
        tenant_id = self.tenant_id
        if filters is None:
            return DecisionFilter(tenant_id=tenant_id)
        if filters.tenant_id is not None and filters.tenant_id != tenant_id:
            raise ValueError(
                f"tenant conflict: filter has {filters.tenant_id!r} "
                f"but authenticated tenant is {tenant_id!r}"
            )
        if filters.tenant_id == tenant_id:
            return filters
        return replace(filters, tenant_id=tenant_id)

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
            filters=self._inject_tenant_filter(filters),
            projection=projection,
            page=page,
            as_of_generation=as_of_generation,
        )
        return result

    def count_decisions(
        self, domain: str, *, filters: DecisionFilter | None = None,
    ) -> int:
        result: int = self._bounded_store.count_decisions(
            domain, filters=self._inject_tenant_filter(filters),
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
            filters=self._inject_tenant_filter(filters),
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
            filters=self._inject_tenant_filter(filters),
        )
        return result

    def write_governed_decision(
        self,
        decision_id: str,
        domain: str,
        category: str,
        category_index: int,
        recommended_action: str,
        recommended_index: int,
        confidence: float,
        probabilities: list[float],
        factor_vector: list[float],
        factor_names: list[str],
        source: str = "score",
        scorer_version: str = "",
        preset_version: str = "",
        factor_schema_version: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        tenant_id = self.tenant_id
        stamped = deepcopy(metadata or {})
        stamped["tenant_id"] = tenant_id
        bounded = cast(Any, self._store)
        bounded.write_governed_decision(
            decision_id,
            domain,
            category,
            category_index,
            recommended_action,
            recommended_index,
            confidence,
            probabilities,
            factor_vector,
            factor_names,
            source,
            scorer_version,
            preset_version,
            factor_schema_version,
            stamped,
        )
