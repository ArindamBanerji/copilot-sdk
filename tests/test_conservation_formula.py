from __future__ import annotations

import pytest

from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring.scorer import (
    CompoundingScorer,
    _conservation_stats,
    _scale_raw_reward,
    compute_theta_min,
)


def _seed_verified(
    store: InMemoryGraphStore,
    *,
    total: int,
    correct: int,
    overrides: int,
) -> None:
    for index in range(total):
        decision_id = store.write_decision(
            getattr(store, "domain", "dataops"),
            category="batch_failure",
            action="retry",
            confidence=0.8,
            factors={
                "error_rate": 0.4,
                "duration": 0.4,
                "dependency_health": 0.4,
                "blast_radius": 0.4,
            },
            metadata={
                "created_at": 1000.0 + index,
                "entity_id": f"entity-{index}",
                "recommended_index": 0,
                "category_index": 0,
                "factor_vector": [0.4, 0.4, 0.4, 0.4],
            },
        )
        actual_action = "escalate" if index < overrides else "retry"
        store.write_outcome(
            decision_id,
            actual_action=actual_action,
            is_correct=index < correct,
            metadata={"verified_at": 2000.0 + index},
        )


def _scorer(tmp_path, graph_store: InMemoryGraphStore, domain: str = "dataops"):
    return CompoundingScorer.from_preset(
        domain,
        db_path=str(tmp_path / f"{domain}.db"),
        graph_store=graph_store,
        profile="test",
    )


def test_sdk_theta_min_canonical_examples():
    assert compute_theta_min(0.25, 200) == pytest.approx(0.4706, rel=1e-4)
    assert compute_theta_min(0.25, 50) == pytest.approx(1.8824, rel=1e-4)


def test_sdk_theta_min_zero_verified_conservative():
    assert compute_theta_min(0.25, 0) is None
    assert compute_theta_min(0.0, 200) is None


def test_sdk_override_rate_from_decision_history():
    graph_store = InMemoryGraphStore()
    _seed_verified(graph_store, total=10, correct=7, overrides=3)

    verified, correct, override_rate = _conservation_stats(graph_store)

    assert verified == 10
    assert correct == 7
    assert override_rate == pytest.approx(0.3)


def test_sdk_conservation_does_not_use_penalty_ratio_for_theta(tmp_path):
    graph_store = InMemoryGraphStore()
    _seed_verified(graph_store, total=100, correct=90, overrides=20)
    scorer = _scorer(tmp_path, graph_store)

    pause = scorer._conservation_pause()

    assert pause is not None
    assert pause["reason"] == "conservation_red"
    assert pause["override_rate"] == pytest.approx(0.2)
    assert pause["theta_min"] == pytest.approx(23.53 / (0.2 * 100))
    assert pause["theta_min"] != pytest.approx(23.53 / (10.0 * 100))


def test_sdk_conservation_uses_override_rate(tmp_path):
    low_override_store = InMemoryGraphStore()
    high_override_store = InMemoryGraphStore()
    _seed_verified(low_override_store, total=100, correct=90, overrides=5)
    _seed_verified(high_override_store, total=100, correct=90, overrides=50)

    low = _scorer(tmp_path, low_override_store, "dataops")._evolution_conservation_state()
    high = _scorer(tmp_path, high_override_store, "dataops")._evolution_conservation_state()

    assert low["override_rate"] == pytest.approx(0.05)
    assert high["override_rate"] == pytest.approx(0.5)
    assert low["theta_min"] == pytest.approx(23.53 / (0.05 * 100))
    assert high["theta_min"] == pytest.approx(23.53 / (0.5 * 100))
    assert low["theta_min"] > high["theta_min"]


def test_sdk_penalty_ratio_still_available_for_learning_role():
    assert _scale_raw_reward(-1.0, 5.0) == pytest.approx(-5.0)
    assert _scale_raw_reward(1.0, 5.0) == pytest.approx(1.0)
