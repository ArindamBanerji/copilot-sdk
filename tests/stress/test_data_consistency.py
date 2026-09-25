"""Data consistency tests — write/read round-trip integrity.

Every test uses InMemoryGraphStore (real protocol, not a mock).
Verifies that what goes in comes out unchanged.
"""
from __future__ import annotations

import pytest
from copilot_sdk.graph.memory_store import InMemoryGraphStore

from .helpers import SAMPLE_FACTORS, seed_decisions


class TestWriteReadRoundTrip:
    """Core write → read consistency."""

    def test_write_decision_then_get_returns_same(self, store):
        did = store.write_decision(
            domain="trading", category="momentum", action="buy",
            confidence=0.85, factors=SAMPLE_FACTORS["trading"],
            metadata={"ticker": "AAPL"},
        )
        got = store.get_decision(did, domain="trading")
        assert got is not None
        assert got["decision_id"] == did
        assert got["domain"] == "trading"
        assert got["category"] == "momentum"
        assert got["confidence"] == pytest.approx(0.85)

    def test_factors_preserved_exactly(self, store):
        factors = {"a": 0.123456789, "b": 0.0, "c": 1.0, "d": -0.5}
        did = store.write_decision(
            domain="trading", category="test", action="hold",
            confidence=0.5, factors=factors,
        )
        got = store.get_decision(did, domain="trading")
        for k, v in factors.items():
            assert got["factors"][k] == pytest.approx(v), f"Factor {k} mismatch"

    def test_metadata_preserved(self, store):
        meta = {"ticker": "MSFT", "amount": 10_000, "nested": {"key": "val"}}
        did = store.write_decision(
            domain="trading", category="test", action="buy",
            confidence=0.7, factors=SAMPLE_FACTORS["trading"],
            metadata=meta,
        )
        got = store.get_decision(did, domain="trading")
        assert got["metadata"]["ticker"] == "MSFT"
        assert got["metadata"]["amount"] == 10_000

    def test_outcome_written_on_learn(self, store):
        did = store.write_decision(
            domain="trading", category="test", action="buy",
            confidence=0.7, factors=SAMPLE_FACTORS["trading"],
        )
        store.write_outcome(did, "buy", True, domain="trading")
        # Outcomes are stored separately — verify via verified decisions
        verified = store.get_verified_decisions("trading")
        verified_ids = {d["decision_id"] for d in verified}
        assert did in verified_ids, f"{did} not in verified decisions after write_outcome"

    def test_decision_id_unique(self, store):
        ids = set()
        for _ in range(100):
            did = store.write_decision(
                domain="trading", category="test", action="buy",
                confidence=0.5, factors=SAMPLE_FACTORS["trading"],
            )
            assert did not in ids, f"Duplicate decision_id: {did}"
            ids.add(did)


class TestCountConsistency:
    """Count methods agree with collection methods."""

    def test_count_matches_get_all(self, store):
        seed_decisions(store, "trading", 25)
        count = store.count_decisions("trading")
        all_decisions = store.get_all_decisions("trading")
        assert count == len(all_decisions)

    def test_verified_subset_of_all(self, store):
        seed_decisions(store, "trading", 20, correct_ratio=0.6)
        all_d = store.get_all_decisions("trading")
        verified = store.get_verified_decisions("trading")
        all_ids = {d["decision_id"] for d in all_d}
        verified_ids = {d["decision_id"] for d in verified}
        assert verified_ids.issubset(all_ids)

    def test_count_verified_matches_verified_list(self, store):
        seed_decisions(store, "trading", 30, correct_ratio=0.7)
        count = store.count_verified("trading")
        verified = store.get_verified_decisions("trading")
        assert count == len(verified)

    def test_count_correct_lte_verified(self, store):
        seed_decisions(store, "trading", 40, correct_ratio=0.75)
        correct = store.count_correct("trading")
        verified = store.count_verified("trading")
        assert correct <= verified

    def test_empty_store_counts_zero(self):
        s = InMemoryGraphStore(domain="trading")
        assert s.count_decisions("trading") == 0
        assert s.count_verified("trading") == 0
        assert s.count_correct("trading") == 0
        assert s.get_all_decisions("trading") == []


class TestCategoryFiltering:
    """Category-scoped queries return correct subsets."""

    def test_get_decisions_filters_by_category(self, store):
        for cat in ["alpha", "beta", "gamma"]:
            for _ in range(5):
                store.write_decision(
                    domain="trading", category=cat, action="buy",
                    confidence=0.5, factors=SAMPLE_FACTORS["trading"],
                )
        alpha = store.get_decisions("trading", category="alpha")
        assert len(alpha) == 5
        assert all(d["category"] == "alpha" for d in alpha)

    def test_get_decisions_no_category_returns_all(self, store):
        for cat in ["alpha", "beta"]:
            for _ in range(5):
                store.write_decision(
                    domain="trading", category=cat, action="buy",
                    confidence=0.5, factors=SAMPLE_FACTORS["trading"],
                )
        all_d = store.get_decisions("trading")
        assert len(all_d) == 10

    def test_nonexistent_category_returns_empty(self, store):
        seed_decisions(store, "trading", 10)
        result = store.get_decisions("trading", category="nonexistent_xyz")
        assert result == []
