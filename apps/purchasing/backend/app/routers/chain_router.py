"""Same-brand location transfer endpoints."""

from __future__ import annotations

from typing import Any

import numpy as np
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from copilot_sdk.scoring.presets.purchasing import PurchasingPreset
from copilot_sdk.transfer.chain_transfer import ChainTransfer, LocationStore


class ChainRequest(BaseModel):
    source: str = "chicago"
    target: str = "miami"
    dry_run: bool = True


def create_demo_chain_stores() -> dict[str, LocationStore]:
    preset = PurchasingPreset()
    categories = list(preset.shape.category_names)
    actions = list(preset.shape.action_names)
    shape = (preset.shape.n_categories, preset.shape.n_actions, preset.shape.n_factors)
    return {
        "chicago": LocationStore(
            location_id="Chicago",
            decisions=500,
            accuracy=0.84,
            conservation="GREEN",
            categories=categories,
            actions=actions,
            pattern_grid=np.ones(shape, dtype=float) * 0.72,
            dk_weights={"supplier": 0.7},
        ),
        "miami": LocationStore(
            location_id="Miami",
            decisions=0,
            accuracy=0.50,
            conservation="GREEN",
            categories=categories,
            actions=actions,
            pattern_grid=np.ones(shape, dtype=float) * 0.50,
            dk_weights={"supplier": 0.2},
        ),
    }


def reset_chain_state(app_state: Any) -> None:
    app_state.purchasing_chain_stores = create_demo_chain_stores()


def create_chain_router() -> APIRouter:
    router = APIRouter(prefix="/api/purchasing/chain", tags=["purchasing-chain"])
    transfer = ChainTransfer()

    @router.post("/validate")
    def validate(payload: ChainRequest, request: Request) -> dict[str, Any]:
        source, target = _stores_for_request(request, payload)
        result = transfer.validate(source, target)
        return {**result, "source_location": source.location_id, "target_location": target.location_id}

    @router.post("/transfer")
    def execute(payload: ChainRequest, request: Request) -> dict[str, Any]:
        source, target = _stores_for_request(request, payload)
        result = transfer.transfer(source, target, dry_run=payload.dry_run)
        return {**result, "source_location": source.location_id, "target_location": target.location_id}

    @router.get("/status")
    def status(request: Request) -> dict[str, Any]:
        stores = _chain_stores(request)
        source = stores["chicago"]
        target = stores["miami"]
        return {
            "source": {"location": source.location_id, "decisions": source.decisions, "accuracy": source.accuracy},
            "target": {"location": target.location_id, "decisions": target.decisions, "accuracy": target.accuracy},
            "estimated_accuracy": transfer.estimate_accuracy(source.accuracy),
            "provenance": "demo",
            "note": "Miami starts with Chicago patterns and verifies them locally before auto-approve.",
        }

    return router


def _stores_for_request(request: Request, payload: ChainRequest) -> tuple[LocationStore, LocationStore]:
    stores = _chain_stores(request)
    source_key = payload.source.strip().lower()
    target_key = payload.target.strip().lower()
    if source_key not in stores:
        raise HTTPException(status_code=404, detail=f"Unknown source location: {payload.source}")
    if target_key not in stores:
        raise HTTPException(status_code=404, detail=f"Unknown target location: {payload.target}")
    return stores[source_key], stores[target_key]


def _chain_stores(request: Request) -> dict[str, LocationStore]:
    stores = getattr(request.app.state, "purchasing_chain_stores", None)
    if stores is None:
        reset_chain_state(request.app.state)
        stores = request.app.state.purchasing_chain_stores
    return stores
