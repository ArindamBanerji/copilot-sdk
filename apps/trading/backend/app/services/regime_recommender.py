"""Detailed regime-context allocation readiness recommendations."""

from __future__ import annotations

from typing import Any


REGIMES = ("trending", "ranging", "volatile")
ACTION_ORDER = {"avoid": 0, "reduce": 1, "hold": 2, "increase": 3}


class RegimeRecommender:
    def recommend(
        self,
        current_regime: str,
        accuracy: dict[str, dict[str, float]],
        conservation_status: Any = None,
    ) -> dict[str, Any]:
        regime = str(current_regime or "ranging")
        conservation_safe = _is_conservation_safe(conservation_status)
        conservation_label = _conservation_label(conservation_status, conservation_safe)
        recommendations = [
            _category_recommendation(category, regime, regimes)
            for category, regimes in sorted(accuracy.items())
        ]
        recommendations = sorted(
            recommendations,
            key=lambda item: (
                ACTION_ORDER.get(str(item["action"]), 99),
                -abs(float(item["delta_pp"])),
                str(item["category"]),
            ),
        )
        transitions = _regime_transitions(accuracy)
        return {
            "regime": regime,
            "recommendations": recommendations,
            "regime_transitions": transitions,
            "conservation_safe": conservation_safe,
            "conservation_status": conservation_label,
            "summary": _summary(recommendations, conservation_safe),
        }


def _category_recommendation(
    category: str,
    current_regime: str,
    regimes: dict[str, float],
) -> dict[str, Any]:
    values = [_to_float(value) for value in regimes.values()]
    values = [value for value in values if value is not None]
    baseline = sum(values) / len(values) if values else 0.5
    current_accuracy = _to_float(regimes.get(current_regime))
    if current_accuracy is None:
        current_accuracy = 0.5
    delta_pp = round((current_accuracy - baseline) * 100, 1)
    spread_pp = round((max(values) - min(values)) * 100, 1) if values else 0.0
    regime_neutral = spread_pp < 5.0

    if current_accuracy < 0.40:
        action = "avoid"
        shift_pct = -100
    elif delta_pp <= -10.0:
        action = "reduce"
        shift_pct = max(-50, int(delta_pp * 2))
    elif delta_pp >= 5.0:
        action = "increase"
        shift_pct = min(30, int(delta_pp * 2))
    else:
        action = "hold"
        shift_pct = 0

    return {
        "category": category,
        "current_regime": current_regime,
        "current_accuracy": round(current_accuracy, 4),
        "baseline_accuracy": round(baseline, 4),
        "delta_pp": delta_pp,
        "action": action,
        "shift_pct": shift_pct,
        "regime_neutral": regime_neutral,
        "rationale": _rationale(category, current_regime, current_accuracy, baseline, delta_pp, action),
    }


def _rationale(
    category: str,
    regime: str,
    current_accuracy: float,
    baseline: float,
    delta_pp: float,
    action: str,
) -> str:
    return (
        f"{category} has {current_accuracy:.0%} verified accuracy in {regime} "
        f"versus {baseline:.0%} baseline; allocation shift action is {action} "
        f"with {delta_pp:+.1f}pp regime context."
    )


def _regime_transitions(accuracy: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    pairs = (("trending", "ranging"), ("trending", "volatile"), ("ranging", "volatile"))
    transitions: list[dict[str, Any]] = []
    for source, target in pairs:
        deltas: list[float] = []
        categories: list[str] = []
        for category, regimes in sorted(accuracy.items()):
            source_value = _to_float(regimes.get(source))
            target_value = _to_float(regimes.get(target))
            if source_value is None or target_value is None:
                continue
            deltas.append((target_value - source_value) * 100)
            categories.append(category)
        avg_delta = round(sum(deltas) / len(deltas), 1) if deltas else 0.0
        transitions.append({
            "from_regime": source,
            "to_regime": target,
            "avg_accuracy_delta_pp": avg_delta,
            "categories_affected": categories,
            "count": len(categories),
        })
    return transitions


def _summary(recommendations: list[dict[str, Any]], conservation_safe: bool) -> str:
    counts = {action: 0 for action in ACTION_ORDER}
    neutral = 0
    for item in recommendations:
        counts[str(item.get("action"))] = counts.get(str(item.get("action")), 0) + 1
        if item.get("regime_neutral") is True:
            neutral += 1
    message = (
        f"{counts['avoid']} avoid, {counts['reduce']} reduce, "
        f"{counts['increase']} increase, {neutral} regime-neutral."
    )
    if not conservation_safe:
        message = f"{message} Conservation not confirmed; treat shifts as informational."
    return message


def _is_conservation_safe(status: Any) -> bool:
    if status is None:
        return False
    if isinstance(status, str):
        return status.strip().upper() == "GREEN"
    if not isinstance(status, dict):
        return False
    status_value = status.get("status")
    if isinstance(status_value, str) and status_value.strip().upper() == "GREEN":
        return True
    state_value = status.get("state")
    if isinstance(state_value, str) and state_value.strip().upper() == "GREEN":
        return True
    phase_value = status.get("phase")
    if isinstance(phase_value, str) and phase_value.strip().lower() in {"green", "verified", "active"}:
        return True
    return status.get("overall_safe") is True or status.get("overallSafe") is True


def _conservation_label(status: Any, safe: bool) -> str:
    if safe:
        return "safe"
    if status is None:
        return "unknown"
    return "unsafe"


def _to_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number
