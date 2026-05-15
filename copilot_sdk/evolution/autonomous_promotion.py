"""Opt-in autonomous promotion checks layered over shadow promotion data."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, ClassVar


@dataclass(frozen=True)
class PromotionDecision:
    PROMOTE: ClassVar[str] = "promote"
    CONTINUE: ClassVar[str] = "continue"
    BLOCK: ClassVar[str] = "block"

    action: str
    reason: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence", dict(self.evidence or {}))


class AutonomousPromotionGate:
    """GREEN-only autonomous gate for opt-in promotion workflows."""

    def __init__(
        self,
        min_shadow_batches: int = 3,
        min_win_rate: float = 0.7,
        base_gate: Any | None = None,
    ) -> None:
        self.min_shadow_batches = int(min_shadow_batches)
        self.min_win_rate = float(min_win_rate)
        self.base_gate = base_gate

    def evaluate(
        self,
        variant: dict[str, Any],
        conservation_status: str,
        shadow_results: list[dict[str, Any]],
    ) -> PromotionDecision:
        status = str(conservation_status).strip().upper()
        evidence = {
            "variant_id": variant.get("variant_id") or variant.get("id"),
            "conservation_status": status,
            "shadow_batches": len(shadow_results),
        }
        if status != "GREEN":
            return PromotionDecision(PromotionDecision.BLOCK, "conservation", evidence)

        if len(shadow_results) < self.min_shadow_batches:
            return PromotionDecision(PromotionDecision.CONTINUE, "insufficient_shadow_batches", evidence)

        win_rate = _win_rate(variant, shadow_results)
        regressions = _regressions(shadow_results)
        evidence.update(
            {
                "win_rate": win_rate,
                "min_win_rate": self.min_win_rate,
                "regressions": regressions,
            }
        )

        if regressions:
            return PromotionDecision(PromotionDecision.CONTINUE, "regression", evidence)
        if win_rate < self.min_win_rate:
            return PromotionDecision(PromotionDecision.CONTINUE, "win_rate", evidence)

        if self.base_gate is not None:
            base_decision = _evaluate_base_gate(self.base_gate, shadow_results, status)
            evidence["base_gate"] = base_decision
            if not bool(base_decision.get("promoted", True)):
                return PromotionDecision(
                    PromotionDecision.CONTINUE,
                    str(base_decision.get("reason") or "base_gate"),
                    evidence,
                )

        return PromotionDecision(PromotionDecision.PROMOTE, "criteria_met", evidence)


def _win_rate(variant: dict[str, Any], shadow_results: list[dict[str, Any]]) -> float:
    wins = 0
    total = 0
    for result in shadow_results:
        if "better" in result:
            wins += 1 if bool(result["better"]) else 0
            total += 1
        elif "win" in result:
            wins += 1 if bool(result["win"]) else 0
            total += 1
        elif "is_win" in result:
            wins += 1 if bool(result["is_win"]) else 0
            total += 1
        elif "accuracy" in result and "baseline_accuracy" in result:
            wins += 1 if float(result["accuracy"]) > float(result["baseline_accuracy"]) else 0
            total += 1
    if total:
        return wins / total
    if "win_rate" in variant:
        return float(variant["win_rate"])
    return 0.0


def _regressions(shadow_results: list[dict[str, Any]]) -> list[int]:
    regressions = []
    for index, result in enumerate(shadow_results):
        if bool(result.get("regression")):
            regressions.append(index)
        elif "accuracy" in result and "baseline_accuracy" in result:
            if float(result["accuracy"]) < float(result["baseline_accuracy"]):
                regressions.append(index)
    return regressions


def _evaluate_base_gate(
    base_gate: Any,
    shadow_results: list[dict[str, Any]],
    conservation_status: str,
) -> dict[str, Any]:
    evaluate = getattr(base_gate, "evaluate", None)
    if not callable(evaluate):
        return {"promoted": True}

    aggregate = {
        "sufficient": True,
        "total": len(shadow_results),
        "accuracy": sum(float(item.get("accuracy", 0.0)) for item in shadow_results) / len(shadow_results),
        "baseline_accuracy": sum(float(item.get("baseline_accuracy", 0.0)) for item in shadow_results) / len(shadow_results),
        "batch_accuracies": [float(item.get("accuracy", 0.0)) for item in shadow_results],
    }
    return dict(evaluate(aggregate, conservation_state={"status": conservation_status}))
