from __future__ import annotations

import pytest

from copilot_sdk.evolution import StepCreditAssigner, StepRecord


def _step(step_id: str, timestamp: float) -> StepRecord:
    return StepRecord(step_id=step_id, step_type="decision", timestamp=timestamp)


def test_single_step_gets_full_credit():
    credits = StepCreditAssigner().assign([_step("s1", 100.0)], 2.0)

    assert credits[0].step_id == "s1"
    assert credits[0].credit == pytest.approx(2.0)


def test_chain_discount_favors_most_recent_step():
    chain = [_step("old", 100.0), _step("new", 100.0)]

    credits = StepCreditAssigner(chain_discount=0.5).assign(chain, 1.0)

    assert credits[1].credit > credits[0].credit
    assert sum(credit.credit for credit in credits) == pytest.approx(1.0)


def test_time_decay_reduces_old_steps():
    chain = [_step("old", 70.0), _step("new", 100.0)]

    credits = StepCreditAssigner(half_life=30, chain_discount=1.0).assign(chain, 1.0)

    assert credits[0].decay_factor == pytest.approx(0.5)
    assert credits[1].decay_factor == pytest.approx(1.0)
    assert credits[1].credit > credits[0].credit


def test_half_life_respected():
    chain = [_step("old", 40.0), _step("new", 100.0)]

    credits = StepCreditAssigner(half_life=60, chain_discount=1.0).assign(chain, 1.0)

    assert credits[0].decay_factor == pytest.approx(0.5)


def test_zero_reward_returns_zero_credits():
    credits = StepCreditAssigner().assign([_step("a", 1.0), _step("b", 2.0)], 0.0)

    assert [credit.credit for credit in credits] == [0.0, 0.0]


def test_negative_reward_distributed():
    credits = StepCreditAssigner(chain_discount=1.0).assign([_step("a", 1.0), _step("b", 2.0)], -2.0)

    assert sum(credit.credit for credit in credits) == pytest.approx(-2.0)
    assert all(credit.credit < 0 for credit in credits)


def test_output_order_preserved():
    chain = [_step("first", 10.0), _step("second", 20.0), _step("third", 30.0)]

    credits = StepCreditAssigner().assign(chain, 1.0)

    assert [credit.step_id for credit in credits] == ["first", "second", "third"]


def test_non_positive_half_life_avoids_division_by_zero():
    credits = StepCreditAssigner(half_life=0).assign([_step("a", 1.0), _step("b", 1.0)], 1.0)

    assert sum(credit.credit for credit in credits) == pytest.approx(1.0)
