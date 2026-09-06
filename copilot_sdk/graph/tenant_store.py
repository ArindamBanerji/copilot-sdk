"""Tenant-scoped GraphStore decorator with backward-compatible signatures."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, cast

from copilot_sdk.config.tenant import current_tenant_id, validate_tenant_id
from copilot_sdk.graph.protocol import GraphStore


class TenantScopedGraphStore:
    """Apply tenant scope to an existing domain-scoped GraphStore.

    The wrapped store remains the source of truth (AGE in production). Tenant
    identity is stored as a property inside each record's metadata/state while
    reads are filtered before they reach callers. This keeps the frozen
    GraphStore method signatures compatible with existing copilot services.
    """

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

    def get_decision(self, decision_id: str, domain: str) -> dict[str, Any] | None:
        row = self._store.get_decision(decision_id, domain)
        return row if self._belongs(row) else None

    def get_decisions(self, domain: str, category: str | None = None, limit: int = 400) -> list[dict[str, Any]]:
        return self._filter(self._store.get_decisions(domain, category, limit))

    def get_all_decisions(self, domain: str) -> list[dict[str, Any]]:
        return self._filter(self._store.get_all_decisions(domain))

    def get_archived_decisions(self, domain: str) -> list[dict[str, Any]]:
        return self._filter(self._store.get_archived_decisions(domain))

    def get_verified_decisions(self, domain: str) -> list[dict[str, Any]]:
        return self._filter(self._store.get_verified_decisions(domain))

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
        return getattr(self._store, name)
