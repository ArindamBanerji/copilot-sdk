"""Models for quality-aware data asset search."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str
    filters: dict[str, object] | None = None
    limit: int = Field(default=20, ge=1, le=100)


class AssetResult(BaseModel):
    asset_id: str
    asset_name: str
    asset_type: str
    source_connector: str
    trust_tier: int
    trust_score: float
    freshness_hours: float | None
    quality_status: str
    quality_issues: list[str] = Field(default_factory=list)
    match_reason: str
    iks: float = 0.0


class SearchResult(BaseModel):
    results: list[AssetResult]
    total: int
    filters_applied: dict[str, object]
    quality_summary: str
