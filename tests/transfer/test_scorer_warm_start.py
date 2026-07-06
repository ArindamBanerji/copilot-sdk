from __future__ import annotations

import numpy as np

from copilot_sdk.graph.memory_store import InMemoryGraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer
from copilot_sdk.transfer import SharedPatternRegistry, TransferPattern


def _scorer(tmp_path) -> CompoundingScorer:
    return CompoundingScorer.from_preset(
        "s2p",
        db_path=str(tmp_path / "s2p.db"),
        graph_store=InMemoryGraphStore(domain="s2p"),
    )


def _pattern(
    category: str = "price_variance",
    action: str = "auto_approve",
    delta_length: int = 8,
    source_copilot: str = "dataops",
    confidence: float = 0.9,
) -> TransferPattern:
    return TransferPattern(
        pattern_id="p1",
        source_copilot=source_copilot,
        pattern_type="centroid_delta",
        category=category,
        action=action,
        win_rate=0.8,
        centroid_delta=[0.05 for _ in range(delta_length)],
        confidence=confidence,
    )


def test_warm_start_returns_summary_dict(tmp_path) -> None:
    scorer = _scorer(tmp_path)

    summary = scorer.warm_start([_pattern()])

    assert summary["applied"] == 1
    assert 0.0 < summary["score"] <= 1.0
    assert summary["source_copilots"] == ["dataops"]


def test_warm_start_changes_active_centroid_state(tmp_path) -> None:
    scorer = _scorer(tmp_path)
    before = scorer.gae_scorer.centroids.copy()

    scorer.warm_start([_pattern()], blend_weight=0.5)

    assert not np.array_equal(scorer.gae_scorer.centroids, before)


def test_warm_start_category_mapping_works(tmp_path) -> None:
    scorer = _scorer(tmp_path)
    registry = SharedPatternRegistry()
    registry.register(_pattern(category="freshness_violation"))

    summary = scorer.warm_start(
        registry,
        category_mapping={"freshness_violation": "price_variance"},
    )

    assert summary["applied"] == 1
    assert summary["source_copilots"] == ["dataops"]


def test_empty_registry_returns_zero_summary(tmp_path) -> None:
    scorer = _scorer(tmp_path)
    before = scorer.gae_scorer.centroids.copy()

    summary = scorer.warm_start(SharedPatternRegistry())

    assert summary == {"applied": 0, "score": 0.0, "source_copilots": []}
    assert np.array_equal(scorer.gae_scorer.centroids, before)


def test_scorer_still_scores_after_warm_start(tmp_path) -> None:
    scorer = _scorer(tmp_path)
    factors = {name: 0.5 for name in scorer._preset.shape.factor_names}

    scorer.warm_start([_pattern()])
    result = scorer.score(factors, "price_variance")

    assert result.decision_id
    assert result.action in scorer._preset.shape.action_names


def test_wrong_length_pattern_is_not_counted_as_applied(tmp_path) -> None:
    scorer = _scorer(tmp_path)

    summary = scorer.warm_start([_pattern(delta_length=6)])

    assert summary["applied"] == 0
    assert summary["score"] == 0.0


def test_source_copilots_include_only_applied_patterns(tmp_path) -> None:
    scorer = _scorer(tmp_path)
    skipped = _pattern(
        category="missing_category",
        source_copilot="other_source",
    )

    summary = scorer.warm_start([_pattern(), skipped])
    checkpoint = scorer.graph_store.get_centroid_checkpoints(scorer._domain, limit=1)[0]

    assert summary["applied"] == 1
    assert summary["source_copilots"] == ["dataops"]
    assert "other_source" not in summary["source_copilots"]
    assert checkpoint["metadata"]["source_copilots"] == ["dataops"]


def test_zero_confidence_pattern_is_not_counted_as_applied(tmp_path) -> None:
    scorer = _scorer(tmp_path)

    summary = scorer.warm_start([_pattern(confidence=0.0)])

    assert summary == {"applied": 0, "score": 0.0, "source_copilots": []}
