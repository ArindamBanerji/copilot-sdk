export const S2P_CATEGORIES = [
  "price_variance",
  "quantity_mismatch",
  "duplicate_risk",
  "contract_gap",
  "format_compliance"
] as const;

export const S2P_ACTIONS = [
  "auto_approve",
  "hold_for_review",
  "escalate_to_buyer",
  "flag_leakage",
  "refer_to_specialist"
] as const;

export const S2P_FACTORS = [
  "match_status",
  "amount_variance_ratio",
  "duplicate_score",
  "supplier_exception_history",
  "payment_terms_impact",
  "commodity_index_correlation",
  "tax_regulatory_compliance"
] as const;

export type S2PCategory = (typeof S2P_CATEGORIES)[number];
export type S2PAction = (typeof S2P_ACTIONS)[number];
export type S2PFactor = (typeof S2P_FACTORS)[number];
export type ProvenanceTier = "learned" | "context" | "proven" | "sample" | "signal";

export const S2P_REASON_CODES = [
  "wrong_category",
  "wrong_action",
  "missing_context",
  "system_correct_but_override_policy",
  "novel_situation"
] as const;

export type S2PReasonCode = (typeof S2P_REASON_CODES)[number];

export type FactorMap = Partial<Record<S2PFactor, number>> & Record<string, number | undefined>;

export interface InvoiceException {
  invoice_id?: string;
  invoiceId?: string;
  event_id?: string;
  eventId?: string;
  supplier?: string;
  supplier_name?: string;
  supplierName?: string;
  supplier_id?: string;
  supplierId?: string;
  po_reference?: string;
  poReference?: string;
  po_number?: string;
  poNumber?: string;
  amount?: number;
  amount_variance_ratio?: number;
  variance_ratio?: number;
  category?: S2PCategory | string;
  scored_action?: S2PAction | string;
  scoredAction?: S2PAction | string;
  recommended_action?: S2PAction | string;
  recommendedAction?: S2PAction | string;
  confidence?: number;
  factors?: FactorMap;
  factor_vector?: number[];
  factorVector?: number[];
  process_context?: ProcessContext | null;
  processContext?: ProcessContext | null;
}

export interface SupplierProfile {
  supplier_id: string;
  supplier_name: string;
  exception_rate: number;
  exception_rate_trend: number | null;
  otif: number | null;
  otif_by_quarter: Record<string, number>;
  avg_lead_time_days: number | null;
  lead_time_by_quarter: Record<string, number>;
  invoice_count: number;
  last_invoice_date: string | null;
  pricing_trend: number | null;
  categories: string[];
  last_updated: string | null;
  source: "fixture" | "computed" | "hybrid";
  supplierId?: string;
  name?: string;
  category?: string;
  otif_score?: number;
  otifScore?: number;
  total_invoices?: number;
  totalInvoices?: number;
  trend_direction?: string;
  trendDirection?: string;
}

export interface SupplierHistoryEvent {
  invoice_id: string;
  invoice_date: string | null;
  category: string;
  is_correct: boolean;
  reward: number;
  amount: number;
  supplier_id?: string;
  supplier_name?: string;
  recommended_action?: string;
  actual_action?: string;
  factors?: Record<string, number>;
  timestamp?: string | null;
}

export interface SupplierProfilesResponse {
  suppliers: SupplierProfile[];
  total: number;
  source: string;
}

export interface SupplierHistoryResponse {
  events: SupplierHistoryEvent[];
  total: number;
}

export interface PaymentBehavior {
  supplier_id: string;
  supplier_name: string;
  current_terms: string;
  recommended_strategy: "early_pay" | "on_time" | "extend";
  reason: string;
  payment_otif_correlation: number;
  discount_opportunity: number;
  risk_if_delayed: string;
  confidence: number;
}

export interface PaymentOptimizationResponse {
  strategies: PaymentBehavior[];
  total_discount_opportunity: number;
  suppliers_analyzed: number;
  dpo_improvement_days: number;
  summary: string;
}

export interface CrossSystemDiscovery {
  discovery_id: string;
  title: string;
  sources: string[];
  correlation_strength: number;
  impact_estimate: string;
  pattern: string;
  confidence: number;
  discovered_at: string;
  recommendation: string;
}

export interface DiscoveryResponse {
  discoveries: CrossSystemDiscovery[];
  total_discoveries: number;
  sources_connected: number;
  highest_impact: string;
}

export interface DisruptionRecovery {
  disruption_id: string;
  disruption_type: string;
  occurrence: number;
  recovery_time_days: number;
  recovery_cost: number;
  improvement_from_first: number;
  pattern_reuse: string;
  decisions_applied: number;
}

export interface DisruptionResponse {
  disruptions: DisruptionRecovery[];
  total_disruptions: number;
  cumulative_savings: number;
  avg_improvement_pct: number;
  learning_narrative: string;
}

export interface BehavioralCluster {
  cluster_id: number;
  label: string;
  members: string[];
  centroid?: number[];
  consolidation_potential: "high" | "medium" | "low";
  estimated_savings: number;
}

export interface ClusteringResponse {
  clusters: BehavioralCluster[];
  total_suppliers: number;
  consolidation_candidates: number;
  estimated_annual_savings: number;
  method: string;
}

export interface SimilarSupplier {
  supplier_id: string;
  supplier_name: string;
  distance: number;
  similarity: number;
}

export interface SupplierSimilarityResponse {
  supplier_id: string;
  similar_suppliers: SimilarSupplier[];
  method: string;
}

export interface TrendSignal {
  signal_name: string;
  current_value: number;
  baseline_value: number;
  delta_pct: number;
  direction: "declining" | "stable" | "improving";
  severity: "normal" | "watch" | "warning" | "critical";
}

export interface EarlyWarning {
  supplier_id: string;
  supplier_name: string;
  risk_score: number;
  confidence: number;
  signals: TrendSignal[];
  pattern: string;
  recommendation: string;
  lead_time_weeks: number;
}

export interface EarlyWarningResponse {
  warnings: EarlyWarning[];
  monitored_suppliers: number;
  active_warnings: number;
  patterns_detected: number;
}

export interface ConservationStatus {
  engine_version?: string;
  source?: string;
  status?: string;
  auto_approve_rate?: number;
  autoApproveRate?: number;
  accuracy?: number;
  verified_decisions?: number;
  verifiedDecisions?: number;
  verified_count?: number;
  verifiedCount?: number;
  penalty_ratio?: number;
  penaltyRatio?: number;
  theta_min?: number;
  thetaMin?: number;
  q?: number;
  conservation_product?: number;
  conservationProduct?: number;
  passed?: boolean;
}

export interface PreviewQueueResponse {
  engine_version?: string;
  exceptions: InvoiceException[];
  total: number;
  auto_approve_rate?: number;
  autoApproveRate?: number;
  confidence_avg?: number;
  confidenceAvg?: number;
}

export interface PreviewSuppliersResponse {
  engine_version?: string;
  suppliers: SupplierProfile[];
  total: number;
}

export interface ExceptionQueueResponse {
  exceptions: InvoiceException[];
  total: number;
}

export interface ProcessContext {
  bottleneck_activity?: string;
  bottleneckActivity?: string;
  duration_median_min?: number;
  durationMedianMin?: number;
  cause?: string;
  root_cause?: string;
  rootCause?: string;
  source?: string;
  cross_copilot_signal?: CrossCopilotSignal;
  crossCopilotSignal?: CrossCopilotSignal;
}

export interface CrossCopilotSignal {
  source: string;
  supplier: string;
  reliability: number;
  delta: number | null;
  warning: string;
  supplier_exception_history?: number;
  supplierExceptionHistory?: number;
  supplier_risk_rating?: number;
  supplierRiskRating?: number;
  timestamp?: number;
  ttl_days?: number;
  ttlDays?: number;
  provenance: ProvenanceTier;
}

export interface ScoreInvoiceRequest {
  event_id: string;
  category: string;
  amount: number;
  supplier_id: string;
  supplier_name?: string;
  contract_id?: string | null;
  supplier_risk_rating?: number;
  match_status?: number;
  amount_variance_ratio?: number;
  duplicate_score?: number;
  supplier_exception_history?: number;
  payment_terms_impact?: number;
  commodity_index_correlation?: number;
  tax_regulatory_compliance?: number;
}

export interface ScoreInvoiceResponse {
  event_id?: string;
  eventId?: string;
  category: string;
  action?: string;
  recommended_action?: string;
  recommendedAction?: string;
  scored_action?: string;
  scoredAction?: string;
  action_index?: number;
  actionIndex?: number;
  confidence: number;
  probabilities?: number[];
  factors?: FactorMap;
  factor_vector?: number[];
  factorVector?: number[];
  factor_names?: string[];
  factorNames?: string[];
  decision_id: string;
  decisionId?: string;
  process_context?: ProcessContext | null;
  processContext?: ProcessContext | null;
  active_variant?: S2PVariantSummary | null;
  activeVariant?: S2PVariantSummary | null;
  auto_approve?: AutoApproveDecision | null;
  autoApprove?: AutoApproveDecision | null;
  threshold_decision?: ThresholdDecision | null;
  thresholdDecision?: ThresholdDecision | null;
}

export interface ThresholdDecision {
  decision: "REJECT" | "APPROVE" | string;
  reason: string;
  cost_of_error?: string;
  costOfError?: string;
  price_variance_pct?: number;
  priceVariancePct?: number;
  threshold_pct?: number;
  thresholdPct?: number;
  provenance?: "sample" | "live" | string;
}

export interface AutoApproveDecision {
  auto_approved: boolean;
  autoApproved?: boolean;
  reason: string;
  threshold: number | null;
  spot_check: boolean;
  spotCheck?: boolean;
  category: string;
  confidence?: number;
  conservation_status?: string;
  conservationStatus?: string;
  action?: string;
}

export interface AutoApproveCategoryStats {
  approved: number;
  held: number;
  threshold: number | null;
}

export interface AutoApproveStats {
  total_auto_approved: number;
  totalAutoApproved?: number;
  total_spot_checked: number;
  totalSpotChecked?: number;
  spot_check_accuracy: number;
  spotCheckAccuracy?: number;
  per_category: Record<string, AutoApproveCategoryStats>;
  perCategory?: Record<string, AutoApproveCategoryStats>;
  current_auto_approve_rate: number;
  currentAutoApproveRate?: number;
  source?: string;
}

export interface ExpansionProof {
  category: string;
  current_threshold: number;
  currentThreshold?: number;
  proposed_threshold: number;
  proposedThreshold?: number;
  verified_decisions: number;
  verifiedDecisions?: number;
  accuracy: number;
  conservation_status: string;
  conservationStatus?: string;
  safe_to_expand: boolean;
  safeToExpand?: boolean;
  evidence: string;
  rollback_available: boolean;
  rollbackAvailable?: boolean;
}

export interface LearnDecisionRequest {
  decision_id: string;
  actual_action: string;
  outcome?: "confirmed" | "confirm" | "override" | string;
  reason_code?: S2PReasonCode | string;
  variant_id?: string;
  variantId?: string;
  context?: {
    amount?: number;
    at_risk?: number;
    recovery_pct?: number;
    [key: string]: unknown;
  };
}

export interface EvidenceTemplateResponse {
  invoice_id: string;
  category: string;
  template: string;
  rendered: string;
  variables: Record<string, string | number | boolean | null | undefined>;
}

export interface ContextChainNode {
  node: string;
  id: string;
  properties: Record<string, unknown>;
  depth: number;
  provenance: ProvenanceTier;
}

export interface SituationResponse {
  decision_id: string;
  category: string;
  context_chain: ContextChainNode[];
  nl_explanation: string;
  confidence: number;
  factors_used: string[];
  traversal_depth: number;
  context_available: boolean;
  warnings: string[];
  missing_variables: string[];
  provenance: {
    nl_explanation: ProvenanceTier;
    confidence: ProvenanceTier;
    overall: ProvenanceTier;
  };
}

export interface LearnDecisionResponse {
  decision_id?: string;
  decisionId?: string;
  outcome?: string;
  learning_applied?: boolean;
  learningApplied?: boolean;
  learned?: boolean;
  reward?: number;
  reward_raw?: number;
  rewardRaw?: number;
  decisions_total?: number;
  decisionsTotal?: number;
  centroid_delta?: number;
  centroidDelta?: number;
  active_variant_id?: string;
  activeVariantId?: string;
  evolution_recorded?: boolean;
  evolutionRecorded?: boolean;
  evolution_note?: string;
  evolutionNote?: string;
}

export interface FingerprintResponse {
  invoice_id?: string;
  invoiceId?: string;
  category?: string;
  factors?: FactorMap;
  dominant_factor?: string | null;
  dominantFactor?: string | null;
  error?: string;
}

export interface SimilarInvoice {
  invoice_id?: string;
  invoiceId?: string;
  distance: number;
  category?: string;
  amount?: number;
  supplier?: string | null;
}

export interface SimilarResponse {
  invoice_id?: string;
  invoiceId?: string;
  similar: SimilarInvoice[];
  count: number;
  error?: string;
}

export interface CrossGraphInsight {
  supplier_id?: string;
  supplierId?: string;
  supplier?: string;
  exception_rate?: number;
  exceptionRate?: number;
  commodity?: string;
  category?: string;
  impact_score?: number;
  impactScore?: number;
}

export interface CrossGraphResponse {
  insights: CrossGraphInsight[];
  count: number;
  bottleneck_duration?: number;
  bottleneckDuration?: number;
  bottleneck_activity?: string;
  bottleneckActivity?: string;
}

export interface ProcessActivity {
  id?: string;
  activity_id?: string;
  activityId?: string;
  name?: string;
  activity?: string;
  avg_duration_hours?: number;
  avgDurationHours?: number;
  duration_median_hours?: number;
  durationMedianHours?: number;
  system?: string;
  status?: string;
  bottleneck?: boolean;
  bottleneck_cause?: string;
  bottleneckCause?: string;
}

export interface ProcessSignalsResponse {
  available: boolean;
  supplier_id?: string | null;
  supplierId?: string | null;
  process_model?: string;
  processModel?: string;
  variant?: string;
  activities: ProcessActivity[];
  recommendations: Array<Record<string, unknown>>;
  source?: string | null;
}

export interface ProcessFusionResponse {
  where: {
    bottleneck: string;
    activity: string;
    avg_duration_hours: number;
    vs_benchmark_hours: number;
  };
  what: {
    pattern: string;
    exception_rate: number;
    vs_org_rate: number;
  };
  why: {
    root_cause: string;
    situation_analysis: string;
  };
  which_decision: {
    recommendation: string;
    estimated_impact: string;
    provenance: string;
    confidence: number;
  };
  ingest_summary?: Record<string, unknown>;
}

export interface AuditTrailDecision {
  decision_id?: string;
  decisionId?: string;
  entity_id?: string;
  entityId?: string;
  category?: string;
  action?: string;
  recommended_action?: string;
  recommendedAction?: string;
  actual_action?: string;
  actualAction?: string;
  confidence?: number;
  is_correct?: boolean;
  isCorrect?: boolean;
  metadata?: Record<string, unknown>;
  factors?: FactorMap;
}

export interface AuditTrailResponse {
  invoice_id?: string;
  invoiceId?: string;
  decisions: AuditTrailDecision[];
  count: number;
}

export interface RuleLifecycle {
  rule_id?: string;
  ruleId?: string;
  name: string;
  state: "proposed" | "shadow" | "promoted" | "rejected" | string;
  action?: string;
  factor?: string;
}

export interface RuleLifecycleResponse {
  rules: RuleLifecycle[];
  count: number;
  source?: string;
  note?: string;
}

export interface S2PEvolutionRule extends RuleLifecycle {
  label?: string;
  success_metric_name?: string;
  successMetricName?: string;
  applicable_categories?: string[];
  applicableCategories?: string[];
  variant_count?: number;
  variantCount?: number;
}

export interface S2PEvolutionRulesResponse {
  rules: S2PEvolutionRule[];
  count?: number;
  total?: number;
}

export interface S2PEvolutionVariant {
  id?: string;
  variant_id?: string;
  variantId?: string;
  template_name?: string;
  templateName?: string;
  category?: string;
  categories?: string[];
  parameter?: string;
  win_rate?: number;
  winRate?: number;
  sample_size?: number;
  sampleSize?: number;
  status?: string;
  source?: string;
  description?: string;
  [key: string]: unknown;
}

export interface S2PVariantSummary {
  id: string;
  family: string;
  version?: number;
  status: string;
  metadata?: Record<string, unknown>;
  successes?: number;
  failures?: number;
  total?: number;
  success_rate?: number;
  successRate?: number;
}

export interface S2PEvolutionSummary {
  domain?: string;
  variant_count?: number;
  variantCount?: number;
  active_count?: number;
  activeCount?: number;
  families?: string[];
  categories?: string[];
  variants: S2PVariantSummary[];
}

export interface S2PEvolutionVariantsResponse {
  variants: S2PEvolutionVariant[];
  total?: number;
  sdk_summary?: S2PEvolutionSummary;
  sdkSummary?: S2PEvolutionSummary;
}

export interface S2PPromotionResult {
  family?: string;
  promoted_id?: string;
  promotedId?: string;
  previous_id?: string;
  previousId?: string;
  improvement?: number;
  candidate_rate?: number;
  candidateRate?: number;
  active_rate?: number;
  activeRate?: number;
  candidate_total?: number;
  candidateTotal?: number;
}

export interface S2PPromotionCheckResponse {
  promotion?: S2PPromotionResult | null;
}

export interface S2PShadowResult {
  variant_id?: string;
  variantId?: string;
  metric_name?: string;
  metricName?: string;
  better?: boolean;
  win?: boolean;
  accuracy?: number;
  baseline_accuracy?: number;
  baselineAccuracy?: number;
  regression?: boolean;
  sample_size?: number;
  sampleSize?: number;
  [key: string]: unknown;
}

export interface S2PShadowResultsResponse {
  variant_id?: string;
  variantId?: string;
  total_variants?: number;
  totalVariants?: number;
  results?: Record<string, S2PShadowResult[]> | S2PShadowResult[];
}

export interface S2PPromotedResponse {
  promoted?: Record<string, unknown> | null;
}

export interface ComplianceInvoice {
  invoice_id?: string;
  invoiceId?: string;
  category?: string;
  supplier_id?: string;
  supplierId?: string;
  tax_regulatory_compliance?: number;
  taxRegulatoryCompliance?: number;
  recommended_action?: string;
  recommendedAction?: string;
}

export interface ComplianceResponse {
  total: number;
  compliant: number;
  compliant_pct?: number;
  compliantPct?: number;
  flagged_count?: number;
  flaggedCount?: number;
  flagged_invoices?: ComplianceInvoice[];
  flaggedInvoices?: ComplianceInvoice[];
  factor?: string;
}

export interface PerformanceTrajectoryPoint {
  decision_id?: string;
  decisionId?: string;
  category?: string;
  created_at?: string;
  createdAt?: string;
  centroids?: unknown;
  [key: string]: unknown;
}

export interface PerformanceTrajectoryResponse {
  points: PerformanceTrajectoryPoint[];
  total_checkpoints?: number;
  totalCheckpoints?: number;
  verified?: number;
  current_q?: number;
  currentQ?: number;
}

export interface WhatIfResponse {
  current: {
    verified: number;
    correct: number;
    q: number;
  };
  additional: {
    correct: number;
    incorrect: number;
  };
  projected: {
    verified: number;
    correct: number;
    q: number;
    theta_min?: number;
    thetaMin?: number;
    status: string;
  };
  penalty_ratio?: number;
  penaltyRatio?: number;
}

export interface PerformanceSummaryResponse {
  total_scored?: number;
  totalScored?: number;
  total_verified?: number;
  totalVerified?: number;
  accuracy?: number;
  auto_approve_rate?: number;
  autoApproveRate?: number;
  savings_estimate_usd?: number;
  savingsEstimateUsd?: number;
  annual_target_usd?: number;
  annualTargetUsd?: number;
  penalty_ratio?: number;
  penaltyRatio?: number;
}

export interface NoveltyPerCategory {
  total_in_window?: number;
  novelty_count?: number;
  novelty_rate?: number;
  alert_active?: boolean;
  conservation_review?: boolean;
  recommendation?: string;
  status?: string;
  [key: string]: number | boolean | string | undefined;
}

export interface NoveltyStatusResponse {
  window_size: number;
  distance_threshold: number;
  total_in_window: number;
  novelty_count: number;
  novelty_rate: number;
  alert_active: boolean;
  conservation_review?: boolean;
  recommendation?: string;
  review_categories?: Array<Record<string, unknown>>;
  status?: string;
  per_category: Record<string, NoveltyPerCategory | number>;
}

export interface NoveltyHistoryEntry {
  sequence?: number;
  category?: string;
  nearest_distance?: number;
  is_novel?: boolean;
  vector_norm?: number;
  timestamp?: string;
  [key: string]: unknown;
}

export interface NoveltyHistoryResponse {
  entries: NoveltyHistoryEntry[];
  total_in_window: number;
  alert_active: boolean;
}

export interface NoveltyTriggeredResponse {
  decisions: NoveltyHistoryEntry[];
  total: number;
}

export interface CentroidCell {
  category: string;
  category_index: number;
  action: string;
  action_index: number;
  factor_names: string[];
  centroid_vector: number[];
  source: "scorer_centroid" | string;
  read_only: boolean;
}

export interface CentroidAllResponse {
  cells: CentroidCell[];
  shape: {
    categories: number;
    actions: number;
    factors: number;
  };
  categories: string[];
  actions: string[];
  factors: string[];
  read_only: boolean;
}

export interface FactorContribution {
  factor_name: string;
  factor_index: number;
  factor_value: number;
  centroid_value: number;
  distance: number;
  dk_weight: number;
  dk_status: "available" | "learning" | "unavailable" | string;
  weighted_distance: number;
  direction: "above_centroid" | "below_centroid" | "at_centroid" | string;
}

export interface ProvenanceDisplayValue {
  value: unknown;
  source?: string;
  provenance_tier?: string;
  provenance_label?: string;
  measured?: boolean;
  verified?: boolean;
  factor_eligible?: boolean;
}

export interface CentroidExplanation {
  decision_id: string;
  category: string;
  recommended_action: string;
  closest_action: string;
  closest_matches_recommendation: boolean;
  factor_names: string[];
  factor_contributions: FactorContribution[];
  centroid_distances: Record<string, number>;
  summary: string;
  dk_status: "available" | "learning" | "unavailable" | string;
  p39_evidence: Record<string, ProvenanceDisplayValue>;
  read_only: boolean;
}

export interface DriftPoint {
  timestamp?: string | null;
  verified_count?: number | null;
  centroid_vector?: number[];
  distance_from_previous?: number | null;
}

export interface DriftResponse {
  category: string;
  action: string;
  supported: boolean;
  reason: string;
  points: DriftPoint[];
}

export type CentroidResponse = CentroidCell;

export interface DKWeightsResponse {
  factors: string[];
  weights: number[];
  available: boolean;
}

export interface OutcomeReceipt {
  receipt_id: string;
  invoice_id: string;
  timestamp: string;
  scored_action: string;
  confidence?: number;
  factor_vector?: number[];
  category: string;
  human_action: string;
  override_reason?: string | null;
  reward?: number;
  centroid_updated?: boolean;
  conservation_state_before?: string;
  conservation_state_after?: string;
  verified_count_before?: number;
  verified_count_after?: number;
  previous_hash?: string;
  receipt_hash: string;
}

export interface ReceiptStats {
  total_receipts: number;
  confirms: number;
  overrides: number;
  override_rate: number;
  chain_valid: boolean;
}

export interface ReceiptsResponse {
  receipts: OutcomeReceipt[];
  stats: ReceiptStats;
}

export interface ChainIntegrityResponse {
  verified: boolean;
  count?: number;
  broken_at?: number | null;
  reason?: string;
  [key: string]: unknown;
}

export interface AuditPackResponse {
  export_timestamp: string;
  receipt_count: number;
  chain_integrity: ChainIntegrityResponse;
  conservation_state: Record<string, unknown>;
  override_distribution: Record<string, number>;
  override_count: number;
  confirm_count: number;
  receipts: OutcomeReceipt[];
}

export interface SimulationMitigation {
  action: string;
  effort: string;
  impact_reduction: number;
  description: string;
}

export interface SimulationScenario {
  scenario_id: string;
  name: string;
  type: string;
  description: string;
  affected_suppliers: string[];
  affected_categories: string[];
  trigger: string;
  conservation_impact: string;
  estimated_quarterly_cost: number;
  recovery_time_days: number;
  mitigation?: {
    recommended?: string;
    available_actions?: SimulationMitigation[];
  };
  impact?: Record<string, string | number | boolean>;
}

export interface SimulationScenariosResponse {
  scenarios: SimulationScenario[];
  total: number;
}

export interface ImpactSummaryResponse {
  total_scenarios: number;
  total_quarterly_exposure: number;
  worst_case_recovery_days: number;
  scenarios_causing_red: number;
  scenarios_causing_amber: number;
  scenarios_green_safe: number;
}

export interface FinancialImpactBucket {
  count: number;
  amount: number;
  at_risk: number;
  recovered: number;
}

export interface FinancialImpactSummaryResponse {
  total_decisions: number;
  verified_decisions: number;
  total_amount: number;
  total_at_risk: number;
  total_recovered: number;
  net_savings: number;
  recovery_rate: number;
  missing_receipts: number;
  by_supplier: Record<string, FinancialImpactBucket>;
  by_category: Record<string, FinancialImpactBucket>;
}

export interface FinancialImpactCategoryResponse extends FinancialImpactSummaryResponse {
  category: string;
  allowed_categories: string[];
}

export interface FinancialImpactTrendPoint {
  week: string;
  start_date?: string | null;
  end_date?: string | null;
  total_decisions: number;
  verified_decisions: number;
  total_amount: number;
  total_at_risk: number;
  total_recovered: number;
  net_savings: number;
  recovery_rate: number;
  missing_receipts: number;
}

export interface FinancialImpactTrendResponse {
  window_weeks: number;
  as_of?: string | null;
  points: FinancialImpactTrendPoint[];
  totals: FinancialImpactSummaryResponse;
}

export interface ExtendedDiscovery {
  discovery_id: string;
  title: string;
  type: string;
  sources: string[];
  correlation_strength: number;
  confidence: number;
  impact_estimate: string;
  supplier_ids: string[];
  pattern: string;
  first_detected: string;
  detection_count: number;
  recommendation: string;
  propagation_path: string[];
}

export interface ExtendedDiscoveryResponse {
  discoveries: ExtendedDiscovery[];
  total: number;
  per_supplier: Record<string, {
    supplier_id: string;
    discovery_count: number;
    detection_count: number;
    highest_correlation: number;
  }>;
  by_type: Record<string, number>;
  sources_connected: number;
}

export interface ComplianceScreeningResponse {
  screening_timestamp: string;
  total_decisions_screened: number;
  compliant: number;
  with_gaps: number;
  compliance_rate: number;
  chain_integrity: ChainIntegrityResponse;
  conservation_state: Record<string, unknown>;
  receipt_stats: ReceiptStats;
  gaps: Array<Record<string, unknown>>;
  eu_ai_act: {
    article_14_traceable: boolean;
    human_oversight_documented: boolean;
    automated_decision_logged: boolean;
  };
  sox_readiness: {
    hash_chain_valid: boolean;
    override_distribution_available: boolean;
    conservation_proof_available: boolean;
    score: number;
  };
}

export interface SupplierRecommendation {
  supplier_id: string;
  name: string;
  recommendation: "grow" | "maintain" | "phase_out" | string;
  exception_rate: number;
  otif: number;
  trend: string;
  region?: string;
  total_invoices?: number;
  reason: string;
  action: string;
}

export interface RationalizationSavings {
  currency: string;
  estimated_quarterly_savings: number;
  estimated_annual_savings: number;
  phase_out_invoice_volume: number;
  total_invoice_volume: number;
  suppliers_affected: number;
  basis: string;
}

export interface RationalizationResponse {
  total_suppliers: number;
  grow: number;
  maintain: number;
  phase_out: number;
  recommendations: SupplierRecommendation[];
  estimated_savings: RationalizationSavings;
}
