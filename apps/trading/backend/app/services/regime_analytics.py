"""Read-only per-regime decision quality analytics."""

from __future__ import annotations

from collections import defaultdict
from typing import Any


CANONICAL_REGIMES = ("trending", "volatile", "ranging")
MEASURED_THRESHOLD = 30
IKS_COVERAGE_TARGET = 200


class RegimeAnalytics:
    """Compute per-regime accuracy, IKS, conservation from tagged decisions.

    ZERO writes to scorer centroids. Read-only aggregation.
    """

    def __init__(self, regimes: tuple[str, ...] = CANONICAL_REGIMES) -> None:
        self._regimes = tuple(regimes)

    def compute(self, decisions: list[dict[str, Any]]) -> dict[str, Any]:
        """Group decisions by regime, compute stats per group."""

        by_regime: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
        for decision in decisions:
            by_regime[_decision_regime(decision)].append(decision)

        regime_names = list(self._regimes)
        for regime in sorted(by_regime):
            if regime not in regime_names:
                regime_names.append(regime)

        regime_stats = {}
        for regime in regime_names:
            group = by_regime.get(regime, [])
            verified = [decision for decision in group if _is_verified(decision)]
            correct = [decision for decision in verified if _is_correct(decision)]
            conservation_values = [_conservation_safe(decision) for decision in group]
            conservation_known = [value for value in conservation_values if value is not None]
            verified_count = len(verified)
            accuracy = len(correct) / verified_count if verified_count > 0 else None
            measured = verified_count >= MEASURED_THRESHOLD
            iks = accuracy * min(verified_count / IKS_COVERAGE_TARGET, 1.0) if measured and accuracy is not None else None
            conservation_safe_count = sum(1 for value in conservation_known if value)
            conservation_rate = (
                conservation_safe_count / len(conservation_known)
                if conservation_known
                else None
            )

            regime_stats[regime] = {
                "regime": regime,
                "decision_count": len(group),
                "verified_count": verified_count,
                "accuracy": round(accuracy, 3) if accuracy is not None else None,
                "iks_proxy": round(iks, 3) if iks is not None else None,
                "conservation_count": len(conservation_known),
                "conservation_safe_count": conservation_safe_count,
                "conservation_rate": round(conservation_rate, 3) if conservation_rate is not None else None,
                "measurement_state": "measured" if measured else "accumulating",
                "provenance": "real_measured" if measured else "accumulating",
            }

        return {
            "regimes": regime_stats,
            "total_decisions": sum(len(group) for group in by_regime.values()),
            "regime_count": len(regime_stats),
        }


def _decision_regime(decision: dict[str, Any]) -> str:
    for context_key in ("regime_context", "regime_metadata"):
        context = decision.get(context_key)
        if isinstance(context, dict) and context.get("regime"):
            return _clean_regime(context.get("regime"))

    metadata = decision.get("metadata")
    if isinstance(metadata, dict):
        context = metadata.get("regime_metadata") or metadata.get("regime_context")
        if isinstance(context, dict) and context.get("regime"):
            return _clean_regime(context.get("regime"))

    factors = decision.get("factors")
    if isinstance(factors, dict):
        factor_metadata = factors.get("metadata")
        if isinstance(factor_metadata, dict):
            context = factor_metadata.get("regime_metadata") or factor_metadata.get("regime_context")
            if isinstance(context, dict) and context.get("regime"):
                return _clean_regime(context.get("regime"))

    return "unknown"


def _clean_regime(value: Any) -> str:
    text = str(value or "").strip().lower()
    return text or "unknown"


def _is_verified(decision: dict[str, Any]) -> bool:
    if decision.get("verified") is True:
        return True
    if decision.get("verified_at") is not None:
        return True
    if decision.get("outcome_correct") is not None or decision.get("is_correct") is not None:
        return True
    return str(decision.get("status") or "").lower() in {"confirmed", "overridden"}


def _is_correct(decision: dict[str, Any]) -> bool:
    if "outcome_correct" in decision:
        return bool(decision.get("outcome_correct"))
    return bool(decision.get("is_correct"))


def _conservation_safe(decision: dict[str, Any]) -> bool | None:
    for key in ("conservation_safe", "conservationSafe"):
        if key in decision:
            return bool(decision.get(key))

    status = _nested_value(
        decision,
        (
            ("conservation_status",),
            ("conservationStatus",),
            ("conservation", "status"),
            ("metadata", "conservation_status"),
            ("metadata", "conservationStatus"),
            ("metadata", "conservation", "status"),
            ("factors", "metadata", "conservation_status"),
            ("factors", "metadata", "conservationStatus"),
            ("factors", "metadata", "conservation", "status"),
        ),
    )
    if status is None:
        return None

    normalized = str(status).strip().lower()
    if normalized in {"green", "safe", "pass", "passed", "ok"}:
        return True
    if normalized in {"red", "unsafe", "fail", "blocked"}:
        return False
    return None


def _nested_value(decision: dict[str, Any], paths: tuple[tuple[str, ...], ...]) -> Any:
    for path in paths:
        value: Any = decision
        for part in path:
            if not isinstance(value, dict) or part not in value:
                value = None
                break
            value = value[part]
        if value is not None:
            return value
    return None
