"""Concurrent store operations — thread safety tests.

Verifies InMemoryGraphStore handles concurrent writes correctly.
These are store-level tests. Scorer-level concurrency tests
require Codex (needs CompoundingScorer API).
"""
from __future__ import annotations

import concurrent.futures
import threading
import time

import pytest
from copilot_sdk.graph.memory_store import InMemoryGraphStore

from .helpers import DOMAINS, SAMPLE_FACTORS


class TestConcurrentWrites:
    """Multiple threads writing to the same store."""

    def test_50_concurrent_writes_all_persist(self):
        """50 threads each write one decision. All 50 must persist."""
        store = InMemoryGraphStore(domain="trading")
        ids: list[str] = []
        lock = threading.Lock()

        def write_one(index: int) -> str:
            did = store.write_decision(
                domain="trading",
                category=f"cat_{index % 3}",
                action="buy",
                confidence=0.5 + (index % 10) * 0.05,
                factors=SAMPLE_FACTORS["trading"],
                metadata={"thread_index": index},
            )
            with lock:
                ids.append(did)
            return did

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(write_one, i) for i in range(50)]
            concurrent.futures.wait(futures)
            for f in futures:
                f.result()  # raise if any thread failed

        assert len(ids) == 50
        assert len(set(ids)) == 50  # all unique
        assert store.count_decisions("trading") == 50

    def test_concurrent_cross_domain_no_leakage(self):
        """5 domains × 10 threads. No cross-domain leakage."""
        store = InMemoryGraphStore(domain="trading")

        def write_domain(domain: str, count: int) -> list[str]:
            result_ids = []
            factors = SAMPLE_FACTORS[domain]
            for i in range(count):
                did = store.write_decision(
                    domain=domain,
                    category="test",
                    action="approve",
                    confidence=0.5,
                    factors=factors,
                )
                result_ids.append(did)
            return result_ids

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            futures = {
                domain: pool.submit(write_domain, domain, 10)
                for domain in DOMAINS
            }
            concurrent.futures.wait(futures.values())

        for domain in DOMAINS:
            count = store.count_decisions(domain)
            assert count == 10, f"{domain}: expected 10, got {count}"
            decisions = store.get_all_decisions(domain)
            for d in decisions:
                assert d["domain"] == domain

    def test_concurrent_write_and_read(self):
        """One thread writes, another reads. No crash or corruption."""
        store = InMemoryGraphStore(domain="trading")
        errors: list[str] = []
        stop = threading.Event()

        def writer():
            for i in range(100):
                store.write_decision(
                    domain="trading", category="test", action="buy",
                    confidence=0.5, factors=SAMPLE_FACTORS["trading"],
                )
            stop.set()

        def reader():
            while not stop.is_set():
                try:
                    decisions = store.get_all_decisions("trading")
                    for d in decisions:
                        assert d["domain"] == "trading"
                except Exception as e:
                    errors.append(str(e))
                time.sleep(0.001)

        t_write = threading.Thread(target=writer)
        t_read = threading.Thread(target=reader)
        t_write.start()
        t_read.start()
        t_write.join(timeout=10)
        t_read.join(timeout=10)

        assert not errors, f"Read errors during concurrent write: {errors[:3]}"
        assert store.count_decisions("trading") == 100

    def test_concurrent_write_outcome(self):
        """Write decisions, then concurrent outcome writes."""
        store = InMemoryGraphStore(domain="trading")
        ids = []
        for i in range(50):
            did = store.write_decision(
                domain="trading", category="test", action="buy",
                confidence=0.5, factors=SAMPLE_FACTORS["trading"],
            )
            ids.append(did)

        def write_outcome(did: str, index: int):
            store.write_outcome(
                did, "buy", index % 2 == 0, domain="trading",
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(write_outcome, ids[i], i) for i in range(50)]
            concurrent.futures.wait(futures)
            for f in futures:
                f.result()

        verified = store.count_verified("trading")
        assert verified == 50

    def test_no_duplicate_ids_under_load(self):
        """200 concurrent writes, all IDs unique."""
        store = InMemoryGraphStore(domain="trading")
        all_ids: list[str] = []
        lock = threading.Lock()

        def write_batch(start: int):
            batch_ids = []
            for i in range(20):
                did = store.write_decision(
                    domain="trading", category="test", action="buy",
                    confidence=0.5, factors=SAMPLE_FACTORS["trading"],
                )
                batch_ids.append(did)
            with lock:
                all_ids.extend(batch_ids)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(write_batch, i * 20) for i in range(10)]
            concurrent.futures.wait(futures)

        assert len(all_ids) == 200
        assert len(set(all_ids)) == 200, "Duplicate decision IDs generated"
