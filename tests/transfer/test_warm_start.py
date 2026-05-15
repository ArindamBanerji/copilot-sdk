from __future__ import annotations

import numpy as np

from copilot_sdk.transfer import TransferPattern, warm_start_centroids


def _pattern(
    category: str = "cat",
    action: str = "act",
    delta: list[float] | None = None,
    confidence: float = 0.5,
    win_rate: float = 0.8,
) -> TransferPattern:
    return TransferPattern(
        pattern_id="p1",
        source_copilot="source",
        pattern_type="centroid_delta",
        category=category,
        action=action,
        win_rate=win_rate,
        centroid_delta=delta if delta is not None else [1.0, 2.0],
        confidence=confidence,
    )


def test_empty_patterns_returns_copy_and_zero_score() -> None:
    centroids = np.zeros((1, 1, 2))

    updated, score = warm_start_centroids(centroids, [], ["cat"], ["act"])

    assert score == 0.0
    assert np.array_equal(updated, centroids)
    assert updated is not centroids


def test_single_pattern_shifts_expected_centroid() -> None:
    centroids = np.zeros((1, 1, 2))

    updated, score = warm_start_centroids(
        centroids,
        [_pattern(confidence=0.5)],
        ["cat"],
        ["act"],
        blend_weight=0.2,
    )

    assert np.allclose(updated[0, 0, :], [0.1, 0.2])
    assert score == 0.4


def test_unknown_category_is_ignored() -> None:
    centroids = np.zeros((1, 1, 2))

    updated, score = warm_start_centroids(centroids, [_pattern(category="missing")], ["cat"], ["act"])

    assert np.array_equal(updated, centroids)
    assert score == 0.0


def test_unknown_action_is_ignored() -> None:
    centroids = np.zeros((1, 1, 2))

    updated, score = warm_start_centroids(centroids, [_pattern(action="missing")], ["cat"], ["act"])

    assert np.array_equal(updated, centroids)
    assert score == 0.0


def test_wrong_delta_length_is_ignored() -> None:
    centroids = np.zeros((1, 1, 2))

    updated, score = warm_start_centroids(centroids, [_pattern(delta=[1.0])], ["cat"], ["act"])

    assert np.array_equal(updated, centroids)
    assert score == 0.0


def test_blend_weight_scales_delta() -> None:
    centroids = np.zeros((1, 1, 2))

    updated, _score = warm_start_centroids(
        centroids,
        [_pattern(confidence=1.0)],
        ["cat"],
        ["act"],
        blend_weight=0.5,
    )

    assert np.allclose(updated[0, 0, :], [0.5, 1.0])


def test_score_is_bounded() -> None:
    centroids = np.zeros((1, 1, 2))

    _updated, score = warm_start_centroids(
        centroids,
        [_pattern(confidence=2.0, win_rate=2.0)],
        ["cat"],
        ["act"],
    )

    assert score == 1.0


def test_multiple_patterns_accumulate() -> None:
    centroids = np.zeros((1, 1, 2))

    updated, _score = warm_start_centroids(
        centroids,
        [
            _pattern(delta=[1.0, 0.0], confidence=1.0),
            _pattern(delta=[0.0, 2.0], confidence=0.5),
        ],
        ["cat"],
        ["act"],
        blend_weight=0.5,
    )

    assert np.allclose(updated[0, 0, :], [0.5, 0.5])


def test_input_centroids_are_not_mutated() -> None:
    centroids = np.zeros((1, 1, 2))

    warm_start_centroids(centroids, [_pattern()], ["cat"], ["act"])

    assert np.array_equal(centroids, np.zeros((1, 1, 2)))
