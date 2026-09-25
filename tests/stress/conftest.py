"""Fixtures for offline stress tests.

All tests use InMemoryGraphStore — a real protocol implementation,
not a mock. No AGE required.
"""
from __future__ import annotations

import pytest
from copilot_sdk.graph.memory_store import InMemoryGraphStore

from .helpers import DOMAINS, SAMPLE_FACTORS


@pytest.fixture
def store():
    """Fresh InMemoryGraphStore for a single test."""
    return InMemoryGraphStore(domain="trading")


@pytest.fixture
def multi_domain_store():
    """InMemoryGraphStore with decisions seeded across all 5 domains."""
    s = InMemoryGraphStore(domain="trading")
    for domain in DOMAINS:
        factors = SAMPLE_FACTORS[domain]
        for i in range(10):
            s.write_decision(
                domain=domain,
                category=f"cat_{i % 3}",
                action="approve" if i % 2 == 0 else "reject",
                confidence=0.5 + (i * 0.04),
                factors=factors,
                metadata={"index": i},
            )
    return s
