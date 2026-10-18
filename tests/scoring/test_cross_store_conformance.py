"""Conformance tests for direct GraphStore seeding and scorer bootstrap."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

import numpy as np

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.presets import PRESET_REGISTRY
from copilot_sdk.scoring.scorer import CompoundingScorer
from scripts.seed_all_decisions import seed_domain


def _scorer(domain: str, store: InMemoryGraphStore) -> CompoundingScorer:
    return CompoundingScorer.from_preset(
        domain,
        graph_store=store,
        profile="test",
        enable_rl=False,
    )


def _trading_factors(index: int) -> dict[str, float]:
    names = PRESET_REGISTRY["trading"]().shape.factor_names
    return {
        name: min(0.95, 0.15 + ((index + offset) % 7) * 0.1)
        for offset, name in enumerate(names)
    }


def _copy_verified_rows(
    source: InMemoryGraphStore,
    target: InMemoryGraphStore,
    domain: str,
) -> None:
    """Copy AGE-shaped verified rows without copying centroid checkpoints."""
    for row in source.get_verified_decisions(domain):
        factors = row.get("factors")
        assert isinstance(factors, Mapping)
        decision_id = str(row["decision_id"])
        target.write_decision(
            domain,
            category=str(row["category"]),
            action=str(row["recommended_action"]),
            confidence=float(row["confidence"]),
            factors={str(name): float(value) for name, value in factors.items()},
            metadata={
                "decision_id": decision_id,
                "category_index": int(row["category_index"]),
                "recommended_index": int(row["recommended_index"]),
                "factor_vector": list(row["factor_vector"]),
                "created_at": row["created_at"],
            },
        )
        target.write_outcome(
            decision_id,
            actual_action=str(row["actual_action"]),
            is_correct=bool(row["is_correct"]),
            metadata={
                "actual_index": int(row["actual_index"]),
                "verified_at": row["verified_at"],
            },
            domain=domain,
        )


def _seed_and_bootstrap(
    domain: str,
    *,
    count: int,
) -> tuple[InMemoryGraphStore, CompoundingScorer]:
    store = InMemoryGraphStore(domain=domain)
    result = seed_domain(domain, store, count=count, override_count=max(1, count // 4))
    assert result.decisions_seeded == count
    assert result.outcomes_seeded == count
    return store, _scorer(domain, store)


def _centroids(scorer: CompoundingScorer) -> np.ndarray:
    return cast(np.ndarray, np.asarray(scorer._scorer.centroids, dtype=np.float64))


def test_memory_store_scorer_parity() -> None:
    normal_store = InMemoryGraphStore(domain="trading")
    normal = _scorer("trading", normal_store)
    categories = PRESET_REGISTRY["trading"]().shape.category_names

    for index in range(20):
        result = normal.score(
            _trading_factors(index),
            categories[index % len(categories)],
        )
        learned = normal.learn(result.decision_id, result.action)
        assert not isinstance(learned, dict)

    replay_store = InMemoryGraphStore(domain="trading")
    _copy_verified_rows(normal_store, replay_store, "trading")
    replayed = _scorer("trading", replay_store)

    assert replayed._scorer.decision_count == 20
    assert np.allclose(_centroids(replayed), _centroids(normal), atol=1e-10)


def test_bootstrap_deterministic() -> None:
    store = InMemoryGraphStore(domain="trading")
    seed_domain("trading", store, count=20, override_count=5)

    first = _scorer("trading", store)
    second = _scorer("trading", store)

    assert first._scorer.decision_count == second._scorer.decision_count == 20
    assert np.allclose(_centroids(first), _centroids(second), atol=1e-10)


def test_bootstrap_preserves_conservation() -> None:
    store, scorer = _seed_and_bootstrap("trading", count=20)

    status = scorer.get_conservation_state()

    assert scorer.get_verified_count() == 20
    assert store.count_verified_decisions("trading") == 20
    assert status["verified_count"] == 20
    assert status["V"] == 20


def test_bootstrap_cold_vs_seeded() -> None:
    cold = _scorer("trading", InMemoryGraphStore(domain="trading"))
    _, seeded = _seed_and_bootstrap("trading", count=5)

    assert cold._cold_start is True
    assert seeded._cold_start is False
    assert seeded._scorer.decision_count == 5
    assert not np.allclose(_centroids(cold), _centroids(seeded), atol=1e-12)


def test_bootstrap_all_domains() -> None:
    for domain in ("trading", "purchasing", "dataops", "s2p"):
        store, scorer = _seed_and_bootstrap(domain, count=5)

        assert store.count_verified_decisions(domain) == 5
        assert scorer._scorer.decision_count > 0
        assert scorer._cold_start is False


def test_seed_then_bootstrap_round_trip() -> None:
    domain = "purchasing"
    store, scorer = _seed_and_bootstrap(domain, count=12)
    verified = store.get_verified_decisions(domain)

    assert len(verified) == 12
    assert scorer.get_verified_count() == 12
    assert scorer._scorer.decision_count == 12
    assert scorer._cold_start is False
    assert all(row["metadata"]["seed_domain"] == domain for row in verified)
