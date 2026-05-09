"""DataOps context endpoints backed by AGE or fixture graph data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status

from .graph_queries import DataOpsGraphClient


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
METADATA_PATH = DATA_DIR / "alert_metadata.json"

router = APIRouter()


def _graph_client() -> DataOpsGraphClient:
    return DataOpsGraphClient(fallback_dir=DATA_DIR / "fallback")


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@router.get("/pipelines")
async def pipelines() -> dict[str, Any]:
    return await _graph_client().get_pipelines()


@router.get("/alerts")
async def alerts() -> dict[str, Any]:
    return await _graph_client().get_alerts()


@router.get("/system/{name}")
async def system_detail(name: str) -> dict[str, Any]:
    return await _graph_client().get_system(name)


@router.get("/alert/{id}")
async def alert_detail(id: str) -> dict[str, Any]:
    return await _graph_client().get_alert(id)


@router.get("/alert/{id}/deps")
async def alert_deps(id: str) -> dict[str, Any]:
    return await _graph_client().get_blast_radius(id)


@router.get("/alert/{id}/recurrence")
async def alert_recurrence(id: str) -> dict[str, Any]:
    return await _graph_client().get_recurrence(id)


@router.get("/alert/{id}/factors")
async def alert_factors(id: str) -> dict[str, Any]:
    return await _graph_client().get_factors(id)


@router.post("/alert-metadata", status_code=status.HTTP_201_CREATED)
def store_alert_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    decision_id = payload.get("decision_id")
    if not decision_id:
        raise HTTPException(status_code=400, detail="decision_id is required")

    metadata = _load_json(METADATA_PATH, {})
    metadata[str(decision_id)] = dict(payload)
    _write_json(METADATA_PATH, metadata)
    return {"stored": True, "decision_id": decision_id, "metadata": metadata[str(decision_id)]}


@router.get("/alert-metadata")
def alert_metadata() -> dict[str, Any]:
    return {"metadata": _load_json(METADATA_PATH, {})}
