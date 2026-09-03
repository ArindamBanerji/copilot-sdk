"""Demonstrate two isolated tenants sharing one copilot GraphStore."""

from __future__ import annotations

from copilot_sdk.config.tenant import tenant_context
from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.graph.tenant_store import TenantScopedGraphStore


def main() -> None:
    shared_store = InMemoryGraphStore(domain="trading", decision_id_prefix="TRD-")
    tenant_store = TenantScopedGraphStore(shared_store)

    for tenant_id, action in (("tenant-a", "buy"), ("tenant-b", "sell")):
        with tenant_context(tenant_id):
            tenant_store.write_decision(
                domain="trading",
                category="market",
                action=action,
                confidence=0.9,
                factors={"signal": 0.8},
            )

    for tenant_id in ("tenant-a", "tenant-b"):
        with tenant_context(tenant_id):
            decisions = tenant_store.get_all_decisions("trading")
            print(f"{tenant_id}: {len(decisions)} decision(s), actions={[row['recommended_action'] for row in decisions]}")


if __name__ == "__main__":
    main()
