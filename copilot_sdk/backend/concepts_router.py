"""Versioned narrative concepts used by demo surfaces."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from fastapi import APIRouter, HTTPException


_CONCEPTS: dict[str, dict[str, Any]] = {
    "four-clocks": {
        "concept_id": "four-clocks",
        "title": "The Four Clocks",
        "version": "1.0",
        "content": {
            "clocks": [
                {"name": "State Clock", "measures": "What exists now", "worth": "Operating cost"},
                {"name": "Event Clock", "measures": "What just happened", "worth": "Operating cost"},
                {"name": "Decision Clock", "measures": "What was learned", "worth": "Capital investment"},
                {"name": "Insight Clock", "measures": "What was discovered", "worth": "Capital investment"},
            ],
            "divider": "THE COMPOUNDING DIVIDE",
            "note": "Clocks 1-2 are operating expense. Clocks 3-4 are capital investment.",
        },
    },
    "two-questions": {
        "concept_id": "two-questions",
        "title": "The Two Questions That Separate Surface from Investigation",
        "version": "1.0",
        "content": {
            "questions": [
                {"question": "Does the surface tell you?", "agreement": "~86% on surface-resolvable decisions"},
                {"question": "Does investigation change the answer?", "agreement": "~12% surface vs ~76% geometry on investigation-dependent decisions"},
            ],
            "source": "K14 validation tier experiment, 240 LLM judgments",
            "note": "The gap between 86% and 12% is the K14 blind spot.",
        },
    },
    "retraction-list": {
        "concept_id": "retraction-list",
        "title": "Claims Tested and Withdrawn",
        "version": "1.0",
        "content": {
            "retractions": [
                {"claim": "+28pp with RL in scorer", "status": "WITHDRAWN", "reason": "EXP-RL-SCORER: 3 strategies, none beat uniform eta", "experiment": "EXP-RL-SCORER"},
                {"claim": "AE accelerates d²/dt² beyond logistic baseline", "status": "HYPOTHESIS", "reason": "EXP-AE-SECONDDERIV not yet run", "experiment": "EXP-AE-SECONDDERIV"},
                {"claim": "gamma measured in pilot", "status": "CORRECTED", "reason": "gamma ≈ 1.2 in production-faithful simulation (270 runs); pilot measurement pending", "experiment": "EXP-G1"},
            ],
        },
    },
}


def create_concepts_router() -> APIRouter:
    router = APIRouter(prefix="/api/platform/concepts", tags=["platform-concepts"])

    @router.get("/{concept_id}")
    def concept(concept_id: str) -> dict[str, Any]:
        payload = _CONCEPTS.get(concept_id)
        if payload is None:
            raise HTTPException(status_code=404, detail=f"Unknown concept: {concept_id}")
        return deepcopy(payload)

    return router

