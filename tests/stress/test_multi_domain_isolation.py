"""Multi-domain isolation tests.

Shared store, isolated domains. Trading decisions must not leak into
purchasing queries. Conservation must be domain-specific.
"""
from __future__ import annotations

import pytest
from copilot_sdk.graph.memory_store import InMemoryGraphStore

from .helpers import DOMAINS, SAMPLE_FACTORS, seed_decisions


class TestDomainIsolation:
    """Queries scoped to one domain never return another's data."""

    def test_five_domains_isolated(self, multi_domain_store):
        store = multi_domain_store
        for domain in DOMAINS:
            decisions = store.get_all_decisions(domain)
            assert len(decisions) == 10, f"{domain}: expected 10, got {len(decisions)}"
            for d in decisions:
                assert d["domain"] == domain, (
                    f"Decision {d['decision_id']} has domain={d['domain']}, "
                    f"expected {domain}"
                )

    def test_count_per_domain(self, multi_domain_store):
        store = multi_domain_store
        for domain in DOMAINS:
            assert store.count_decisions(domain) == 10

    def test_verified_per_domain(self):
        store = InMemoryGraphStore(domain="trading")
        # Seed trading with outcomes, purchasing without
        seed_decisions(store, "trading", 20, correct_ratio=1.0)
        for i in range(10):
            store.write_decision(
                domain="purchasing", category="test", action="order",
                confidence=0.5, factors=SAMPLE_FACTORS["purchasing"],
            )
        assert store.count_verified("trading") == 20
        assert store.count_verified("purchasing") == 0

    def test_write_to_one_domain_does_not_affect_another(self):
        store = InMemoryGraphStore(domain="trading")
        seed_decisions(store, "trading", 5)
        before_purchasing = store.count_decisions("purchasing")
        seed_decisions(store, "trading", 10)
        after_purchasing = store.count_decisions("purchasing")
        assert before_purchasing == after_purchasing == 0

    def test_category_isolation_across_domains(self):
        store = InMemoryGraphStore(domain="trading")
        # Same category name in two domains
        store.write_decision(
            domain="trading", category="quality", action="buy",
            confidence=0.5, factors=SAMPLE_FACTORS["trading"],
        )
        store.write_decision(
            domain="dataops", category="quality", action="investigate",
            confidence=0.5, factors=SAMPLE_FACTORS["dataops"],
        )
        trading_quality = store.get_decisions("trading", category="quality")
        dataops_quality = store.get_decisions("dataops", category="quality")
        assert len(trading_quality) == 1
        assert len(dataops_quality) == 1
        assert trading_quality[0]["domain"] == "trading"
        assert dataops_quality[0]["domain"] == "dataops"

    def test_total_across_all_domains(self, multi_domain_store):
        store = multi_domain_store
        total = sum(store.count_decisions(d) for d in DOMAINS)
        assert total == 50  # 5 domains × 10 each
