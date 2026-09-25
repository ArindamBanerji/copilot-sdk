from __future__ import annotations

from copilot_sdk.evolution import DefaultPromotionGate


def _shadow(**overrides):
    data = {
        "sufficient": True,
        "total": 2_000,
        "correct": 1_640,
        "baseline_correct": 1_400,
        "accuracy": 0.82,
        "baseline_accuracy": 0.70,
        "batch_accuracies": [0.82, 0.82, 0.82],
    }
    data.update(overrides)
    return data


def test_gate_promotes_when_checks_pass():
    result = DefaultPromotionGate().evaluate(_shadow(), conservation_state={"status": "GREEN"})

    assert result["promoted"] is True
    assert result["reason"] == "promoted"
    assert result["failed_checks"] == []


def test_gate_rejects_insufficient_data():
    result = DefaultPromotionGate().evaluate(
        _shadow(sufficient=False, total=4),
        conservation_state={"status": "GREEN"},
    )

    assert result["promoted"] is False
    assert result["reason"] == "sufficient_data"


def test_gate_rejects_low_superiority():
    result = DefaultPromotionGate().evaluate(
        _shadow(accuracy=0.73, baseline_accuracy=0.70),
        conservation_state={"status": "GREEN"},
    )

    assert result["promoted"] is False
    assert result["reason"] == "practical_significance"


def test_gate_rejects_below_accuracy_floor():
    result = DefaultPromotionGate().evaluate(
        _shadow(accuracy=0.69, baseline_accuracy=0.50),
        conservation_state={"status": "GREEN"},
    )

    assert result["promoted"] is False
    assert result["reason"] == "accuracy_floor"


def test_gate_red_conservation_blocks():
    result = DefaultPromotionGate().evaluate(_shadow(), conservation_state={"status": "RED"})

    assert result["promoted"] is False
    assert result["reason"] == "conservation"


def test_gate_amber_conservation_blocks():
    result = DefaultPromotionGate().evaluate(_shadow(), conservation_state={"status": "AMBER"})

    assert result["checks"]["conservation"] is False
    assert result["promoted"] is False
    assert result["reason"] == "conservation"


def test_gate_variance_blocks_when_high():
    result = DefaultPromotionGate().evaluate(
        _shadow(batch_accuracies=[0.95, 0.50, 0.95, 0.50]),
        conservation_state={"status": "GREEN"},
    )

    assert result["promoted"] is False
    assert result["reason"] == "variance"


def test_gate_reports_metrics():
    result = DefaultPromotionGate().evaluate(_shadow(), conservation_state={"status": "GREEN"})

    assert result["accuracy"] == 0.82
    assert result["baseline_accuracy"] == 0.7
    assert result["superiority_pp"] == 12.0
    assert result["total"] == 2_000
    assert result["p_value"] is not None


def test_gate_custom_thresholds():
    gate = DefaultPromotionGate(superiority_threshold_pp=15.0, accuracy_floor=0.80)

    result = gate.evaluate(_shadow(), conservation_state={"status": "GREEN"})

    assert result["promoted"] is False
    assert result["reason"] == "practical_significance"


def test_gate_reports_all_failed_checks():
    result = DefaultPromotionGate().evaluate(
        _shadow(
            sufficient=False,
            total=2,
            accuracy=0.40,
            baseline_accuracy=0.50,
            batch_accuracies=[0.95, 0.40, 0.95],
        ),
        conservation_state={"status": "RED"},
    )

    assert result["promoted"] is False
    assert result["failed_checks"] == [
        "sufficient_data",
        "statistical_significance",
        "practical_significance",
        "accuracy_floor",
        "conservation",
        "variance",
    ]


def test_gate_rejects_practically_large_but_statistically_weak_result():
    result = DefaultPromotionGate(min_shadow_decisions=10).evaluate(
        _shadow(
            total=10,
            correct=8,
            baseline_correct=7,
            accuracy=0.80,
            baseline_accuracy=0.70,
        ),
        conservation_state={"status": "GREEN"},
    )

    assert result["promoted"] is False
    assert result["checks"]["practical_significance"] is True
    assert result["checks"]["statistical_significance"] is False
