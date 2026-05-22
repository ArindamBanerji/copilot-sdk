from __future__ import annotations

from app.factors.conviction import ConvictionFactor


def test_no_context_returns_neutral():
    assert ConvictionFactor().compute({}) == 0.5


def test_non_dict_returns_neutral():
    assert ConvictionFactor().compute(object()) == 0.5


def test_signals_all_confirmed():
    value = ConvictionFactor().compute(
        {"tagged_signals": [{"confirmed": True}, {"confirmed": True}]}
    )

    assert value == 1.0


def test_signals_none_confirmed():
    value = ConvictionFactor().compute(
        {"tagged_signals": [{"confirmed": False}, {"confirmed": False}]}
    )

    assert value == 0.0


def test_signals_partial():
    value = ConvictionFactor().compute(
        {"tagged_signals": [{"confirmed": True}, {"confirmed": False}]}
    )

    assert value == 0.5


def test_plan_true():
    assert ConvictionFactor().compute({"has_trade_plan": True}) == 1.0


def test_plan_false():
    assert ConvictionFactor().compute({"has_trade_plan": False}) == 0.3


def test_conviction_high_low_clamped():
    factor = ConvictionFactor()

    assert factor.compute({"position_conviction": 0.9}) == 0.9
    assert factor.compute({"position_conviction": 0.2}) == 0.2
    assert factor.compute({"position_conviction": 1.8}) == 1.0


def test_sizing_normal_oversized_undersized():
    factor = ConvictionFactor()

    assert factor.compute({"size_vs_rolling_avg": 1.0}) == 0.8
    assert factor.compute({"size_vs_rolling_avg": 1.8}) == 0.5
    assert factor.compute({"size_vs_rolling_avg": 0.5}) == 0.6


def test_multi_component_averaging():
    value = ConvictionFactor().compute(
        {
            "tagged_signals": [{"confirmed": True}, {"confirmed": False}],
            "has_trade_plan": True,
            "position_conviction": 0.7,
            "size_vs_rolling_avg": 1.0,
        }
    )

    assert value == 0.75


def test_result_bounded():
    value = ConvictionFactor().compute(
        {
            "has_trade_plan": True,
            "position_conviction": 10.0,
            "size_vs_rolling_avg": 1.0,
        }
    )

    assert 0.0 <= value <= 1.0
