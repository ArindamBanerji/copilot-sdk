"""Trading multi-trader social endpoints."""

from __future__ import annotations

import math
from dataclasses import asdict, is_dataclass
from typing import Any, cast

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.trader_profiles import TraderProfileService
from copilot_sdk.scoring.mutation_lock import serialize_mutation


class ScoreAsRequest(BaseModel):
    category: str
    factors: dict[str, float] = Field(default_factory=dict)
    trader_id: str = "default"
    context: dict[str, Any] | None = None


def create_social_router(scorer_proxy: Any) -> APIRouter:
    router = APIRouter(prefix="/api/trading", tags=["trading-social"])

    def service() -> TraderProfileService:
        return TraderProfileService(getattr(scorer_proxy, "graph_store", None))

    @router.get("/traders")
    def list_traders() -> dict[str, Any]:
        traders = service().list_traders()
        return cast(dict[str, Any], _json_safe({"traders": traders, "count": len(traders), "source": "graphstore"}))

    @router.get("/traders/compare")
    def compare_traders(ids: str = Query("")) -> dict[str, Any]:
        trader_ids = [part.strip() for part in ids.split(",") if part.strip()]
        if len(trader_ids) < 2:
            raise HTTPException(status_code=400, detail="ids must include at least two traders")
        return cast(dict[str, Any], _json_safe(service().get_trader_comparison(trader_ids)))

    @router.get("/traders/{trader_id}/profile")
    def trader_profile(trader_id: str) -> dict[str, Any]:
        return cast(dict[str, Any], _json_safe(service().get_trader_profile(trader_id)))

    @router.get("/traders/{trader_id}/edge")
    def trader_edge(trader_id: str) -> dict[str, Any]:
        return cast(dict[str, Any], _json_safe(service().get_trader_edge(trader_id)))

    @router.get("/social/leaderboard")
    def leaderboard(metric: str = "accuracy") -> dict[str, Any]:
        ranking = service().leaderboard(metric)
        return cast(dict[str, Any], _json_safe({"metric": metric, "ranking": ranking, "source": "graphstore"}))

    @router.get("/social")
    def social_summary() -> dict[str, Any]:
        ranking = service().leaderboard()
        return cast(dict[str, Any], _json_safe({"traders": ranking, "leaderboard": ranking, "source": "graphstore"}))

    @router.get("/profiles")
    def profiles() -> dict[str, Any]:
        trader_ids = [row["trader_id"] for row in service().list_traders()]
        profiles = [service().get_trader_profile(trader_id) for trader_id in trader_ids]
        return cast(dict[str, Any], _json_safe({"profiles": profiles, "count": len(profiles), "source": "graphstore"}))

    @router.get("/trader/{trader_id}")
    def legacy_trader_profile(trader_id: str) -> dict[str, Any]:
        return trader_profile(trader_id)

    @router.post("/score-as")
    @serialize_mutation("trading", event="score")
    def score_as(request: ScoreAsRequest) -> dict[str, Any]:
        trader_id = _normalize_trader(request.trader_id)
        try:
            result = scorer_proxy.score(
                request.factors,
                request.category,
                metadata={
                    "entity_id": trader_id,
                    "trader_id": trader_id,
                    "context": request.context or {},
                },
            )
        except AssertionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        payload = _json_safe(result)
        if isinstance(payload, dict):
            payload["trader_id"] = trader_id
        return cast(dict[str, Any], payload)

    return router


def _normalize_trader(value: Any) -> str:
    text = str(value or "").strip()
    return text or "default"


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "tolist"):
        try:
            return _json_safe(value.tolist())
        except Exception:
            pass
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            return value.item()
        except Exception:
            pass
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value
