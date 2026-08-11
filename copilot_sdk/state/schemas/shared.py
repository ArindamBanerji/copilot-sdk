"""Shared schemas for materialized tab-state keys used by multiple copilots."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FlexibleModel(BaseModel):
    """Strict base schema for materialized tab-state payloads."""

    model_config = ConfigDict(extra="forbid")


class TrajectoryPoint(FlexibleModel):
    decisions: int | float | None = None
    iks: int | float | None = None
    win_rate: int | float | None = Field(default=None, alias="winRate")
    timestamp: str | int | float | None = None


class TrajectoryResponse(FlexibleModel):
    points: list[TrajectoryPoint | dict[str, Any]] = Field(default_factory=list)
    current_iks: int | float | None = None
    current_win_rate: int | float | None = None
    decisions_total: int | None = None
    days_active: int | float | None = None
    engine: Any = None


class AnalyticsResponse(FlexibleModel):
    total_trades: int | None = None
    closed_trades: int | None = None
    portfolio_summary: dict[str, Any] | None = None
    portfolio_concentration: dict[str, Any] | None = None
    category_counts: dict[str, Any] | None = None
    thesis_counts: dict[str, Any] | None = None
    thesis_breakdown: dict[str, Any] | None = None
    risk_management: dict[str, Any] | None = None
    research_impact: dict[str, Any] | None = None
    open_positions: Any = None
    calendar_heatmap: Any = None
    rolling_10: list[dict[str, Any]] | None = None
    regime_analysis: dict[str, Any] | None = None
    contrast_card: dict[str, Any] | None = None
    counterfactual: dict[str, Any] | None = None
    seed_file: str | None = None
    provenance: str | None = None
    source: str | None = None


class ConservationResponse(FlexibleModel):
    """CC-4 conservation payload shared by live tab-state endpoints."""

    model_config = ConfigDict(extra="allow")

    domain: str | None = None
    engine: Any = None
    signal: int | float | None = None
    status: str | None = None
    passed: bool | None = None
    theta_min: int | float | None = None
    headroom: int | float | None = None
    penalty_ratio: int | float | None = None
    reason: str | None = None
    alpha: int | float | None = None
    q: int | float | None = None
    V: int | None = None
    baseline: int | float | None = None
    baseline_q: int | float | None = None
    categories_total: int | None = None
    categories_with_data: int | None = None
    verified_count: int | None = None
    total_decisions: int | None = None
    correct_count: int | None = None
    total_categories: int | None = None
    relative_trigger: int | float | None = None
    relative_trigger_ratio: int | float | None = None


class CohortStatusResponse(FlexibleModel):
    state: str | None = None
    real: dict[str, Any] | None = None
    instrument: dict[str, Any] | None = None
    structure: dict[str, Any] | None = None


class FingerprintFactor(FlexibleModel):
    name: str
    weight: int | float | None = None
    sigma: int | float | None = None
    category: str | None = None
    display_name: str | None = None
    interpretation: str | None = None


class FingerprintResponse(FlexibleModel):
    factors: list[FingerprintFactor | dict[str, Any]] = Field(default_factory=list)
    per_category_precision: dict[str, Any] | None = None
    decisions_analyzed: int | None = None
    overall_win_rate: int | float | None = None
    skipped_decisions: int | None = None
    engine: Any = None
