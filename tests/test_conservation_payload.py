from __future__ import annotations

from copilot_sdk.scoring.scorer import CompoundingScorer


REQUIRED_KEYS = {
    "status",
    "alpha",
    "q",
    "V",
    "theta_min",
    "signal",
    "headroom",
    "baseline_q",
    "relative_trigger",
    "relative_trigger_ratio",
    "reason",
    "domain",
    "verified_count",
    "correct_count",
    "categories_with_data",
    "total_categories",
}


def _scorer() -> CompoundingScorer:
    return CompoundingScorer.from_preset("dataops", profile="test")


def test_conservation_payload_has_all_required_keys() -> None:
    state = _scorer().get_conservation_state()
    assert REQUIRED_KEYS.issubset(state)


def test_conservation_reason_is_string() -> None:
    reason = _scorer().get_conservation_state()["reason"]
    assert isinstance(reason, str)
    assert len(reason) > 10


def test_conservation_headroom_consistent() -> None:
    state = _scorer().get_conservation_state()
    if state["signal"] is not None and state["theta_min"] is not None:
        assert abs(state["headroom"] - (state["signal"] - state["theta_min"])) < 0.01


def test_conservation_signal_formula() -> None:
    state = _scorer().get_conservation_state()
    if state["alpha"] and state["q"] and state["V"]:
        expected = state["alpha"] * state["q"] * state["V"]
        assert abs(state["signal"] - expected) < 0.1
