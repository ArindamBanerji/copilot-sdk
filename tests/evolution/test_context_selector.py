from __future__ import annotations

import pytest

from copilot_sdk.evolution import ContextAwareSelector, SelectionContext


def _context(**overrides):
    data = {
        "category": "payments",
        "recent_accuracy": 0.6,
        "conservation_phase": "A",
        "decision_count": 3,
        "time_of_day": 100.0,
    }
    data.update(overrides)
    return SelectionContext(**data)


def test_select_returns_sole_variant():
    variant = {"variant_id": "only", "win_rate": 0.2}

    assert ContextAwareSelector().select([variant], _context()) is variant


def test_empty_variants_raise():
    with pytest.raises(ValueError, match="variants"):
        ContextAwareSelector().select([], _context())


def test_early_phase_prefers_exploratory_variant():
    variants = [
        {"variant_id": "proven", "win_rate": 0.72, "decision_count": 100},
        {"variant_id": "fresh", "win_rate": 0.50, "decision_count": 0},
    ]

    selected = ContextAwareSelector(exploration_bonus=0.5).select(variants, _context())

    assert selected["variant_id"] == "fresh"


def test_converged_phase_prefers_proven_variant():
    variants = [
        {"variant_id": "fresh", "win_rate": 0.55, "decision_count": 0},
        {"variant_id": "proven", "win_rate": 0.80, "decision_count": 100},
    ]

    selected = ContextAwareSelector(exploration_bonus=1.0).select(
        variants,
        _context(conservation_phase="converged", decision_count=500),
    )

    assert selected["variant_id"] == "proven"


def test_mature_phase_category_evidence_can_change_selection():
    variants = [
        {"variant_id": "global", "win_rate": 0.62, "decision_count": 50},
        {
            "variant_id": "category",
            "win_rate": 0.50,
            "decision_count": 10,
            "category_evidence": {"payments": {"win_rate": 0.9}},
        },
    ]

    selected = ContextAwareSelector().select(
        variants,
        _context(conservation_phase="mature", decision_count=40),
    )

    assert selected["variant_id"] == "category"


def test_failures_downweight_variant_for_same_category():
    selector = ContextAwareSelector(exploration_bonus=0.5)
    variants = [
        {"variant_id": "failed", "win_rate": 0.9, "decision_count": 20},
        {"variant_id": "fallback", "win_rate": 0.7, "decision_count": 20},
    ]

    selector.record_failure("payments", "failed")
    selected = selector.select(variants, _context(conservation_phase="converged", decision_count=500))

    assert selected["variant_id"] == "fallback"


def test_input_variants_not_mutated():
    variants = [
        {"variant_id": "a", "win_rate": 0.1, "decision_count": 0},
        {"variant_id": "b", "win_rate": 0.2, "decision_count": 1},
    ]
    before = [dict(variant) for variant in variants]

    ContextAwareSelector().select(variants, _context())

    assert variants == before
