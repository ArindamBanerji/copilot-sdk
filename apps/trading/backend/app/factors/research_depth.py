"""Research depth factor computer."""

from __future__ import annotations

from typing import Any

from app.factors.base import clamp, mean_or_neutral


class ResearchDepthFactor:
    factor_name = "market_regime"
    factor_index = 1

    def compute(self, event: object) -> float:
        ctx = event if isinstance(event, dict) else {}
        if not ctx:
            return 0.5

        components: list[float] = []

        if "sources_consulted" in ctx:
            components.append(_scaled_score(ctx.get("sources_consulted"), 5.0))

        if "analysis_minutes" in ctx:
            components.append(_scaled_score(ctx.get("analysis_minutes"), 30.0))

        if "has_thesis" in ctx:
            components.append(1.0 if bool(ctx.get("has_thesis")) else 0.3)

        if "checklist_completed" in ctx:
            components.append(
                _checklist_score(ctx.get("checklist_completed"), ctx.get("checklist_total", 6))
            )

        return mean_or_neutral(components)


def _scaled_score(value: Any, denominator: float) -> float:
    try:
        return clamp(float(value) / denominator)
    except (TypeError, ValueError):
        return 0.5


def _checklist_score(completed_value: Any, total_value: Any) -> float:
    try:
        completed = float(completed_value)
        total = float(total_value)
    except (TypeError, ValueError):
        return 0.5
    return clamp(completed / total) if total > 0 else 0.5
