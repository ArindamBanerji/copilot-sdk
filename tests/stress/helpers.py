"""Shared constants and helper functions for offline stress tests.

Not a conftest — these are explicit imports for test data setup.
"""
from __future__ import annotations

from copilot_sdk.graph.memory_store import InMemoryGraphStore


DOMAINS = ["trading", "purchasing", "dataops", "s2p", "soc"]

SAMPLE_FACTORS = {
    "trading": {"momentum": 0.7, "value": 0.4, "quality": 0.8,
                "volatility": 0.3, "sentiment": 0.6, "liquidity": 0.5},
    "purchasing": {"demand_forecast": 0.7, "supplier_reliability": 0.6,
                   "cost_trend": 0.5, "inventory_level": 0.4,
                   "lead_time": 0.3, "quality_score": 0.8},
    "dataops": {"data_freshness": 0.8, "pipeline_health": 0.7,
                "schema_stability": 0.6, "query_performance": 0.5,
                "lineage_coverage": 0.4, "anomaly_score": 0.3},
    "s2p": {"match_confidence": 0.9, "po_alignment": 0.7,
            "grn_status": 0.8, "payment_terms": 0.5,
            "supplier_history": 0.6, "duplicate_risk": 0.1,
            "amount_variance": 0.3},
    "soc": {"data_freshness": 0.8, "pipeline_health": 0.7,
            "schema_stability": 0.6, "query_performance": 0.5,
            "lineage_coverage": 0.4, "anomaly_score": 0.3},
}


def seed_decisions(store: InMemoryGraphStore, domain: str, n: int,
                   *, correct_ratio: float = 0.8) -> list[str]:
    """Seed N decisions with outcomes. Returns decision IDs."""
    factors = SAMPLE_FACTORS.get(domain, SAMPLE_FACTORS["trading"])
    ids = []
    for i in range(n):
        did = store.write_decision(
            domain=domain,
            category=f"cat_{i % 3}",
            action="approve",
            confidence=0.5 + (i % 10) * 0.05,
            factors=factors,
            metadata={"seq": i},
        )
        ids.append(did)
        if i < int(n * correct_ratio):
            store.write_outcome(did, "approve", True, domain=domain)
        else:
            store.write_outcome(did, "reject", False, domain=domain)
    return ids
