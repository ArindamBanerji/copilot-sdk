"""DataOps cohort status API."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, cast

from fastapi import APIRouter

from app.services.cohort_status import CohortStatusService


def create_cohort_status_router(
    graph_store_factory: Callable[[], Any] | None = None,
    oracle_artifact_path: str | Path | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/dataops", tags=["cohort-status"])

    @router.get("/cohort-status")
    def get_cohort_status() -> dict[str, Any]:
        store = graph_store_factory() if graph_store_factory is not None else None
        payload = CohortStatusService(
            graph_store=store,
            oracle_artifact_path=oracle_artifact_path,
        ).get_status()
        return cast(dict[str, Any], payload)

    return router
