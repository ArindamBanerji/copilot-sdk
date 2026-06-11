from __future__ import annotations

from app.factors.timing_quality import TimingQualityFactor


def test_no_context_neutral():
    assert TimingQualityFactor().compute({}) == 0.5


def test_late_entry_penalty():
    assert TimingQualityFactor().compute({"entry_delay_minutes": 31}) == 0.7
    assert TimingQualityFactor().compute({"entry_delay_minutes": 11}) == 0.9


def test_early_exit_penalty():
    assert TimingQualityFactor().compute({"hold_time_vs_plan_pct": 0.49}) == 0.7
    assert TimingQualityFactor().compute({"hold_time_vs_plan_pct": 0.79}) == 0.9


def test_time_of_day_accuracy_penalty():
    assert TimingQualityFactor().compute({"time_of_day_accuracy": 0.35}) == 0.8
