"""Default shadow evaluation for candidate rule variants."""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class DefaultShadowRunner:
    def __init__(self, min_decisions: int = 10) -> None:
        self.min_decisions = int(min_decisions)

    def run_shadow(
        self,
        variant: Any,
        decisions: list[dict[str, Any]],
        baseline: Any | None = None,
    ) -> dict[str, Any]:
        total = len(decisions)
        sufficient = total >= self.min_decisions
        if not sufficient:
            return {
                "sufficient": False,
                "total": total,
                "correct": 0,
                "baseline_correct": 0,
                "accuracy": 0.0,
                "baseline_accuracy": 0.0,
                "errors": 0,
            }

        correct = 0
        baseline_correct = 0
        errors = 0
        for decision in decisions:
            normalized = self._normalize_decision(decision)
            actual = self._actual_action(normalized)
            try:
                if self._predict(variant, normalized) == actual:
                    correct += 1
            except Exception as exc:
                logger.warning("Variant shadow evaluation failed: %s", exc)
                errors += 1
            try:
                baseline_action = (
                    self._predict(baseline, normalized)
                    if baseline is not None
                    else self._baseline_action(normalized)
                )
                if baseline_action == actual:
                    baseline_correct += 1
            except Exception as exc:
                logger.warning("Baseline shadow evaluation failed: %s", exc)
                errors += 1

        return {
            "sufficient": True,
            "total": total,
            "correct": correct,
            "baseline_correct": baseline_correct,
            "accuracy": round(correct / total, 4) if total else 0.0,
            "baseline_accuracy": round(baseline_correct / total, 4) if total else 0.0,
            "errors": errors,
        }

    def _normalize_decision(self, decision: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(decision)
        metadata = normalized.get("metadata")
        if isinstance(metadata, str):
            try:
                normalized["metadata"] = json.loads(metadata)
            except json.JSONDecodeError:
                normalized["metadata"] = {}
        elif metadata is None:
            normalized["metadata"] = {}
        return normalized

    def _actual_action(self, decision: dict[str, Any]) -> Any:
        return (
            decision.get("actual_action")
            or decision.get("recommended_action")
            or decision.get("action")
        )

    def _baseline_action(self, decision: dict[str, Any]) -> Any:
        return decision.get("recommended_action") or decision.get("action")

    def _predict(self, rule: Any, decision: dict[str, Any]) -> Any:
        if rule is None:
            return self._baseline_action(decision)
        if callable(rule):
            return rule(decision)
        for method_name in ("predict", "decide", "action_for"):
            method = getattr(rule, method_name, None)
            if callable(method):
                return method(decision)
        if isinstance(rule, dict):
            return rule.get("recommended_action") or rule.get("action")
        return self._baseline_action(decision)
