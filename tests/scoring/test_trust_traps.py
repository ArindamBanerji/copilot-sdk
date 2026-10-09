from __future__ import annotations

import numpy as np
import pytest
from types import SimpleNamespace

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
            metadata={"decision_id": f"d-{index}", "created_at": float(index + 1)},
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


@pytest.mark.parametrize("newest_first", [False, True])
def test_recency_bias_is_independent_of_read_order(newest_first: bool) -> None:
    rows = [
        {"decision_id": f"d{index:03d}", "created_at": float(index + 1),
         "category": "mixed", "is_correct": index >= 150 or index % 2 == 0}
        for index in range(200)
    ]
    if newest_first:
        rows.reverse()
    original = [dict(row) for row in rows]
    detector = TrustTrapDetector(None, SimpleNamespace(get_verified_decisions=lambda domain: rows), "trust")
    trap = next(trap for trap in detector.scan() if trap.trap_type == "RECENCY_BIAS")
    assert trap.evidence["recent_accuracy"] == 1.0
    assert trap.evidence["long_window_accuracy"] == 0.625
    assert rows == original


def test_no_traps_on_healthy_data() -> None:
    rows = [(f"category-{index % 4}", True) for index in range(200)]
    assert TrustTrapDetector(None, _store(rows), "trust").scan() == []


def _gaming_rows() -> list[dict[str, object]]:
    return ([{"category": "easy", "is_correct": True}] * 40
            + [{"category": "hard", "is_correct": False}] * 10)


def test_trust_trap_reads_conservation_state() -> None:
    store = InMemoryGraphStore(domain="trading")
    scorer = CompoundingScorer.from_preset(
        "trading", graph_store=store, profile="test", enable_rl=False
    )
    detector = TrustTrapDetector(
        scorer,
        SimpleNamespace(get_verified_decisions=lambda _domain: _gaming_rows()),
        "trading",
    )
    traps = detector.scan()
    gaming = next(trap for trap in traps if trap.trap_type == "CONSERVATION_GAMING")
    assert gaming.evidence["conservation"]["status"] == "COLD_START"
    assert detector.unavailable_checks == []


def test_trust_trap_no_scorer_marks_conservation_unavailable() -> None:
    detector = TrustTrapDetector(
        None,
        SimpleNamespace(get_verified_decisions=lambda _domain: _gaming_rows()),
        "trading",
    )
    detector.scan()
    assert detector.unavailable_checks == ["conservation_gaming"]


def test_trust_trap_missing_reader_reports_unavailable() -> None:
    store = InMemoryGraphStore(domain="trading")
    scorer = CompoundingScorer.from_preset(
        "trading", graph_store=store, profile="test", enable_rl=False
    )
    detector = TrustTrapDetector(scorer, SimpleNamespace(), "trading")
    detector.scan()
    assert detector.unavailable_checks == ["conservation_gaming"]


def test_verified_reader_raises_sets_unavailable() -> None:
    def raise_read_error(_domain: str) -> list[dict[str, object]]:
        raise RuntimeError("verified history unavailable")

    detector = TrustTrapDetector(
        None,
        SimpleNamespace(get_verified_decisions=raise_read_error),
        "trading",
    )

    traps = detector.scan()

    assert isinstance(traps, list)
    assert "conservation_gaming" in detector.unavailable_checks


def test_verified_reader_malformed_data_handled() -> None:
    detector = TrustTrapDetector(
        None,
        SimpleNamespace(get_verified_decisions=lambda _domain: None),
        "trading",
    )

    traps = detector.scan()

    assert isinstance(traps, list)
    assert "conservation_gaming" in detector.unavailable_checks


def test_trust_trap_genuine_empty_is_cold_start() -> None:
    store = InMemoryGraphStore(domain="trading")
    scorer = CompoundingScorer.from_preset(
        "trading", graph_store=store, profile="test", enable_rl=False
    )
    detector = TrustTrapDetector(scorer, store, "trading")
    assert detector.scan() == []
    assert detector.unavailable_checks == []


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
