"""DataOps intelligence views backed by the application's selected scorer/store."""

from dataclasses import asdict
from typing import Any, Callable

from fastapi import APIRouter

from ..services.source_trust import compute_source_trust
from copilot_sdk.graph.protocol import GraphStore
from copilot_sdk.scoring.scorer import CompoundingScorer


def create_intelligence_router(
    scorer_provider: Callable[[], CompoundingScorer],
    graph_store_provider: Callable[[], GraphStore],
) -> APIRouter:
    router = APIRouter(prefix="/api/dataops/intelligence", tags=["intelligence"])

    @router.get("/source-trust")
    def source_trust() -> list[dict[str, Any]]:
        """Relative source-group trust from DK weights; unmapped systems are neutral."""
        results = compute_source_trust(scorer_provider(), graph_store_provider(), "dataops")
        return [
            {**asdict(row), "provenance": "DK weights from verified decisions"}
            for row in results
        ]

    return router
