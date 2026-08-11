from __future__ import annotations

import pytest

from copilot_sdk.evolution import DefaultPromotionGate


def _shadow():
    return {
        "sufficient": True,
        "total": 20,
        "accuracy": 0.82,
        "baseline_accuracy": 0.70,
        "batch_accuracies": [0.82, 0.82, 0.82],
    }


@pytest.mark.parametrize(
    "conservation_state",
    [
        None,
        {},
        "RED",
        "AMBER",
        "unknown",
        {"status": "RED"},
        {"status": "AMBER"},
        {"status": "unknown"},
        {"state": "AMBER"},
        {"phase": "paused"},
        {"phase": "unknown"},
        {"overallSafe": False},
        {"overall_safe": False},
        {"status": "RED", "overallSafe": True},
        {"state": "AMBER", "overall_safe": True},
        {"phase": "unknown", "overallSafe": True},
    ],
)
def test_unsafe_conservation_blocks_promotion(conservation_state):
    result = DefaultPromotionGate().evaluate(_shadow(), conservation_state=conservation_state)

    assert result["promoted"] is False
    assert result["checks"]["conservation"] is False
    assert result["reason"] == "conservation"


@pytest.mark.parametrize(
    "conservation_state",
    [
        "GREEN",
        "green",
        {"status": "GREEN"},
        {"state": "GREEN"},
        {"phase": "green"},
        {"phase": "verified"},
        {"phase": "active"},
        {"overallSafe": True},
        {"overall_safe": True},
    ],
)
def test_safe_conservation_allows_promotion_when_other_checks_pass(conservation_state):
    result = DefaultPromotionGate().evaluate(_shadow(), conservation_state=conservation_state)

    assert result["promoted"] is True
    assert result["checks"]["conservation"] is True
    assert result["reason"] == "promoted"
