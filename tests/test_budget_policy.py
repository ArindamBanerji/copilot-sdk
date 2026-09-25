"""Tests for the adaptive investigation budget policy."""

import pytest

from copilot_sdk.scoring.budget_policy import MAX_HISTORY, AdaptiveBudgetPolicy


def test_cold_start_default() -> None:
    policy = AdaptiveBudgetPolicy()
    assert policy.allocate(0.10, "s2p", verified_count=29) == 2
    assert policy.get_stats()["decisions"] == 0


def test_high_confidence_low_reads() -> None:
    policy = AdaptiveBudgetPolicy()
    assert policy.allocate(0.90, "s2p", verified_count=30) == 1


def test_low_confidence_high_reads() -> None:
    policy = AdaptiveBudgetPolicy()
    assert policy.allocate(0.50, "s2p", verified_count=30) == 4


def test_medium_confidence_default() -> None:
    policy = AdaptiveBudgetPolicy()
    assert policy.allocate(0.75, "s2p", verified_count=30) == 2


def test_stats_empty() -> None:
    policy = AdaptiveBudgetPolicy(safety_lambda=0.0)
    assert policy.get_stats() == {
        "controller": "adaptive",
        "decisions": 0,
        "safety_lambda": 0.0,
        "mean_reads_easy": None,
        "mean_reads_hard": None,
        "total_reads_saved": 0,
        "easy_count": 0,
        "hard_count": 0,
    }


def test_cold_stats_has_all_fields() -> None:
    assert len(AdaptiveBudgetPolicy().get_stats()) == 8


def test_warm_stats_has_all_fields() -> None:
    policy = AdaptiveBudgetPolicy()
    policy.allocate(0.90, "s2p", verified_count=30)
    assert len(policy.get_stats()) == 8


def test_cold_warm_same_keys() -> None:
    policy = AdaptiveBudgetPolicy()
    cold = policy.get_stats()
    policy.allocate(0.90, "s2p", verified_count=30)
    assert cold.keys() == policy.get_stats().keys()


def test_stats_after_decisions() -> None:
    policy = AdaptiveBudgetPolicy()
    policy.allocate(0.90, "s2p", verified_count=30)
    policy.allocate(0.50, "s2p", verified_count=30)
    stats = policy.get_stats()
    assert stats["decisions"] == 2
    assert stats["easy_count"] == 1
    assert stats["hard_count"] == 1


def test_reads_saved_positive() -> None:
    policy = AdaptiveBudgetPolicy()
    policy.allocate(0.90, "s2p", verified_count=30)
    policy.allocate(0.90, "s2p", verified_count=30)
    assert policy.get_stats()["total_reads_saved"] == 2


def test_safety_lambda_stored() -> None:
    policy = AdaptiveBudgetPolicy(safety_lambda=0.0)
    assert policy.safety_lambda == 0.0


def test_invalid_budget_order_rejected() -> None:
    with pytest.raises(ValueError):
        AdaptiveBudgetPolicy(min_reads=3, default_reads=2)


def test_history_bounded() -> None:
    policy = AdaptiveBudgetPolicy()
    for index in range(300):
        policy.allocate(0.90, f"category-{index}", verified_count=30)
    assert len(policy._history) == MAX_HISTORY


def test_stats_with_bounded_history_preserve_lifetime_aggregates() -> None:
    policy = AdaptiveBudgetPolicy()
    for index in range(300):
        confidence = 0.90 if index % 2 == 0 else 0.50
        policy.allocate(confidence, "s2p", verified_count=30)
    stats = policy.get_stats()
    assert len(policy._history) == MAX_HISTORY
    assert stats["decisions"] == 300
    assert stats["easy_count"] == 150
    assert stats["hard_count"] == 150
    assert stats["mean_reads_easy"] == 1
    assert stats["mean_reads_hard"] == 4
    assert stats["total_reads_saved"] == -150


def test_history_trim_is_fifo() -> None:
    policy = AdaptiveBudgetPolicy()
    for index in range(MAX_HISTORY + 2):
        policy.allocate(0.75, f"category-{index}", verified_count=30)
    assert policy._history[0]["category"] == "category-2"
    assert policy._history[-1]["category"] == f"category-{MAX_HISTORY + 1}"
