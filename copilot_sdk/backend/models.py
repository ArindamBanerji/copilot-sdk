"""Shared FastAPI response models for SDK backend routers."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class FlexibleResponse(BaseModel):
    model_config = ConfigDict(extra="allow")


class DiagnosticsResponse(FlexibleResponse):
    """Canonical convergence and measurement diagnostics."""

    centroid_distance_to_canonical: float | None = None
    epsilon_firm: dict[str, Any] | float | None = None
    iks: float | None = None
    measurement_state: dict[str, Any] | None = None
    domain: str


class ConservationResponse(FlexibleResponse):
    """Compact conservation view for clients that need the public contract."""

    status: str
    alpha: float | None = None
    q: float | None = None
    V: int | None = Field(default=None, alias="verified_count")
    model_config = ConfigDict(extra="allow", populate_by_name=True)
    theta_min: float | None = None
    signal: float | None = None
    headroom: float | None = None
    reason: str | None = None
    domain: str | None = None


class EvolutionSummaryResponse(FlexibleResponse):
    """Evolution inventory and conservation-gate telemetry."""

    domain: str
    evolution_enabled: bool
    schema_version: int = 1
    conservation_state: str | dict[str, Any] | None = None
    inventory: dict[str, Any] | None = None
    variant_stats: list[dict[str, Any]] | None = None
    recent_events: list[dict[str, Any]] | None = None


class TransferListResponse(FlexibleResponse):
    """Cross-copilot transfer records visible to the current domain."""

    transfers: list[Any]
    total: int


class ScoreResponse(FlexibleResponse):
    decision_id: str
    action: str
    action_index: int
    confidence: float
    probabilities: list[float]
    category: str
    factors: dict[str, float]
    engine: dict[str, str]


class LearnResponse(FlexibleResponse):
    decision_id: str
    iks_before: float
    iks_after: float
    centroid_delta: float
    decisions_total: int
    outcome: str
    reward: float
    previous_reward: float | None
    reward_multiplier: float
    engine: dict[str, str]
    paused: bool | None = None
    pause_reason: str | None = None
    centroid_updated: bool | None = None
    action: str | None = None
    confidence: float | None = None


class FingerprintFactorResponse(BaseModel):
    name: str
    sigma: float
    weight: float
    interpretation: str


class FingerprintResponse(FlexibleResponse):
    factors: list[FingerprintFactorResponse]
    overall_win_rate: float
    per_category_precision: dict[str, float]
    decisions_analyzed: int
    engine: dict[str, str]


class TrajectoryPointResponse(BaseModel):
    decisions: int
    iks: float
    win_rate: float
    timestamp: float


class TrajectoryResponse(FlexibleResponse):
    points: list[TrajectoryPointResponse]
    current_iks: float
    current_win_rate: float
    decisions_total: int
    days_active: float
    engine: dict[str, str]


class ScoringHealthResponse(BaseModel):
    phase: str
    alpha: float
    engine: dict[str, str]


class ScoringHistoryResponse(BaseModel):
    engine: dict[str, str]
    decisions: list[dict[str, Any]]


class MeasurementStateResponse(BaseModel):
    state: str
    decisions_verified: int
    decisions_needed: int
    arms_measured: int
    arms_total: int
    accuracy: float | None
    iks: float | None
    message: str
    provenance: str
    engine: dict[str, str]


class ConservationStatusResponse(BaseModel):
    engine: dict[str, str]
    domain: str
    verified_count: int
    correct_count: int
    total_decisions: int
    penalty_ratio: float
    alpha: float
    q: float
    V: int
    baseline: float
    baseline_q: float
    relative_trigger: float
    relative_trigger_ratio: float
    categories_total: int
    total_categories: int
    categories_with_data: int
    reason: str
    signal: float | None
    theta_min: float | None
    headroom: float | None
    status: str
    passed: bool


class ConservationInputs(BaseModel):
    alpha: float
    q: float
    V: float
    theta_min: float | None


class ConservationWhatIfResponse(BaseModel):
    engine: dict[str, str]
    domain: str
    inputs: ConservationInputs
    signal: float | None
    theta_min: float | None
    headroom: float | None
    status: str
    passed: bool


class DiscoveryAlertResponse(BaseModel):
    alert_id: str
    pattern_type: str
    source_copilots: list[str]
    title: str
    description: str
    confidence: float
    evidence: dict[str, Any]
    status: str
    created_at: float
    metadata: dict[str, Any]


class DiscoverySweepResponse(BaseModel):
    new_alerts: int
    alerts: list[DiscoveryAlertResponse]


class DiscoveryDigestResponse(BaseModel):
    alerts: list[DiscoveryAlertResponse]


class DiscoveryAlertsResponse(BaseModel):
    total: int
    alerts: list[DiscoveryAlertResponse]


class EvolutionVariantsResponse(BaseModel):
    domain: str
    variants: list[dict[str, Any]]
    active_rules: list[Any]
    promoted_rules: list[Any]
    total_active: int
    total_promoted: int


class EvolutionHistoryResponse(BaseModel):
    domain: str
    events: list[dict[str, Any]]
    count: int


class EvolutionPromotedResponse(BaseModel):
    domain: str
    promoted: list[Any]


class CheckpointQuality(BaseModel):
    window_size: int | None = None
    verified_count: int | None = None
    correct_count: int | None = None
    rolling_accuracy: float | None = None
    window_end: str | None = None
    policy_version: str | None = None


class CentroidHistoryResponse(BaseModel):
    checkpoints: list[dict[str, Any]]
    total: int


class CounterfactualDetail(BaseModel):
    decision_id: str
    category: str
    baseline_action: str
    counterfactual_action: str
    changed: bool


class CounterfactualResponse(BaseModel):
    analysis_type: str = "centroid_ablation"
    description: str
    checkpoint_id: str
    checkpoint_time: float | None
    baseline: str = "latest_centroids"
    held_fixed: list[str] = ["dk_weights", "temperature"]
    window_requested: int
    decisions_rescored: int
    would_change: int
    change_rate: float | None
    details: list[CounterfactualDetail]


class AccuracyCategoryResponse(BaseModel):
    category: str
    accuracy: float
    total: int
    correct: int
    alert: bool


class AccuracyByCategoryResponse(BaseModel):
    categories: list[AccuracyCategoryResponse]
    threshold: float
    overall_verified: int


class SelfDecisionsResponse(BaseModel):
    decisions: list[dict[str, Any]]
    total: int


class DecisionFlowCategoryStats(BaseModel):
    total_decisions: int
    verified_decisions: int
    correct_decisions: int
    accuracy: float


class DecisionFlowDecision(BaseModel):
    decision_id: str | None
    entity_id: str | None
    category: str | int | None
    action: str | int | None
    confidence: float | None
    factors: dict[str, Any] | list[Any] | None
    outcome: str | None
    is_correct: bool | None
    timestamp: str | int | float | None


class DecisionFlowCheckpoint(BaseModel):
    timestamp: str | int | float | None
    iks: float | None
    category: str | int | None
    action: str | int | None
    metadata: dict[str, Any]


class DecisionChainItem(BaseModel):
    decision_id: str
    outcome: str | None
    centroid_update: bool
    next: str | None


class DecisionFlowStatistics(BaseModel):
    avg_confidence: float
    confirmation_rate: float
    override_rate: float
    mean_reward: float | None


class DecisionFlowResponse(BaseModel):
    domain: str
    total_decisions: int
    verified_decisions: int
    accuracy: float
    by_category: dict[str, DecisionFlowCategoryStats]
    recent_decisions: list[DecisionFlowDecision]
    centroid_evolution: list[DecisionFlowCheckpoint]
    decision_chain: list[DecisionChainItem]
    flow_statistics: DecisionFlowStatistics


class TransferInactiveResponse(BaseModel):
    warm_started: Literal[False]


class TransferActiveResponse(BaseModel):
    warm_started: Literal[True]
    source_copilot: str
    patterns_transferred: int
    transferred_at: str | None
