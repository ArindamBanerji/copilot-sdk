from dataclasses import dataclass

from copilot_sdk.di import DataValuationEngine, DOMAIN_DECISION_VALUES


@dataclass(frozen=True)
class Candidate:
    factor_a: str
    factor_b: str
    lift_pp: float
    correlation: float = 0.8
    sample_size: int = 100
    description: str = "Customer orders x weather"


def test_valuate_basic():
    valuation = DataValuationEngine("purchasing").valuate_single(15, decisions_per_year=10000)
    assert valuation.annual_value == 12600.0


def test_conservative_70():
    engine = DataValuationEngine("purchasing")
    assert engine.valuate_single(100, decisions_per_year=1).annual_value == 8.4


def test_domain_soc_85():
    assert DOMAIN_DECISION_VALUES["soc"] == 85.0


def test_domain_purchasing_12():
    assert DOMAIN_DECISION_VALUES["purchasing"] == 12.0


def test_custom_value():
    valuation = DataValuationEngine("unknown", custom_value=100).valuate_single(10, decisions_per_year=10)
    assert valuation.annual_value == 70.0


def test_report_sorted():
    report = DataValuationEngine("dataops", decisions_per_year=1000).valuate([
        Candidate("a", "b", 5),
        Candidate("a", "c", 15),
    ])
    assert report.valuations[0].annual_value > report.valuations[1].annual_value


def test_top_combination():
    report = DataValuationEngine("dataops", decisions_per_year=1000).valuate([
        Candidate("a", "b", 5),
        Candidate("a", "c", 15),
    ])
    assert report.top_combination == report.valuations[0]


def test_estimate_annual():
    decisions = [{"id": index} for index in range(90)]
    assert DataValuationEngine("dataops").estimate_annual_decisions(decisions) == 360


def test_payback_period():
    engine = DataValuationEngine("dataops")
    valuation = engine.valuate_single(100, decisions_per_year=527.4725274725)
    valued = engine.with_acquisition_cost(valuation, 10000)
    assert valued.payback_months == 5.0


def test_zero_improvement():
    assert DataValuationEngine("dataops").valuate_single(0, decisions_per_year=1000).annual_value == 0.0


def test_empty_candidates():
    report = DataValuationEngine("dataops").valuate([])
    assert report.valuations == []
    assert report.top_combination is None


def test_narrative_present():
    valuation = DataValuationEngine("dataops").valuate_single(15, decisions_per_year=1000, factor_a="orders", factor_b="weather")
    assert "narrative" in valuation.to_dict()
    assert "$" in valuation.narrative


def test_negative_improvement_clamped():
    valuation = DataValuationEngine("dataops").valuate_single(-5, decisions_per_year=1000)
    assert valuation.improvement_pp == 0.0
    assert valuation.annual_value == 0.0


def test_extreme_improvement_clamped():
    valuation = DataValuationEngine("purchasing").valuate_single(150, decisions_per_year=10)
    assert valuation.improvement_pp == 100.0
    assert valuation.annual_value == 84.0


def test_zero_cost_payback_none():
    engine = DataValuationEngine("dataops")
    valuation = engine.valuate_single(10, decisions_per_year=1000)
    valued = engine.with_acquisition_cost(valuation, 0)
    assert valued.payback_months is None


def test_narrative_mentions_conservative():
    valuation = DataValuationEngine("dataops").valuate_single(15, decisions_per_year=1000)
    assert "conservative" in valuation.narrative
    assert "70%" in valuation.narrative
