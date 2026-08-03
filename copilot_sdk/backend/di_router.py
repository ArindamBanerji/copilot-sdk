"""FastAPI router factory for Data Intelligence source profiles."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from copilot_sdk.di import AcquisitionAdvisor, BaseSourceProfiler, IntelligenceMapBuilder


class ProfileRefreshRequest(BaseModel):
    entity_ids: list[str] = Field(default_factory=list)


class DISourceSummary(BaseModel):
    source_name: str
    entity_type: str
    trust_tier: int
    has_profile: bool = False
    cache_status: str = "not_profiled"
    age_seconds: float | None = None
    is_stale: bool = False
    latest_profile: dict[str, Any] | None = None


class DIProfilesResponse(BaseModel):
    sources: list[DISourceSummary] = Field(default_factory=list)
    total: int = 0


class DIProfileResponse(BaseModel):
    source_name: str
    entity_type: str
    trust_tier: int
    has_profile: bool = False
    cache_status: str = "not_profiled"
    age_seconds: float | None = None
    is_stale: bool = False
    profile: dict[str, Any] | None = None


class DIRefreshResponse(BaseModel):
    status: str
    source_name: str
    cache_status: str
    age_seconds: float
    is_stale: bool
    profile: dict[str, Any]


def create_di_router(
    profiler_registry: dict[str, BaseSourceProfiler],
    *,
    map_builder: Any | None = None,
    map_sources: list[dict[str, Any]] | None = None,
    advisor: Any | None = None,
    cache_ttl_seconds: int | None = 300,
) -> APIRouter:
    """Create domain-agnostic Data Intelligence source profile endpoints."""

    router = APIRouter()
    cache: dict[str, dict[str, Any]] = {}
    resolved_map_builder = map_builder or IntelligenceMapBuilder()
    resolved_advisor = advisor or AcquisitionAdvisor()

    def _profiler(source_name: str) -> BaseSourceProfiler:
        try:
            return profiler_registry[source_name]
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown DI source: {source_name}") from exc

    def _connector_metadata(profiler: BaseSourceProfiler, source_name: str) -> dict[str, Any]:
        connector = getattr(profiler, "connector", None)
        return {
            "source_name": str(getattr(connector, "source_name", source_name)),
            "entity_type": str(getattr(connector, "entity_type", "")),
            "trust_tier": int(getattr(connector, "trust_tier", 3)),
        }

    def _cache_metadata(entry: dict[str, Any] | None, now: datetime | None = None) -> dict[str, Any]:
        if entry is None:
            return {
                "has_profile": False,
                "cache_status": "not_profiled",
                "age_seconds": None,
                "is_stale": False,
            }
        current = now or datetime.now(timezone.utc)
        generated_at = entry["generated_at"]
        age_seconds = max((current - generated_at).total_seconds(), 0.0)
        is_stale = cache_ttl_seconds is not None and age_seconds > float(cache_ttl_seconds)
        return {
            "has_profile": True,
            "cache_status": "stale" if is_stale else "fresh",
            "age_seconds": age_seconds,
            "is_stale": is_stale,
        }

    def _profile_response(source_name: str) -> dict[str, Any]:
        profiler = _profiler(source_name)
        entry = cache.get(source_name)
        payload = {
            **_connector_metadata(profiler, source_name),
            **_cache_metadata(entry),
            "profile": entry["profile"] if entry is not None else None,
        }
        return payload

    @router.get("/di/profiles", response_model=DIProfilesResponse)
    def profiles() -> dict[str, Any]:
        sources = []
        for source_name in sorted(profiler_registry):
            profiler = _profiler(source_name)
            entry = cache.get(source_name)
            sources.append(
                {
                    **_connector_metadata(profiler, source_name),
                    **_cache_metadata(entry),
                    "latest_profile": entry["profile"] if entry is not None else None,
                }
            )
        return {"sources": sources, "total": len(sources)}

    @router.get("/di/profile/{source_name}", response_model=DIProfileResponse)
    def profile(source_name: str) -> dict[str, Any]:
        return _profile_response(source_name)

    @router.post("/di/profile/{source_name}/refresh", response_model=DIRefreshResponse)
    def refresh_profile(source_name: str, request: ProfileRefreshRequest) -> dict[str, Any]:
        profiler = _profiler(source_name)
        entity_ids = [str(entity_id) for entity_id in request.entity_ids if str(entity_id)]
        if not entity_ids:
            raise HTTPException(status_code=400, detail="entity_ids must contain at least one id")
        profile_payload = profiler.profile(entity_ids).to_dict()
        generated_at = datetime.now(timezone.utc)
        cache[source_name] = {
            "profile": profile_payload,
            "generated_at": generated_at,
        }
        return {
            "status": "completed",
            "source_name": source_name,
            "profile": profile_payload,
            **_cache_metadata(cache[source_name], generated_at),
        }

    @router.get("/di/combinations")
    def combinations() -> dict[str, Any]:
        discovered = resolved_map_builder.discover_combinations()
        combinations_payload = [
            item.to_dict() if hasattr(item, "to_dict") else dict(item)
            for item in discovered
        ]
        total_value = sum(
            float(item.get("value_estimate_annual", item.get("annual_value", 0.0)) or 0.0)
            for item in combinations_payload
        )
        return {
            "combinations": combinations_payload,
            "total_value": round(total_value, 2),
        }

    @router.get("/di/acquisition-advice")
    def acquisition_advice() -> dict[str, Any]:
        result = resolved_advisor.recommend()
        recommendations = result.get("recommendations", []) if isinstance(result, dict) else result
        return {"recommendations": list(recommendations)}

    @router.get("/di/intelligence-map")
    def intelligence_map() -> dict[str, Any]:
        result = (
            resolved_map_builder.build(sources=map_sources)
            if map_sources is not None
            else resolved_map_builder.build()
        )
        payload = result.to_dict() if hasattr(result, "to_dict") else dict(result)
        if not payload.get("gold_lines"):
            payload["gold_lines"] = [
                {
                    "source": item.get("source_a"),
                    "target": item.get("source_b"),
                    "value": item.get("value_estimate_annual", 0.0),
                    "type": "suggested",
                }
                for item in resolved_map_builder.discover_combinations()
            ]
        for node in payload.get("nodes", []):
            if "trust" not in node and "brightness" in node:
                node["trust"] = node["brightness"]
        return payload

    return router
