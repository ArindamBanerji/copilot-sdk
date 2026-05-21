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
  supplier_id?: string;
  supplierId?: string;
  name: string;
  category?: string;
  exception_rate?: number;
  exceptionRate?: number;
  avg_invoice_amount?: number;
  avgInvoiceAmount?: number;
  payment_terms?: string;
  paymentTerms?: string;
  otif_score?: number;
  otifScore?: number;
  total_invoices?: number;
  totalInvoices?: number;
  total_exceptions?: number;
  totalExceptions?: number;
  recent_trend?: string;
  recentTrend?: string;
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
}

export interface ScoreInvoiceRequest {
  event_id: string;
  category: string;
  amount: number;
  supplier_id: string;
  contract_id?: string | null;
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
