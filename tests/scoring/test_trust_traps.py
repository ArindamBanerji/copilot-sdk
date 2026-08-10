from __future__ import annotations

import numpy as np
import pytest

from copilot_sdk.graph import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.scoring.trust_traps import TrustTrapDetector


def _store(rows: list[tuple[str, bool]]) -> InMemoryGraphStore:
    store = InMemoryGraphStore(domain="trust")
    for index, (category, correct) in enumerate(rows):
        decision_id = store.write_decision(
            "trust",
            category=category,
            action="investigate",
            confidence=0.8,
            factors={"signal": 0.7},
            metadata={"decision_id": f"d-{index}"},
        )
        store.write_outcome(
            decision_id,
            actual_action="investigate",
            is_correct=correct,
            domain="trust",
        )
    return store


def _types(detector: TrustTrapDetector) -> set[str]:
    return {trap.trap_type for trap in detector.scan()}


def test_category_divergence_detected() -> None:
    rows = [("stable", True)] * 10 + [("degrading", index < 20) for index in range(40)]
    rows += [("stable", True)] * 40 + [("degrading", False)] * 10
    assert "CATEGORY_DIVERGENCE" in _types(TrustTrapDetector(None, _store(rows), "trust"))


def test_volume_skew_detected() -> None:
    rows = [("easy", True)] * 80
    rows.extend((f"hard-{index}", False) for index in range(20))
    assert "VOLUME_SKEW" in _types(TrustTrapDetector(None, _store(rows), "trust"))


def test_recency_bias_detected() -> None:
    rows = [("mixed", index % 2 == 0) for index in range(150)]
    rows.extend(("mixed", True) for _ in range(50))
    assert "RECENCY_BIAS" in _types(TrustTrapDetector(None, _store(rows), "trust"))


def test_no_traps_on_healthy_data() -> None:
    rows = [(f"category-{index % 4}", True) for index in range(200)]
    assert TrustTrapDetector(None, _store(rows), "trust").scan() == []


def test_rollback_restores_centroids() -> None:
    store = InMemoryGraphStore(domain="trading")
    scorer = CompoundingScorer.from_preset("trading", graph_store=store, profile="test", enable_rl=False)
    factors = {name: 0.7 for name in scorer._preset.shape.factor_names}
    first = scorer.score(factors, "trend_following")
    scorer.learn(first.decision_id, first.action)
    checkpoints = store.get_centroid_checkpoints("trading", limit=None, include_v2=True)
    checkpoint = next(item for item in checkpoints if item.get("checkpoint_id"))
    expected = np.asarray(checkpoint["centroids"], dtype=np.float64).copy()

    for _ in range(5):
        result = scorer.score(factors, "trend_following")
        scorer.learn(result.decision_id, result.action)
    assert not np.array_equal(np.asarray(scorer._scorer.centroids), expected)

    rollback_result = scorer.rollback_to_checkpoint(str(checkpoint["checkpoint_id"]))
    assert rollback_result["rolled_back"] is True
    np.testing.assert_array_equal(np.asarray(scorer._scorer.centroids), expected)


def test_rollback_nonexistent_raises() -> None:
    store = InMemoryGraphStore(domain="trading")
    scorer = CompoundingScorer.from_preset("trading", graph_store=store, profile="test", enable_rl=False)
    with pytest.raises(ValueError, match="not found"):
        scorer.rollback_to_checkpoint("fake-id")
