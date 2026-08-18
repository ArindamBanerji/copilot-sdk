"""Pydantic schemas for Trading materialized tab-state keys."""

from __future__ import annotations

from typing import Any

from pydantic import Field, RootModel

from app.state.key_manifest import TradingKey
from copilot_sdk.state.schemas.shared import (
    AnalyticsResponse,
    CohortStatusResponse,
    ConservationResponse,
    FingerprintResponse,
    FlexibleModel,
    TrajectoryResponse,
)


class HistorySummaryResponse(FlexibleModel):
    decisions: list[dict[str, Any]] = Field(default_factory=list)
    total: int | None = None
    bounded: bool | None = None
    engine: Any = None


class TradeMetadataResponse(RootModel[dict[str, Any]]):
    pass


class MarketSnapshotResponse(FlexibleModel):
    vix: dict[str, Any] | None = None
    spy: dict[str, Any] | None = None
    source: str | None = None
    sector: dict[str, Any] | None = None
    provenance: dict[str, Any] | None = None
    asOf: str | None = None
    rsi: float | None = None
    above_50ma: bool | None = None
    volume_rank: int | None = None
    market_cap_b: float | None = None
    source_detail: str | None = None


class TransferStatusResponse(FlexibleModel):
    warm_started: bool | None = None
    source_copilot: str | None = None
    source_accuracy: float | None = None
    patterns_transferred: int | None = None
    categories_transferred: int | None = None
    provenance: str | None = None
    status: str | None = None
    domain: str | None = None
    own_fingerprint_present: bool | None = None
    available_domains: list[str] = Field(default_factory=list)
    opportunity_count: int | None = None
    opportunities: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[Any] = Field(default_factory=list)
    available_transfers: list[dict[str, Any]] = Field(default_factory=list)


class ArchetypeSummary(FlexibleModel):
    name: str
    domain: str | None = None
    description: str | None = None
    expected_initial_accuracy: float | None = None
    categories: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    factors: list[str] = Field(default_factory=list)


class ArchetypesResponse(RootModel[Any]):
    pass


class MeasurementStateResponse(FlexibleModel):
    engine: Any = None
    state: str | None = None
    message: str | None = None
    accuracy: float | None = None
    iks: float | None = None
    decisions_verified: int | None = None
    decisions_needed: int | None = None
    arms_measured: int | None = None
    arms_total: int | None = None
    provenance: str | None = None


class RegimeResponse(FlexibleModel):
    current_regime: str | None = None
    previous_regime: str | None = None
    regime_break_active: bool | None = None
    decisions_in_new_regime: int | None = None
    decisions_to_stabilize: int | None = None
    autonomy_level: str | None = None
    restrictions: list[str] = Field(default_factory=list)
    current: dict[str, Any] | None = None
    accuracy_by_category: dict[str, Any] | None = None
    recommendations: list[dict[str, Any]] = Field(default_factory=list)


class PatternsResponse(FlexibleModel):
    patterns: list[dict[str, Any]] | None = None
    total_trades: int | None = None
    message: str | None = None
    total_patterns_detected: int | None = None
    total_trades_analyzed: int | None = None
    active_patterns: int | None = None
    patterns_by_category: dict[str, Any] | None = None
    most_severe: str | None = None


class AccuracyResponse(FlexibleModel):
    categories: list[dict[str, Any]] = Field(default_factory=list)
    overall_verified: int | None = None
    threshold: float | None = None
    evidence_tier: str | None = None
    evidence_label: str | None = None
    evidence_gate: str | None = None
    claim_id: str | None = None


class TrustAnalysisResponse(FlexibleModel):
    factors: list[Any] = Field(default_factory=list)
    factor_details: list[dict[str, Any]] | None = None
    factor_names: list[str] | None = None
    trust_scores: dict[str, Any] | None = None
    mode: str | None = None
    phase: str | None = None
    available_categories: list[str] | None = None
    implemented: list[str] | None = None
    top_signal: str | None = None
    noise_signals: list[str] | None = None
    hero_insight: str | None = None
    per_category: Any = None
    decisions_until_dk: int | None = None
    total_trades: int | None = None


class DecisionsSummaryResponse(FlexibleModel):
    decisions: list[dict[str, Any]] = Field(default_factory=list)
    total: int | None = None
    limit: int | None = None


class VolSharpeResponse(FlexibleModel):
    naive_quality_score: float | None = None
    quality_adjusted_score: float | None = None
    inflation: float | None = None
    n_decisions: int | None = None
    decisions_until_measured: int | None = None
    day_zero: bool | None = None
    provenance: str | None = None
    substantiation: Any = None
    status: str | None = None
    overall_quality_score: float | None = None
    overall_quality_adjusted: float | None = None
    clusters: list[dict[str, Any]] = []
    min_decisions_per_cluster: int | None = None
    source: str | None = None
    analytics_provenance: str | None = None
    evidence_tier: str | None = None
    evidence_label: str | None = None
    evidence_gate: str | None = None
    claim_id: str | None = None


class VrpAttributionResponse(FlexibleModel):
    provenance: str | None = None
    substantiation: Any = None
    day_zero: bool | None = None
    decisions_until_measured: int | None = None
    status: str | None = None
    vrp_spread_mean: float | None = None
    vrp_spread_current: float | None = None
    classification: str | None = None
    iv_mean: float | None = None
    rv_mean: float | None = None
    n_eligible: int | None = None
    n_excluded_missing_iv_rv: int | None = None
    min_observations: int | None = None
    source: str | None = None
    analytics_provenance: str | None = None
    tail_attribution: dict[str, Any] | None = None
    evidence_tier: str | None = None
    evidence_label: str | None = None
    evidence_gate: str | None = None
    claim_id: str | None = None


class RegimeVrpResponse(FlexibleModel):
    regimes: Any = None
    n_decisions: int | None = None
    provenance: str | None = None
    substantiation: Any = None
    day_zero: bool | None = None
    decisions_until_measured: int | None = None
    evidence_tier: str | None = None
    evidence_label: str | None = None
    evidence_gate: str | None = None
    claim_id: str | None = None


class DispersionFollowResponse(FlexibleModel):
    follow_rate: float | None = None
    signals_fired: int | None = None
    followed: int | None = None
    skipped: int | None = None
    skipped_value: float | None = None
    provenance: str | None = None
    substantiation: Any = None
    day_zero: bool | None = None
    decisions_until_measured: int | None = None
    evidence_tier: str | None = None
    evidence_label: str | None = None
    evidence_gate: str | None = None
    claim_id: str | None = None


class CorrelationPairResponse(FlexibleModel):
    ticker_a: str | None = None
    ticker_b: str | None = None
    correlation: float | None = None


class CorrelationAlertResponse(FlexibleModel):
    level: str | None = None
    message: str | None = None
    value: float | None = None
    ticker_a: str | None = None
    ticker_b: str | None = None
    tickers: list[str] | None = None
    correlation: float | None = None


class CorrelationResponse(FlexibleModel):
    matrix: Any = None
    correlations: Any = None
    tickers: list[str] = Field(default_factory=list)
    pairs: list[CorrelationPairResponse] = Field(default_factory=list)
    avg_correlation: float | None = None
    max_pair: CorrelationPairResponse | None = None
    alerts: list[CorrelationAlertResponse] = Field(default_factory=list)
    window_days: int | None = None
    source: str | None = None
    reason: str | None = None
    n_decisions: int | None = None
    day_zero: bool | None = None
    decisions_until_measured: int | None = None
    provenance: str | None = None
    rho_bar: float | None = None
    effective_multiplier: float | None = None
    n_effective_bets: float | None = None
    tail_gap: Any = None
    recommendations: list[str] = Field(default_factory=list)


class CounterfactualDefaultResponse(FlexibleModel):
    base_score: float | None = None
    perturbed_score: float | None = None
    delta: float | None = None
    perturbed_factor: str | None = None
    base_action: str | None = None
    perturbed_action: str | None = None
    provenance: str | None = None


class EvolutionResponse(RootModel[Any]):
    pass


class CentroidHistorySummaryResponse(FlexibleModel):
    checkpoints: list[dict[str, Any]] = Field(default_factory=list)
    total: int | None = None


class AuditTrailSummaryResponse(FlexibleModel):
    trails: list[dict[str, Any]] = Field(default_factory=list)
    total: int | None = None


class RegimeStatusResponse(RegimeResponse):
    pass


class RegimeAnalyticsResponse(FlexibleModel):
    regimes: dict[str, Any] = Field(default_factory=dict)
    total_decisions: int | None = None
    regime_count: int | None = None


class PromotionResponse(RootModel[list[dict[str, Any]]]):
    pass


class RejectionSummaryResponse(FlexibleModel):
    total_tested: int | None = None
    total_promoted: int | None = None
    total_rejected: int | None = None
    rejection_breakdown: dict[str, Any] = Field(default_factory=dict)
    rejected_variants: list[dict[str, Any]] = Field(default_factory=list)
    provenance: str | None = None


class TransferResponse(TransferStatusResponse):
    pass


class BrokerExecutionSummaryResponse(FlexibleModel):
    broker: str | None = None
    trade_count: int | None = None
    avg_slippage: float | None = None
    fill_rate: float | None = None
    median_slippage: float | None = None
    total_slippage_cost: float | None = None
    avg_fill_time_seconds: float | None = None


class ExecutionResponse(FlexibleModel):
    summary: Any = None
    brokers: list[BrokerExecutionSummaryResponse] = Field(default_factory=list)
    best_broker: str | None = None
    annual_savings_estimate: float | None = None
    recommendation: str | None = None


class WebhookHistoryResponse(RootModel[Any]):
    pass


class VixResponse(FlexibleModel):
    status: str | None = None
    matrix: dict[str, Any] | None = None
    best_bucket: Any = None
    worst_bucket: Any = None
    total_analyzed: int | None = None
    total_skipped: int | None = None
    hold_labels: dict[str, Any] | None = None
    vix_labels: dict[str, Any] | None = None
    recommendations: list[str] = Field(default_factory=list)


class JournalTradesSummaryResponse(FlexibleModel):
    trades: list[dict[str, Any]] = Field(default_factory=list)
    count: int | None = None
    total: int | None = None
    filters_applied: dict[str, Any] = Field(default_factory=dict)
    aggregate: dict[str, Any] | None = None


class AnalyticsByCategoryResponse(FlexibleModel):
    group_by: str | None = None
    groups: list[dict[str, Any]] = Field(default_factory=list)
    total: int | None = None


class AnalyticsBySubcategoryResponse(AnalyticsByCategoryResponse):
    pass


class RegimeHistoryResponse(RootModel[Any]):
    pass


class CorrelationConfigResponse(FlexibleModel):
    window: int | None = None


class RegimeAnalyticsSummaryResponse(RegimeAnalyticsResponse):
    pass


class IksResponse(FlexibleModel):
    iks: float | None = None
    evidence_tier: str | None = None
    evidence_label: str | None = None
    evidence_gate: str | None = None
    claim_id: str | None = None


class RegimeCurrentResponse(FlexibleModel):
    current_regime: str | None = None
    previous_regime: str | None = None
    regime_break_active: bool | None = None
    decisions_in_new_regime: int | None = None
    decisions_to_stabilize: int | None = None
    autonomy_level: str | None = None
    restrictions: list[str] = Field(default_factory=list)
    regime: str | None = None
    confidence: float | None = None
    vix: float | None = None
    adx: float | None = None
    near_boundary: bool | None = None
    hurst: float | None = None
    vol_state: str | None = None
    vix_percentile: float | None = None
    timestamp: str | None = None
    source: str | None = None


class RegimePerformanceResponse(FlexibleModel):
    regimes: dict[str, Any] = Field(default_factory=dict)
    total_decisions: int | None = None
    regime_count: int | None = None
    per_regime_accuracy: dict[str, Any] = Field(default_factory=dict)
    current_regime: str | None = None
    edge_categories: list[dict[str, Any]] = Field(default_factory=list)
    recommendation: str | None = None
    observation: str | None = None
    evidence_tier: str | None = None
    evidence_label: str | None = None
    evidence_gate: str | None = None
    claim_id: str | None = None


class EvolutionPromotedResponse(FlexibleModel):
    domain: str | None = None
    promoted: list[dict[str, Any]] = Field(default_factory=list)


TRADING_SCHEMA_BY_KEY = {
    TradingKey.ANALYTICS: AnalyticsResponse,
    TradingKey.HISTORY_SUMMARY: HistorySummaryResponse,
    TradingKey.TRADE_METADATA: TradeMetadataResponse,
    TradingKey.MARKET_SNAPSHOT: MarketSnapshotResponse,
    TradingKey.TRANSFER_STATUS: TransferStatusResponse,
    TradingKey.ARCHETYPES: ArchetypesResponse,
    TradingKey.MEASUREMENT_STATE: MeasurementStateResponse,
    TradingKey.REGIME: RegimeResponse,
    TradingKey.PATTERNS: PatternsResponse,
    TradingKey.ACCURACY: AccuracyResponse,
    TradingKey.FINGERPRINT: FingerprintResponse,
    TradingKey.TRUST_ANALYSIS: TrustAnalysisResponse,
    TradingKey.DECISIONS_SUMMARY: DecisionsSummaryResponse,
    TradingKey.VOL_SHARPE: VolSharpeResponse,
    TradingKey.VRP_ATTRIBUTION: VrpAttributionResponse,
    TradingKey.REGIME_VRP: RegimeVrpResponse,
    TradingKey.DISPERSION_FOLLOW: DispersionFollowResponse,
    TradingKey.CORRELATION: CorrelationResponse,
    TradingKey.COUNTERFACTUAL_DEFAULT: CounterfactualDefaultResponse,
    TradingKey.EVOLUTION: EvolutionResponse,
    TradingKey.TRAJECTORY: TrajectoryResponse,
    TradingKey.CONSERVATION: ConservationResponse,
    TradingKey.CENTROID_HISTORY_SUMMARY: CentroidHistorySummaryResponse,
    TradingKey.AUDIT_TRAIL_SUMMARY: AuditTrailSummaryResponse,
    TradingKey.REGIME_STATUS: RegimeStatusResponse,
    TradingKey.REGIME_ANALYTICS: RegimeAnalyticsResponse,
    TradingKey.PROMOTION: PromotionResponse,
    TradingKey.REJECTION_SUMMARY: RejectionSummaryResponse,
    TradingKey.TRANSFER: TransferResponse,
    TradingKey.EXECUTION: ExecutionResponse,
    TradingKey.WEBHOOK_HISTORY: WebhookHistoryResponse,
    TradingKey.COHORT_STATUS: CohortStatusResponse,
    TradingKey.VIX: VixResponse,
    TradingKey.JOURNAL_TRADES_SUMMARY: JournalTradesSummaryResponse,
    TradingKey.ANALYTICS_BY_CATEGORY: AnalyticsByCategoryResponse,
    TradingKey.ANALYTICS_BY_SUBCATEGORY: AnalyticsBySubcategoryResponse,
    TradingKey.REGIME_HISTORY: RegimeHistoryResponse,
    TradingKey.CORRELATION_CONFIG: CorrelationConfigResponse,
    TradingKey.REGIME_ANALYTICS_SUMMARY: RegimeAnalyticsSummaryResponse,
    TradingKey.IKS: IksResponse,
    TradingKey.REGIME_CURRENT: RegimeCurrentResponse,
    TradingKey.REGIME_PERFORMANCE: RegimePerformanceResponse,
    TradingKey.EVOLUTION_PROMOTED: EvolutionPromotedResponse,
}
