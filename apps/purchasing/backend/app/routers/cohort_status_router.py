"""Purchasing cohort status API."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, cast

from fastapi import APIRouter

from app.services.cohort_status import CohortReadError, CohortStatusService
from copilot_sdk.backend.graph_access import GRAPH_CONNECTION_ERRORS


def create_cohort_status_router(
    graph_store_factory: Callable[[], Any] | None = None,
    oracle_artifact_path: str | Path | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/purchasing", tags=["cohort-status"])

    @router.get("/cohort-status")
    def get_cohort_status() -> dict[str, Any]:
        try:
            store = graph_store_factory() if graph_store_factory is not None else None
            if graph_store_factory is not None and store is None:
                raise CohortReadError("cohort graph store factory returned None")
            payload = cast(dict[str, Any], CohortStatusService(
                graph_store=store,
                oracle_artifact_path=oracle_artifact_path,
            ).get_status())
            return _http_payload(payload)
        except (CohortReadError, *GRAPH_CONNECTION_ERRORS) as exc:
            return _http_payload({
                "state": "INSTRUMENT_VALIDATED",
                "instrument": {
                    "validated": False,
                    "provenance": "unavailable",
                    "source_artifact": str(oracle_artifact_path or ""),
                    "experiments": [],
                },
                "real": {
                    "treatment_n": 0,
                    "control_n": 0,
                    "threshold_k": CohortStatusService.THRESHOLD_K,
                    "provenance": "real",
                    "status": "unavailable",
                    "magnitude": 0.0,
                    "magnitude_available": False,
                },
                "structure": {
                    "present": False,
                    "treatment_n": 0,
                    "control_n": 0,
                    "split_balanced": False,
                    "split_balanced_available": False,
                    "join_ok": False,
                    "join_available": False,
                    "provenance": "sample",
                },
                "data_available": False,
                "degraded": True,
                "error": str(exc),
            })


    def _http_payload(payload: dict[str, Any]) -> dict[str, Any]:
        result = dict(payload)
        real = dict(result.get("real") or {})
        magnitude = real.get("magnitude")
        real["magnitude"] = float(magnitude) if magnitude is not None else 0.0
        real["magnitude_available"] = bool(real.get("magnitude_available", magnitude is not None))
        structure = dict(result.get("structure") or {})
        split = structure.get("split_balanced")
        join = structure.get("join_ok")
        structure["split_balanced"] = bool(split) if split is not None else False
        structure["split_balanced_available"] = bool(
            structure.get("split_balanced_available", split is not None)
        )
        structure["join_ok"] = bool(join) if join is not None else False
        structure["join_available"] = bool(structure.get("join_available", join is not None))
        result["real"] = real
        result["structure"] = structure
        result["data_available"] = bool(result.get("data_available", True))
        result["degraded"] = bool(result.get("degraded", False))
        result["error"] = str(result.get("error") or "")
        return result

    return router
