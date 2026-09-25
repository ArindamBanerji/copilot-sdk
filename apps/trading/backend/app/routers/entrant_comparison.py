"""Read-only incumbent versus entrant comparison for Trading demos."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter


ScorerProvider = Callable[[], Any]


def create_entrant_comparison_router(scorer_provider: ScorerProvider) -> APIRouter:
    router = APIRouter(prefix="/api/trading", tags=["trading-entrant-comparison"])

    @router.get("/entrant-comparison")
    def entrant_comparison() -> dict[str, Any]:
        scorer = scorer_provider()
        fingerprint = scorer.fingerprint()
        accuracy = float(getattr(fingerprint, "overall_win_rate", 0.0) or 0.0)
        decisions = int(getattr(fingerprint, "decisions_analyzed", 0) or 0)
        baseline = 0.5
        gap = (accuracy - baseline) * 100.0
        trajectory = scorer.trajectory()
        iks = float(getattr(trajectory, "current_iks", 0.0) or 0.0)
        return {
            "incumbent": {
                "verified_decisions": decisions,
                "accuracy": accuracy,
                "iks": iks,
                "warm_start_advantage_pp": round(gap, 4),
            },
            "entrant": {
                "verified_decisions": 0,
                "accuracy": baseline,
                "iks": 0.0,
                "warm_start_advantage_pp": 0.0,
            },
            "gap": {
                "accuracy_pp": round(gap, 4),
                "decisions_accumulated": decisions,
                "baseline_source": "assumed_default",
                "note": f"Incumbent is {gap:+.1f}pp versus the assumed baseline from {decisions} verified decisions. Entrant starts from baseline.",
            },
        }

    return router
