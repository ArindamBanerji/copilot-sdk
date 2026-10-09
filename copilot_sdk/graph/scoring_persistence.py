"""Scoring-state extension over GraphStore's durable governance records.

This bridge supports existing AGE adapters without modifying their repository
or changing runtime GraphStore conformance. There is no local fallback store.
"""
from __future__ import annotations

from copy import deepcopy
import json
import math
from typing import Any

from copilot_sdk.graph.protocol import GraphStore


class GraphScoringPersistence:
    def __init__(self, store: GraphStore) -> None:
        self.store = store

    def _key(self, kind: str, *parts: Any) -> str:
        # TenantScopedGraphStore stamps/filter records, but its generic state
        # keys are not namespaced. Include tenant identity to avoid overwrites.
        tenant = str(getattr(self.store, "tenant_id", "default"))
        return "scoring:" + json.dumps([kind, tenant, *parts], separators=(",", ":"))

    def save_k_utility(self, domain: str, episode_id: str, k: int, utility: float,
                       metadata: dict[str, Any] | None = None) -> str:
        if not domain.strip() or not episode_id.strip() or k < 0 or not math.isfinite(utility):
            raise ValueError("utility requires domain, episode_id, nonnegative k and finite utility")
        key = self._key("k_utility", episode_id, k)
        self.store.save_governance(domain, key, {
            "record_type": "k_utility", "id": key, "domain": domain,
            "episode_id": episode_id, "k": k, "utility": float(utility),
            "metadata": deepcopy(metadata or {}),
        })
        return key

    def get_k_utilities(self, domain: str, episode_id: str | None = None,
                        limit: int = 100) -> list[dict[str, Any]]:
        if limit < 0:
            raise ValueError("limit must be nonnegative")
        rows = [deepcopy(row) for row in self.store.list_governance(domain)
                if row.get("record_type") == "k_utility"
                and (episode_id is None or row["episode_id"] == episode_id)]
        return sorted(rows, key=lambda row: (row["episode_id"], row["k"]))[:limit]

    def save_holdout_decision(self, domain: str, decision_id: str, holdout_group: str,
                              metadata: dict[str, Any] | None = None) -> str:
        if not domain.strip() or not decision_id.strip() or not holdout_group.strip():
            raise ValueError("holdout requires domain, decision_id and holdout_group")
        key = self._key("holdout", decision_id)
        self.store.save_governance(domain, key, {
            "record_type": "holdout", "id": key, "domain": domain,
            "decision_id": decision_id, "holdout_group": holdout_group,
            "metadata": deepcopy(metadata or {}),
        })
        return key

    def get_holdout_decisions(self, domain: str,
                              holdout_group: str | None = None) -> list[dict[str, Any]]:
        rows = [deepcopy(row) for row in self.store.list_governance(domain)
                if row.get("record_type") == "holdout"
                and (holdout_group is None or row["holdout_group"] == holdout_group)]
        return sorted(rows, key=lambda row: row["decision_id"])
