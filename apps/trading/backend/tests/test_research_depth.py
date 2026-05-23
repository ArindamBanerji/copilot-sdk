from __future__ import annotations

from app.factors.research_depth import ResearchDepthFactor


def test_no_context_neutral():
    assert ResearchDepthFactor().compute({}) == 0.5


def test_non_dict_neutral():
    assert ResearchDepthFactor().compute(object()) == 0.5


def test_sources_consulted_component():
    assert ResearchDepthFactor().compute({"sources_consulted": 3}) == 0.6


def test_sources_cap_at_five():
    assert ResearchDepthFactor().compute({"sources_consulted": 8}) == 1.0


def test_analysis_minutes_component():
    assert ResearchDepthFactor().compute({"analysis_minutes": 15}) == 0.5


def test_analysis_minutes_cap_at_30():
    assert ResearchDepthFactor().compute({"analysis_minutes": 45}) == 1.0


def test_has_thesis_true():
    assert ResearchDepthFactor().compute({"has_thesis": True}) == 1.0


def test_has_thesis_false():
    assert ResearchDepthFactor().compute({"has_thesis": False}) == 0.3


def test_checklist_completion():
    assert ResearchDepthFactor().compute({"checklist_completed": 3, "checklist_total": 6}) == 0.5


def test_checklist_zero_total_guard():
    assert ResearchDepthFactor().compute({"checklist_completed": 3, "checklist_total": 0}) == 0.5


def test_combined_high():
    value = ResearchDepthFactor().compute(
        {
            "sources_consulted": 5,
            "analysis_minutes": 30,
            "has_thesis": True,
            "checklist_completed": 6,
            "checklist_total": 6,
        }
    )

    assert value == 1.0


def test_combined_low():
    value = ResearchDepthFactor().compute(
        {
            "sources_consulted": 1,
            "analysis_minutes": 3,
            "has_thesis": False,
            "checklist_completed": 1,
            "checklist_total": 6,
        }
    )

    assert round(value, 4) == 0.1917


def test_output_bounded():
    value = ResearchDepthFactor().compute(
        {"sources_consulted": 50, "analysis_minutes": 300, "checklist_completed": 100}
    )

    assert 0.0 <= value <= 1.0
