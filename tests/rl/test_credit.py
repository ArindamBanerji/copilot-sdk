from __future__ import annotations

import pytest

from copilot_sdk.rl import CreditAssigner


def test_uniform_credit():
    assigner = CreditAssigner()

    credit = assigner.assign(0.9, ["a", "b", "c"])

    assert credit == {"a": pytest.approx(0.3), "b": pytest.approx(0.3), "c": pytest.approx(0.3)}


def test_weighted_credit():
    assigner = CreditAssigner()

    credit = assigner.assign(1.0, ["a", "b"], {"a": 3.0, "b": 1.0})

    assert credit["a"] == pytest.approx(0.75)
    assert credit["b"] == pytest.approx(0.25)


def test_temporal_discount():
    assigner = CreditAssigner(temporal_discount=0.5)

    credit = assigner.assign(1.0, ["a", "b"], decision_age=2)

    assert sum(credit.values()) == pytest.approx(0.25)


def test_zero_age():
    assigner = CreditAssigner(temporal_discount=0.5)

    credit = assigner.assign(1.0, ["a"], decision_age=0)

    assert credit["a"] == pytest.approx(1.0)


def test_empty_factors_returns_empty_dict():
    assert CreditAssigner().assign(1.0, []) == {}


def test_dominant_contribution():
    assigner = CreditAssigner()

    credit = assigner.assign(1.0, ["a", "b", "c"], {"a": 0.0, "b": -9.0, "c": 1.0})

    assert credit["b"] == pytest.approx(0.9)
    assert credit["c"] == pytest.approx(0.1)
    assert credit["a"] == pytest.approx(0.0)


def test_negative_reward():
    assigner = CreditAssigner()

    credit = assigner.assign(-1.0, ["a", "b"], {"a": 1.0, "b": 3.0})

    assert credit["a"] == pytest.approx(-0.25)
    assert credit["b"] == pytest.approx(-0.75)


def test_credit_sums_to_base():
    assigner = CreditAssigner(temporal_discount=0.95)
    base = 2.0 * (0.95 ** 3)

    credit = assigner.assign(2.0, ["a", "b", "c"], {"a": 5.0, "b": -2.0, "c": 3.0}, decision_age=3)

    assert sum(credit.values()) == pytest.approx(base)
