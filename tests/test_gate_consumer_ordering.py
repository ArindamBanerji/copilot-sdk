"""Gate trailing windows must not depend on backend read presentation."""

from copy import deepcopy
from types import SimpleNamespace
from typing import Any

import pytest

from copilot_sdk.scoring.composite_gate import (
    CompositeGate,
    chronological_decisions,
    outcomes_from_state,
)
from copilot_sdk.scoring.gate_enforced_scorer import GateEnforcedScorer


@pytest.mark.parametrize("newest_first", [False, True])
@pytest.mark.parametrize("recovered", [False, True])
def test_gate_consumers_measure_latest_window(newest_first: bool, recovered: bool) -> None:
    outcomes = [True] * 80 + [False] * 20 + ([True] * 20 if recovered else [])
    rows = [
        {"decision_id": f"d{index:03d}", "created_at": float(index + 1), "is_correct": correct}
        for index, correct in enumerate(outcomes)
    ]
    if newest_first:
        rows.reverse()
    original = deepcopy(rows)
    store = SimpleNamespace(get_verified_decisions=lambda domain: rows)
    state = SimpleNamespace(graph_store=store, domain="test")
    extracted = outcomes_from_state(state)
    assert extracted == outcomes
    measured = CompositeGate().evaluate(
        alpha_q_v=100.0, theta_min=1.0, rolling_accuracy=sum(outcomes) / len(outcomes),
        baseline=0.8, verified_outcomes=extracted,
    )
    assert measured["g_rate"]["active"] is (not recovered)
    assert measured["g_rate"]["short_accuracy"] == (1.0 if recovered else 0.0)

    learned: list[str] = []

    def learn(decision_id: str) -> dict[str, bool]:
        learned.append(decision_id)
        return {"learned": True}

    scorer = SimpleNamespace(
        graph_store=store, domain="test", learn=learn,
        get_conservation_state=lambda: {"signal": 100.0, "theta_min": 1.0, "V": len(rows), "baseline_q": 0.8},
    )
    wrapper = GateEnforcedScorer(scorer, CompositeGate())
    result = wrapper.learn("new-decision")
    status = wrapper.gate_status()
    assert status is not None
    assert status["g_rate"]["active"] is (not recovered)
    if recovered:
        assert result == {"learned": True}
        assert learned == ["new-decision"]
    else:
        assert result["blocked_by_gate"] is True
        assert learned == []
    assert rows == original


def test_chronological_decisions_ties_use_id() -> None:
    rows = [
        {"created_at": 2.0, "decision_id": "z"},
        {"created_at": 1.0, "decision_id": "b"},
        {"created_at": 1.0, "decision_id": "a"},
    ]
    assert [row["decision_id"] for row in chronological_decisions(rows)] == ["a", "b", "z"]
    assert rows[0]["decision_id"] == "z"


def test_gate_consumers_preserve_untimed_legacy_order() -> None:
    rows: list[dict[str, Any]] = [{"is_correct": True}, {"is_correct": False}]
    store = SimpleNamespace(get_verified_decisions=lambda domain: rows)
    state = SimpleNamespace(graph_store=store, domain="test")
    assert outcomes_from_state(state) == [True, False]
    assert GateEnforcedScorer(state, CompositeGate())._get_recent_outcomes() == [True, False]
    assert chronological_decisions([True, False]) == [True, False]


def test_explicit_outcome_stream_keeps_caller_order() -> None:
    assert outcomes_from_state({"verified_outcomes": [True, False, True]}) == [True, False, True]


def test_empty_decision_stream() -> None:
    assert chronological_decisions([]) == []
    state = SimpleNamespace(graph_store=SimpleNamespace(get_verified_decisions=lambda domain: []))
    assert outcomes_from_state(state) == []
    assert GateEnforcedScorer(state, CompositeGate())._get_recent_outcomes() == []
