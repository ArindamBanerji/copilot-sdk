"""Archive behavior tests.

Tests the archive lifecycle at the STORE level. Prevents recurrence
of the _maybe_archive bug where learn() implicitly archived decisions
beyond keep_recent=800.

These tests verify:
- Archiving is an explicit operation, not implicit
- Archived decisions are excluded from get_all_decisions
- Archived decisions are included in get_archived_decisions
- Count methods correctly scope to non-archived
"""
from __future__ import annotations

import pytest
from copilot_sdk.graph.memory_store import InMemoryGraphStore

from .helpers import SAMPLE_FACTORS, seed_decisions


class TestExplicitArchive:
    """archive_old_decisions is explicit and correct."""

    def test_no_implicit_archive_on_write(self):
        """Writing 1000 decisions does NOT archive any."""
        store = InMemoryGraphStore(domain="trading")
        for i in range(1000):
            store.write_decision(
                domain="trading", category="test", action="buy",
                confidence=0.5, factors=SAMPLE_FACTORS["trading"],
            )
        assert store.count_decisions("trading") == 1000
        all_d = store.get_all_decisions("trading")
        assert len(all_d) == 1000

    def test_explicit_archive_reduces_active(self):
        """archive_old_decisions keeps only keep_recent."""
        store = InMemoryGraphStore(domain="trading")
        seed_decisions(store, "trading", 100)
        before = store.count_decisions("trading")
        assert before == 100
        archived = store.archive_old_decisions("trading", keep_recent=80)
        assert archived == 20
        after = store.count_decisions("trading")
        assert after == 80

    def test_archived_excluded_from_get_all(self):
        """get_all_decisions excludes archived."""
        store = InMemoryGraphStore(domain="trading")
        ids = seed_decisions(store, "trading", 50)
        store.archive_old_decisions("trading", keep_recent=30)
        active = store.get_all_decisions("trading")
        assert len(active) == 30
        active_ids = {d["decision_id"] for d in active}
        # The most recent 30 should be kept
        assert len(active_ids) == 30

    def test_archived_available_via_get_archived(self):
        """get_archived_decisions returns only archived."""
        store = InMemoryGraphStore(domain="trading")
        seed_decisions(store, "trading", 50)
        store.archive_old_decisions("trading", keep_recent=30)
        archived = store.get_archived_decisions("trading")
        assert len(archived) == 20

    def test_archive_count_method(self):
        """count_archived returns correct count."""
        store = InMemoryGraphStore(domain="trading")
        seed_decisions(store, "trading", 50)
        assert store.count_archived("trading") == 0
        store.archive_old_decisions("trading", keep_recent=40)
        assert store.count_archived("trading") == 10

    def test_verified_counts_exclude_archived(self):
        """count_verified only counts non-archived decisions."""
        store = InMemoryGraphStore(domain="trading")
        seed_decisions(store, "trading", 100, correct_ratio=1.0)
        before_verified = store.count_verified("trading")
        assert before_verified == 100
        store.archive_old_decisions("trading", keep_recent=60)
        after_verified = store.count_verified("trading")
        assert after_verified == 60

    def test_archive_domain_isolated(self):
        """Archiving trading does not affect purchasing."""
        store = InMemoryGraphStore(domain="trading")
        seed_decisions(store, "trading", 50)
        seed_decisions(store, "purchasing", 50)
        store.archive_old_decisions("trading", keep_recent=20)
        assert store.count_decisions("trading") == 20
        assert store.count_decisions("purchasing") == 50  # untouched

    def test_double_archive_is_idempotent(self):
        """Archiving twice with same keep_recent doesn't over-archive."""
        store = InMemoryGraphStore(domain="trading")
        seed_decisions(store, "trading", 50)
        store.archive_old_decisions("trading", keep_recent=30)
        assert store.count_decisions("trading") == 30
        store.archive_old_decisions("trading", keep_recent=30)
        assert store.count_decisions("trading") == 30
