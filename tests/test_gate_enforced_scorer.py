from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from copilot_sdk.backend.conservation_router import create_conservation_router
from copilot_sdk.backend.conservation_utils import _baseline_q
from copilot_sdk.scoring.composite_gate import CompositeGate
from copilot_sdk.scoring.gate_enforced_scorer import GateEnforcedScorer


class FakeStore:
    def __init__(self, outcomes: list[bool]) -> None:
        self.outcomes = outcomes

    def get_verified_decisions(self, _domain: str) -> list[dict[str, bool]]:
        return [{"is_correct": value} for value in self.outcomes]


class FakeScorer:
    def __init__(self, outcomes: list[bool], state: dict[str, Any]) -> None:
        self.graph_store = FakeStore(outcomes)
        self.state = state
        self.learn_calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def get_conservation_state(self) -> dict[str, Any]:
        return dict(self.state)

    def learn(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.learn_calls.append((args, kwargs))
        return {"learned": True}

    def fingerprint(self) -> dict[str, str]:
        return {"fingerprint": "fake"}

    def get_conservation_state_detail(self) -> str:
        return "delegated"


def _green_state() -> dict[str, Any]:
    return {"status": "GREEN", "signal": 10.0, "theta_min": 1.0, "q": 1.0, "baseline_q": 1.0, "V": 20}


def _amber_state() -> dict[str, Any]:
    return {"status": "GREEN", "signal": 0.1, "theta_min": 1.0, "q": 1.0, "baseline_q": 1.0, "V": 20}


def test_learn_passes_when_gate_green() -> None:
    scorer = FakeScorer([True] * 20, _green_state())
    result = GateEnforcedScorer(scorer, CompositeGate()).learn("d1", "accept")
    assert result["learned"] is True
    assert len(scorer.learn_calls) == 1


def test_learn_blocked_when_gate_amber() -> None:
    scorer = FakeScorer([True] * 20, _amber_state())
    result = GateEnforcedScorer(scorer, CompositeGate()).learn("d1", "accept")
    assert result["blocked_by_gate"] is True
    assert not scorer.learn_calls


def test_learn_blocked_when_gate_red() -> None:
    class RedGate:
        def evaluate(self, **_kwargs: Any) -> dict[str, Any]:
            return {"status": "RED", "g_abs": {"active": True}}

    scorer = FakeScorer([], _green_state())
    result = GateEnforcedScorer(scorer, RedGate()).learn("d1", "accept")
    assert result["blocked_by_gate"] is True
    gate_status = result.get("gate_status")
    assert isinstance(gate_status, dict)
    assert gate_status["status"] == "RED"


def test_gate_returns_status_on_block() -> None:
    scorer = FakeScorer([True] * 20, _amber_state())
    wrapper = GateEnforcedScorer(scorer, CompositeGate())
    result = wrapper.learn("d1", "accept")
    assert result["gate_status"]["status"] == "AMBER"
    assert wrapper.gate_status()["status"] == "AMBER"


def test_outcome_buffered_during_pause() -> None:
    scorer = FakeScorer([True] * 20, _amber_state())
    wrapper = GateEnforcedScorer(scorer, CompositeGate())
    result = wrapper.learn("d1", "accept")
    assert result["buffered_outcomes"] == 1
    assert len(wrapper._outcome_buffer) == 1


def test_buffered_outcomes_replayed_on_recovery() -> None:
    scorer = FakeScorer([True] * 20, _amber_state())
    wrapper = GateEnforcedScorer(scorer, CompositeGate())
    wrapper.learn("d1", "accept")
    scorer.state.update({"signal": 10.0, "status": "GREEN"})
    wrapper.learn("d2", "accept")
    assert len(scorer.learn_calls) == 2
    assert not wrapper._outcome_buffer


def test_delegation_transparent() -> None:
    scorer = FakeScorer([], _green_state())
    wrapper = GateEnforcedScorer(scorer, CompositeGate())
    assert wrapper.get_conservation_state_detail() == "delegated"


def test_fingerprint_delegates() -> None:
    scorer = FakeScorer([], _green_state())
    assert GateEnforcedScorer(scorer, CompositeGate()).fingerprint() == {"fingerprint": "fake"}


def test_conservation_delegates() -> None:
    scorer = FakeScorer([], _green_state())
    assert GateEnforcedScorer(scorer, CompositeGate()).get_conservation_state()["signal"] == 10.0


def test_grel_baseline_not_self() -> None:
    baseline = _baseline_q({"verified_outcomes": [True] * 200}, current_q=0.1)
    assert baseline == 1.0
    assert baseline != 0.1


def test_grel_fires_on_drift() -> None:
    scorer = FakeScorer([True, True, True] + [False] * 17, {**_green_state(), "q": 0.3, "baseline_q": 1.0})
    result = GateEnforcedScorer(scorer, CompositeGate()).learn("d1", "accept")
    assert result["blocked_by_gate"] is True
    assert result["gate_status"]["g_rel"]["active"] is True


def test_overlay_consistency() -> None:
    app = FastAPI()
    app.include_router(
        create_conservation_router(
            "dataops",
            state_provider=lambda: {
                "verified_count": 400,
                "correct_count": 400,
                "total_decisions": 400,
                "baseline_q": 1.0,
                "categories_with_data": 6,
                "total_categories": 6,
                "verified_outcomes": [True] * 380 + [False] * 20,
            },
        )
    )
    payload = TestClient(app).get("/conservation/status").json()
    assert payload["status"] == "AMBER"
    assert payload["passed"] is False
    assert "G_RATE" in payload["reason"]
