from __future__ import annotations

from app.factors.position_size import PositionSizeFactor


def test_no_context_neutral():
    assert PositionSizeFactor().compute({}) == 0.5


def test_non_dict_neutral():
    assert PositionSizeFactor().compute(object()) == 0.5


def test_size_sweet_spot():
    factor = PositionSizeFactor()

    assert factor.compute({"position_pct_of_max": 0.3}) == 1.0
    assert factor.compute({"position_pct_of_max": 1.0}) == 1.0


def test_size_under_allocated():
    assert round(PositionSizeFactor().compute({"position_pct_of_max": 0.15}), 4) == 0.5


def test_size_oversized():
    factor = PositionSizeFactor()

    assert factor.compute({"position_pct_of_max": 1.5}) == 0.5
    assert factor.compute({"position_pct_of_max": 1.6}) == 0.2


def test_portfolio_concentration_low_good():
    assert PositionSizeFactor().compute({"portfolio_concentration": 0.05}) == 1.0


def test_portfolio_concentration_high_bad():
    assert PositionSizeFactor().compute({"portfolio_concentration": 0.25}) == 0.2


def test_correlated_exposure_inverse():
    assert PositionSizeFactor().compute({"correlated_exposure": 0.25}) == 0.75


def test_kelly_ratio_ideal():
    assert PositionSizeFactor().compute({"kelly_ratio": 1.0}) == 1.0


def test_kelly_ratio_under_over():
    factor = PositionSizeFactor()

    assert factor.compute({"kelly_ratio": 0.5}) == 0.5
    assert factor.compute({"kelly_ratio": 1.5}) == 0.5
    assert factor.compute({"kelly_ratio": 2.0}) == 0.0


def test_combined_high():
    value = PositionSizeFactor().compute(
        {
            "position_pct_of_max": 0.8,
            "portfolio_concentration": 0.05,
            "correlated_exposure": 0.05,
            "kelly_ratio": 1.0,
        }
    )

    assert value >= 0.98


def test_combined_low():
    value = PositionSizeFactor().compute(
        {
            "position_pct_of_max": 1.8,
            "portfolio_concentration": 0.25,
            "correlated_exposure": 0.9,
            "kelly_ratio": 2.0,
        }
    )

    assert value < 0.2


def test_output_bounded():
    value = PositionSizeFactor().compute(
        {"position_pct_of_max": 10, "portfolio_concentration": 10, "correlated_exposure": -10}
    )

    assert 0.0 <= value <= 1.0


def test_position_size_pct_matches_pd_average_and_max_semantics():
    factor = PositionSizeFactor()

    assert factor.compute(
        {
            "position_size_pct": 2.0,
            "avg_position_size_pct": 2.0,
            "max_position_size_pct": 5.0,
        }
    ) == 1.0
    assert factor.compute(
        {
            "position_size_pct": 4.0,
            "avg_position_size_pct": 2.0,
            "max_position_size_pct": 5.0,
        }
    ) == 0.0
    assert factor.compute(
        {
            "position_size_pct": 6.0,
            "avg_position_size_pct": 2.0,
            "max_position_size_pct": 5.0,
        }
    ) == 0.1
