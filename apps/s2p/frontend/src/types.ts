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
}

export interface LearnDecisionRequest {
  decision_id: string;
  actual_action: string;
  outcome?: "confirmed" | "confirm" | "override" | string;
  context?: {
    amount?: number;
    at_risk?: number;
    recovery_pct?: number;
    [key: string]: unknown;
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
