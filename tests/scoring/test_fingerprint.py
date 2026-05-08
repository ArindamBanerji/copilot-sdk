from __future__ import annotations

from copilot_sdk.scoring.fingerprint import compute_fingerprint


FACTOR_NAMES = ["amount", "risk", "history"]


def decision(category, vector, is_correct):
    return {
        "category": category,
        "factor_vector": vector,
        "is_correct": is_correct,
    }


def varied_decisions():
    return [
        decision("alpha", [0.10, 0.20, 0.30], True),
        decision("alpha", [0.11, 0.30, 0.50], True),
        decision("alpha", [0.12, 0.40, 0.70], False),
        decision("beta", [0.50, 0.20, 0.20], True),
        decision("beta", [0.51, 0.35, 0.40], False),
        decision("beta", [0.52, 0.50, 0.60], True),
    ]


def test_insufficient_data_returns_defaults():
    result = compute_fingerprint(varied_decisions()[:4], FACTOR_NAMES)

    assert result.decisions_analyzed == 4
    assert result.overall_win_rate == 0.0
    assert result.per_category_precision == {}
    assert all(f.sigma == 0.5 for f in result.factors)
    assert all(f.weight == 0.0 for f in result.factors)
    assert all(f.interpretation == "insufficient data" for f in result.factors)


def test_fingerprint_has_all_factors():
    result = compute_fingerprint(varied_decisions(), FACTOR_NAMES)

    assert [f.name for f in result.factors] == FACTOR_NAMES
    assert result.decisions_analyzed == 6


def test_sigma_positive():
    result = compute_fingerprint(varied_decisions(), FACTOR_NAMES)

    assert all(f.sigma >= 0.01 for f in result.factors)


def test_weights_between_zero_and_one_and_max_one():
    result = compute_fingerprint(varied_decisions(), FACTOR_NAMES)
    weights = [f.weight for f in result.factors]

    assert all(0.0 <= weight <= 1.0 for weight in weights)
    assert max(weights) == 1.0


def test_per_category_precision_for_categories_with_at_least_three():
    result = compute_fingerprint(varied_decisions(), FACTOR_NAMES)

    assert result.per_category_precision == {
        "alpha": 0.667,
        "beta": 0.667,
    }
    assert result.overall_win_rate == 0.667


def test_category_with_less_than_three_is_omitted():
    decisions = varied_decisions() + [decision("gamma", [0.1, 0.1, 0.1], True)]

    result = compute_fingerprint(decisions, FACTOR_NAMES)

    assert "gamma" not in result.per_category_precision
