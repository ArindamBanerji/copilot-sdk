"""FastAPI router factory for Data Intelligence source profiles."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from copilot_sdk.di import AcquisitionAdvisor, BaseSourceProfiler, IntelligenceMapBuilder
from copilot_sdk.di.query_models import QueryRequest, QueryResponse
from copilot_sdk.di.query_service import DIQueryService, InvalidQueryError
from copilot_sdk.di.catalog import ExternalDataCatalog
from copilot_sdk.di.search_models import SearchResult
from copilot_sdk.di.search_service import DISearchService


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
    valuation_model: Any | None = None,
    query_service: DIQueryService | None = None,
    search_service: DISearchService | None = None,
    catalog: ExternalDataCatalog | None = None,
    cache_ttl_seconds: int | None = 300,
) -> APIRouter:
    """Create domain-agnostic Data Intelligence source profile endpoints."""

    router = APIRouter()
    cache: dict[str, dict[str, Any]] = {}
    resolved_map_builder = map_builder or IntelligenceMapBuilder()
    resolved_advisor = advisor or AcquisitionAdvisor()
    resolved_catalog = catalog or ExternalDataCatalog()
    resolved_valuation_model = valuation_model or getattr(resolved_advisor, "valuation_model", None)
    intelligence_map_cache: dict[str, Any] | None = None

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

    @router.get("/di/sources", response_model=DIProfilesResponse)
    def sources() -> dict[str, Any]:
        """Compatibility alias for the source-profiler collection endpoint."""
        return profiles()

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

    @router.get("/di/valuation")
    def valuation() -> dict[str, Any]:
        model = resolved_valuation_model or getattr(resolved_advisor, "valuation_model", None)
        if model is not None and callable(getattr(model, "compute_all_recommendations", None)):
            valuations = list(model.compute_all_recommendations())
        else:
            result = resolved_advisor.recommend()
            recommendations = result.get("recommendations", []) if isinstance(result, dict) else result
            valuations = []
            for recommendation in recommendations:
                item = dict(recommendation)
                value = float(item.get("computed_value_annual", item.get("annual_value", 0.0)) or 0.0)
                valuations.append(
                    {
                        "source_name": item.get("source_name", item.get("source", "")),
                        "provider": item.get("provider", ""),
                        "catalog_entry": item.get("catalog_entry"),
                        "signal": item.get("signal", "demand_prediction"),
                        "computed_value_annual": value,
                        "methodology": item.get("methodology", "Derived from acquisition recommendation."),
                        "confidence": item.get("confidence", "moderate"),
                    }
                )
        return {
            "valuations": valuations,
            "total_portfolio_value": round(
                sum(float(item.get("computed_value_annual", 0.0) or 0.0) for item in valuations), 2
            ),
        }

    @router.get("/di/intelligence-map")
    def intelligence_map() -> dict[str, Any]:
        nonlocal intelligence_map_cache
        if intelligence_map_cache is not None:
            return intelligence_map_cache
        if map_sources is not None:
            # DataOps supplies connector-derived rows at startup.  Keep the
            # request path bounded by normalizing those rows directly rather
            # than re-running connector discovery on every request.
            nodes = []
            for index, source in enumerate(map_sources):
                row = dict(source)
                label = str(row.get("name") or row.get("source_name") or f"source-{index + 1}")
                nodes.append({
                    "id": str(row.get("id") or label).replace(" ", "_").lower(),
                    "label": label,
                    "domain": str(row.get("domain") or "dataops"),
                    "trust": row.get("trust", row.get("source_reliability", row.get("quality_score"))),
                    "records": row.get("records", row.get("record_count", 0)),
                    "provenance": row.get("provenance", "connector"),
                })
            payload: dict[str, Any] = {
                "nodes": nodes,
                "edges": [],
                "gold_lines": [],
                "badges": [],
                "clusters": {},
                "join_keys": [],
                "narrative": f"Intelligence Map contains {len(nodes)} source nodes.",
            }
        else:
            result = resolved_map_builder.build()
            payload = result.to_dict() if hasattr(result, "to_dict") else dict(result)
        if not payload.get("gold_lines"):
            # Keep the read path bounded: valuation providers may be remote.
            # The deterministic combination discovery is sufficient for the
            # dashboard's gold-line fallback and is cached below.
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
        intelligence_map_cache = payload
        return payload

    @router.post("/di/query", response_model=QueryResponse)
    def query(request: QueryRequest) -> QueryResponse:
        if query_service is None:
            raise HTTPException(status_code=503, detail="DI query service is not configured")
        try:
            return query_service.execute(request)
        except InvalidQueryError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/di/search", response_model=SearchResult)
    def search(
        q: str = Query(default=""),
        trust_tier: int | None = Query(default=None, ge=1, le=3),
        freshness_max: float | None = Query(default=None, ge=0),
        quality_status: str | None = Query(default=None),
        iks_min: float | None = Query(default=None, ge=0),
        limit: int = Query(default=20, ge=1, le=100),
    ) -> SearchResult:
        if search_service is None:
            raise HTTPException(status_code=503, detail="DI search service is not configured")
        filters = {
            key: value for key, value in {
                "trust_tier": trust_tier,
                "freshness_max": freshness_max,
                "quality_status": quality_status,
                "iks_min": iks_min,
                "limit": limit,
            }.items() if value is not None
        }
        return search_service.search(q, filters)

    @router.get("/di/catalog")
    def catalog_entries(
        q: str = Query(default=""),
        domain: str | None = Query(default=None),
        cost_tier: str | None = Query(default=None),
        data_type: str | None = Query(default=None),
    ) -> dict[str, Any]:
        entries = resolved_catalog.search(q, domain=domain, cost_tier=cost_tier, data_type=data_type)
        return {"entries": [entry.to_dict() for entry in entries], "total": len(entries)}

    @router.get("/di/catalog/{provider_id}")
    def catalog_entry(provider_id: str) -> dict[str, Any]:
        entry = resolved_catalog.get_by_id(provider_id)
        if entry is None:
            raise HTTPException(status_code=404, detail=f"Unknown catalog provider: {provider_id}")
        return entry.to_dict()

    return router
