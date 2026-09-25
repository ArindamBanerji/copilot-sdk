"""Explicit ROI assumptions, never an inferred or measured savings claim."""
from __future__ import annotations

import math
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProjectionInputs(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    setup_cost: float = Field(gt=0)
    weekly_decisions: float = Field(gt=0)
    benefit_per_decision: float = Field(ge=0)
    weekly_operating_cost: float = Field(ge=0)
    required_verified_decisions: int = Field(gt=0)
    provenance: str = Field(min_length=1)


def modeled_projection(inputs: dict[str, Any] | None, verified_count: int) -> dict[str, Any]:
    if inputs is None:
        return {"projected_divergence_week": None, "readiness_score": None,
                "evidence_label": "NOT_CONFIGURED"}
    model = ProjectionInputs.model_validate(inputs)
    net = model.weekly_decisions * model.benefit_per_decision - model.weekly_operating_cost
    return {
        "projected_divergence_week": math.ceil(model.setup_cost / net) if net > 0 else None,
        "readiness_score": min(1.0, max(0, verified_count) / model.required_verified_decisions),
        "evidence_label": "MODELED / PILOT-TARGET — not measured ROI",
        "projection_definition": "First full week cumulative assumed net benefit covers setup cost",
        "projection_inputs": model.model_dump(), "projected_weekly_net_benefit": net,
        "projection_status": "break_even_projected" if net > 0 else "no_break_even",
        "projection_tier": "T-sim", "readiness_definition": "Verified coverage vs configured target; not permission to act",
    }
