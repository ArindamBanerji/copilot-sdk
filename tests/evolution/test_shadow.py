from __future__ import annotations

import logging

from copilot_sdk.evolution import DefaultShadowRunner


class PredictRule:
    def __init__(self, action):
        self.action = action

    def predict(self, decision):
        return self.action


class BadRule:
    def predict(self, decision):
        raise RuntimeError("bad rule")


def _decisions(count=10, actual="accept", baseline="review"):
    return [
        {
            "actual_action": actual,
            "recommended_action": baseline,
            "metadata": '{"ok": true}',
        }
        for _ in range(count)
    ]


def test_shadow_insufficient_decisions():
    runner = DefaultShadowRunner(min_decisions=3)

    result = runner.run_shadow(PredictRule("accept"), _decisions(count=2))

    assert result["sufficient"] is False
    assert result["total"] == 2


def test_shadow_variant_accuracy():
    runner = DefaultShadowRunner(min_decisions=2)

    result = runner.run_shadow(PredictRule("accept"), _decisions(count=4))

    assert result["correct"] == 4
    assert result["accuracy"] == 1.0


def test_shadow_baseline_accuracy_from_decision_action():
    runner = DefaultShadowRunner(min_decisions=2)

    result = runner.run_shadow(PredictRule("accept"), _decisions(count=4))

    assert result["baseline_correct"] == 0
    assert result["baseline_accuracy"] == 0.0


def test_shadow_baseline_rule_used_when_provided():
    runner = DefaultShadowRunner(min_decisions=2)

    result = runner.run_shadow(
        PredictRule("accept"),
        _decisions(count=4),
        baseline=PredictRule("accept"),
    )

    assert result["baseline_correct"] == 4


def test_shadow_actual_falls_back_to_recommended_action():
    runner = DefaultShadowRunner(min_decisions=1)
    decisions = [{"recommended_action": "accept", "metadata": {}}]

    result = runner.run_shadow(PredictRule("accept"), decisions)

    assert result["correct"] == 1


def test_shadow_supports_callable_variant():
    runner = DefaultShadowRunner(min_decisions=1)

    result = runner.run_shadow(lambda decision: "accept", _decisions(count=1))

    assert result["accuracy"] == 1.0


def test_shadow_supports_dict_variant():
    runner = DefaultShadowRunner(min_decisions=1)

    result = runner.run_shadow({"action": "accept"}, _decisions(count=1))

    assert result["accuracy"] == 1.0


def test_shadow_logs_variant_exceptions(caplog):
    runner = DefaultShadowRunner(min_decisions=1)

    with caplog.at_level(logging.WARNING):
        result = runner.run_shadow(BadRule(), _decisions(count=1))

    assert result["errors"] == 1
    assert result["correct"] == 0
    assert "Variant shadow evaluation failed" in caplog.text
