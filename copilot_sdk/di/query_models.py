"""Typed contracts for the DI-3 quality-aware query service."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class QueryIntent(str, Enum):
    METRIC = "metric"
    AGGREGATION = "aggregation"
    COMPARISON = "comparison"
    ACCURACY = "accuracy"
    SOURCE_RELIABILITY = "source_reliability"
    FRESHNESS = "freshness"
    ANOMALY = "anomaly"
    IMPACT = "impact"
    ENTITY_LISTING = "entity_listing"
    UNSUPPORTED = "unsupported"


class QueryContext(BaseModel):
    domain: str = "dataops"
    timezone: str = "UTC"
    preferred_sources: list[str] = Field(default_factory=list)
    conversation_id: str | None = None


class QueryRequest(BaseModel):
    question: str = Field(max_length=2000)
    context: QueryContext = Field(default_factory=QueryContext)


class TypedFilter(BaseModel):
    field: str
    operator: str
    value: str | float | int | bool


class QueryPlan(BaseModel):
    intent: QueryIntent
    domain: str
    metric: str | None = None
    dimensions: list[str] = Field(default_factory=list)
    filters: list[TypedFilter] = Field(default_factory=list)
    time_window: str | None = None
    requested_sources: list[str] = Field(default_factory=list)
    requires_join: bool = False
    explanation: str = ""
    supported: bool = True
    reason: str | None = None


class SourceUsage(BaseModel):
    source_id: str
    records_used: int = 0
    contribution: float = 0.0
    value: float | None = None


class RawQueryResult(BaseModel):
    rows: list[dict[str, Any]] = Field(default_factory=list)
    aggregate: dict[str, Any] | None = None
    source_usage: list[SourceUsage] = Field(default_factory=list)
    data_as_of: datetime | None = None
    records_scanned: int = 0
    query_path: list[str] = Field(default_factory=list)
    unmatched_records: int = 0
    excluded_records: int = 0
    missing_values: int = 0
    disagreement_ratio: float | None = None


class SourceAttribution(BaseModel):
    source_id: str
    source: str
    trust: float
    contribution: str
    weight: float
    freshness_hours: float | None = None
    records_used: int = 0
    trust_available: bool = True


class QueryDescription(BaseModel):
    intent: str
    metric: str | None = None
    time_window: str | None = None
    domain: str
    supported: bool = True
    reason: str | None = None


class ResponseMetadata(BaseModel):
    generated_at: datetime
    data_as_of: datetime | None = None
    cache: str = "miss"
    engine_version: str = "di3-v1"
    query_id: str | None = None


class QueryResponse(BaseModel):
    answer: str
    confidence: float | None = None
    confidence_label: str = "insufficient"
    source_attribution: list[SourceAttribution] = Field(default_factory=list)
    evidence: str
    quality_warning: str | None = None
    computation_path: list[str] = Field(default_factory=list)
    query: QueryDescription
    metadata: ResponseMetadata
