import type {
  AuditPackResponse,
  AutoApproveStats,
  CentroidAllResponse,
  CentroidCell,
  CentroidExplanation,
  CentroidResponse,
  ClusteringResponse,
  ConservationStatus,
  AuditTrailResponse,
  ChainIntegrityResponse,
  ComplianceScreeningResponse,
  ComplianceResponse,
  CrossGraphResponse,
  DKWeightsResponse,
  DiscoveryResponse,
  DriftResponse,
  DisruptionResponse,
  EvidenceTemplateResponse,
  EarlyWarningResponse,
  ExtendedDiscoveryResponse,
  ExpansionProof,
  ExceptionQueueResponse,
  FingerprintResponse,
  FinancialImpactCategoryResponse,
  FinancialImpactSummaryResponse,
  FinancialImpactTrendResponse,
  ImpactSummaryResponse,
  LearnDecisionRequest,
  LearnDecisionResponse,
  PaymentBehavior,
  PaymentOptimizationResponse,
  PerformanceSummaryResponse,
  PerformanceTrajectoryResponse,
  ProcessSignalsResponse,
  ProcessContextDetail,
  ProcessFusionResponse,
  PreviewQueueResponse,
  PreviewSuppliersResponse,
  PromotionStatusResponse,
  RuleLifecycleResponse,
  S2PEvolutionRulesResponse,
  S2PEvolutionVariantsResponse,
  S2PPromotionCheckResponse,
  S2PPromotedResponse,
  S2PShadowResultsResponse,
  SupplierHistoryResponse,
  SupplierSimilarityResponse,
  SupplierProfileDetail,
  SupplierProfile,
  SupplierProfilesResponse,
  TwinDriftReport,
  TwinStatusResponse,
  TrendSignal,
  NoveltyHistoryResponse,
  NoveltyTriggeredResponse,
  NoveltyStatusResponse,
  ReceiptsResponse,
  RationalizationResponse,
  ScoreInvoiceRequest,
  ScoreInvoiceResponse,
  SimilarResponse,
  SimulationScenariosResponse,
  SituationResponse,
  WhatIfResponse
} from "./types";

const HOST = import.meta.env.VITE_COPILOT_HOST || "127.0.0.1";
export const API_URL = import.meta.env.VITE_API_URL || `http://${HOST}:8002`;

export async function apiGet<T>(path: string, timeoutMs = 15_000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${API_URL}${path}`, { signal: controller.signal });
    if (!response.ok) {
      throw new Error(`GET ${path} failed with ${response.status}`);
    }
    return response.json() as Promise<T>;
  } finally {
    clearTimeout(timer);
  }
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`POST ${path} failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export interface CohortExperiment {
  name?: string;
  injected_lift?: number | null;
  injectedLift?: number | null;
  recovered_lift?: number | null;
  recoveredLift?: number | null;
  pass?: boolean;
}

export interface CohortStatusResponse {
  state?: "INSTRUMENT_VALIDATED" | "ACCUMULATING" | "MEASURED" | string;
  instrument?: {
    validated?: boolean;
    provenance?: string;
    source_artifact?: string;
    sourceArtifact?: string;
    experiments?: CohortExperiment[];
  };
  real?: {
    treatment_n?: number;
    treatmentN?: number;
    control_n?: number;
    controlN?: number;
    threshold_k?: number;
    thresholdK?: number;
    magnitude?: number | null;
    provenance?: string;
    status?: string;
  };
  structure?: {
    present?: boolean;
    treatment_n?: number;
    treatmentN?: number;
    control_n?: number;
    controlN?: number;
    provenance?: string;
  };
}

export async function getCohortStatus(): Promise<CohortStatusResponse> {
  return apiGet<CohortStatusResponse>("/api/s2p/cohort-status");
}

export async function getPreviewQueue(): Promise<PreviewQueueResponse> {
  return apiGet<PreviewQueueResponse>("/api/s2p/preview/queue");
}

export async function fetchPreviewQueue(): Promise<PreviewQueueResponse> {
  return getPreviewQueue();
}

export async function getPreviewConservation(): Promise<ConservationStatus> {
  return apiGet<ConservationStatus>("/api/s2p/preview/conservation");
}

export async function fetchPromotionStatus(): Promise<PromotionStatusResponse> {
  return apiGet<PromotionStatusResponse>("/api/s2p/promotion/status");
}

export async function advanceS2PPromotion(
  category: string,
  evidence: Record<string, unknown>
): Promise<Record<string, unknown>> {
  return apiPost<Record<string, unknown>>(
    `/api/s2p/promotion/${encodeURIComponent(category)}/advance`,
    evidence,
  );
}

export async function fetchTwinStatus(): Promise<TwinStatusResponse> {
  return apiGet<TwinStatusResponse>("/api/s2p/twin/status");
}

export async function fetchTwinDrift(): Promise<TwinDriftReport> {
  return apiGet<TwinDriftReport>("/api/s2p/twin/drift");
}

export async function getPreviewSuppliers(): Promise<PreviewSuppliersResponse> {
  return apiGet<PreviewSuppliersResponse>("/api/s2p/preview/suppliers");
}

export async function getFingerprint(invoiceId: string): Promise<FingerprintResponse> {
  return apiGet<FingerprintResponse>(
    `/api/s2p/insight/fingerprint?invoice_id=${encodeURIComponent(invoiceId)}`
  );
}

export async function getTrajectory(): Promise<PerformanceTrajectoryResponse> {
  return apiGet<PerformanceTrajectoryResponse>("/api/s2p/performance/trajectory");
}

export async function getConservationStatus(): Promise<ConservationStatus> {
  return apiGet<ConservationStatus>("/api/conservation/status").catch(() =>
    apiGet<ConservationStatus>("/api/s2p/preview/conservation")
  );
}

export async function fetchConservation(): Promise<ConservationStatus> {
  return getConservationStatus();
}

export async function getExceptionQueue(): Promise<ExceptionQueueResponse> {
  return getPreviewQueue();
}

export async function scoreException(payload: unknown): Promise<unknown> {
  return apiPost<unknown>("/api/s2p/score", payload);
}

export async function verifyDecision(payload: unknown): Promise<unknown> {
  return apiPost<unknown>("/api/s2p/outcome", payload);
}

export async function scoreInvoice(payload: ScoreInvoiceRequest): Promise<ScoreInvoiceResponse> {
  return apiPost<ScoreInvoiceResponse>("/api/s2p/score", payload);
}

export async function learnDecision(payload: LearnDecisionRequest): Promise<LearnDecisionResponse> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 90_000);
  try {
    return await apiPostWithSignal<LearnDecisionResponse>("/api/learn", payload, controller.signal);
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("Learn request timed out after 90s");
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

async function apiPostWithSignal<T>(path: string, body: unknown, signal: AbortSignal): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!response.ok) throw new Error(`POST ${path} failed with ${response.status}`);
  return response.json() as Promise<T>;
}

export async function getEvidenceTemplate(
  invoiceId: string,
  category: string
): Promise<EvidenceTemplateResponse> {
  const params = new URLSearchParams({ invoice_id: invoiceId, category });
  return apiGet<EvidenceTemplateResponse>(`/api/s2p/evidence/template?${params.toString()}`);
}

export async function getSupplierProfile(id: string): Promise<SupplierProfileDetail> {
  return fetchSupplierProfile(id);
}

export async function fetchS2PFingerprint(invoiceId: string): Promise<FingerprintResponse> {
  return apiGet<FingerprintResponse>(
    `/api/s2p/insight/fingerprint?invoice_id=${encodeURIComponent(invoiceId)}`
  );
}

export async function fetchS2PSimilar(invoiceId: string, limit = 5): Promise<SimilarResponse> {
  const params = new URLSearchParams({ invoice_id: invoiceId, limit: String(limit) });
  return apiGet<SimilarResponse>(`/api/s2p/insight/similar?${params.toString()}`);
}

export async function fetchSituation(
  decisionId: string,
  maxDepth = 3,
  signal?: AbortSignal,
): Promise<SituationResponse> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10_000);
  const abortExternal = () => controller.abort();
  signal?.addEventListener("abort", abortExternal, { once: true });
  try {
    const response = await fetch(
      `${API_URL}/api/s2p/situation/${encodeURIComponent(decisionId)}?max_depth=${maxDepth}`,
      { signal: controller.signal },
    );
    if (!response.ok) {
      throw new Error(`GET /api/s2p/situation/${encodeURIComponent(decisionId)} failed with ${response.status}`);
    }
    return await response.json() as SituationResponse;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      return {
        decision_id: decisionId,
        category: "",
        status: "timeout",
        reason: "Situation request exceeded its deadline",
        context_source: "scorer_only",
        context_chain: [],
        nl_explanation: "Situation context unavailable; factor-based scoring was used.",
        confidence: 0,
        factors_used: [],
        traversal_depth: 0,
        context_available: false,
        warnings: ["Situation request exceeded its deadline"],
        missing_variables: [],
        provenance: { nl_explanation: "learned", confidence: "learned", overall: "learned" },
      };
    }
    throw error;
  } finally {
    clearTimeout(timeout);
    signal?.removeEventListener("abort", abortExternal);
  }
}

export async function getSimilarInvoices(invoiceId: string, limit = 5): Promise<SimilarResponse> {
  return fetchS2PSimilar(invoiceId, limit);
}

export async function fetchS2PCrossGraph(): Promise<CrossGraphResponse> {
  return apiGet<CrossGraphResponse>("/api/s2p/insight/cross-graph");
}

export async function fetchS2PProcessSignals(supplierId?: string): Promise<ProcessSignalsResponse> {
  const params = new URLSearchParams();
  if (supplierId) params.set("supplier_id", supplierId);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return apiGet<ProcessSignalsResponse>(`/api/s2p/insight/process-signals${suffix}`);
}

export async function fetchS2PProcessContext(invoiceId: string): Promise<ProcessContextDetail> {
  return apiGet<ProcessContextDetail>(
    `/api/s2p/insight/process-context/${encodeURIComponent(invoiceId)}`
  );
}

export async function fetchProcessFusion(events: Array<Record<string, unknown>>): Promise<ProcessFusionResponse> {
  return apiPost<ProcessFusionResponse>("/api/s2p/enterprise/process-fusion", events);
}

export async function getEarlyWarnings(): Promise<EarlyWarningResponse> {
  return apiGet<EarlyWarningResponse>("/api/s2p/suppliers/early-warnings");
}

export async function getTrendSignals(
  supplierId: string
): Promise<{ supplier_id: string; signals: TrendSignal[] }> {
  const params = new URLSearchParams({ supplier_id: supplierId });
  return apiGet<{ supplier_id: string; signals: TrendSignal[] }>(
    `/api/s2p/suppliers/trend-signals?${params.toString()}`
  );
}

export async function fetchS2PAuditTrail(invoiceId: string): Promise<AuditTrailResponse> {
  return apiGet<AuditTrailResponse>(
    `/api/s2p/evidence/audit-trail/${encodeURIComponent(invoiceId)}`
  );
}

export async function getAuditTrail(invoiceId: string): Promise<AuditTrailResponse> {
  return fetchS2PAuditTrail(invoiceId);
}

export async function fetchS2PRules(): Promise<RuleLifecycleResponse> {
  return apiGet<RuleLifecycleResponse>("/api/s2p/evidence/rules");
}

export async function fetchS2PEvolutionRules(): Promise<S2PEvolutionRulesResponse> {
  return apiGet<S2PEvolutionRulesResponse>("/api/s2p/evolution/rules");
}

export async function fetchS2PEvolutionVariants(): Promise<S2PEvolutionVariantsResponse> {
  return apiGet<S2PEvolutionVariantsResponse>("/api/s2p/evolution/variants");
}

export async function getS2PEvolutionVariants(): Promise<S2PEvolutionVariantsResponse> {
  return fetchS2PEvolutionVariants();
}

export async function getS2PPromotionCheck(): Promise<S2PPromotionCheckResponse> {
  return apiGet<S2PPromotionCheckResponse>("/api/s2p/evolution/promotion-check");
}

export async function resetS2PEvolution(): Promise<{ status: string }> {
  return apiPost<{ status: string }>("/api/s2p/evolution/reset", {});
}

export async function fetchS2PShadowResults(): Promise<S2PShadowResultsResponse> {
  return apiGet<S2PShadowResultsResponse>("/api/s2p/evolution/shadow-results");
}

export async function fetchS2PPromotedRules(): Promise<S2PPromotedResponse> {
  return apiGet<S2PPromotedResponse>("/api/s2p/evolution/promoted");
}

export async function fetchS2PCompliance(): Promise<ComplianceResponse> {
  return apiGet<ComplianceResponse>("/api/s2p/evidence/compliance");
}

export async function getDiscoveryAlerts(): Promise<DiscoveryResponse> {
  return apiGet<DiscoveryResponse>("/api/s2p/discovery/alerts");
}

export async function getDisruptionRecovery(): Promise<DisruptionResponse> {
  return apiGet<DisruptionResponse>("/api/s2p/discovery/disruptions");
}

export async function fetchS2PTrajectory(): Promise<PerformanceTrajectoryResponse> {
  return apiGet<PerformanceTrajectoryResponse>("/api/s2p/performance/trajectory");
}

export async function fetchS2PWhatIf(additionalCorrect: number, additionalIncorrect: number): Promise<WhatIfResponse> {
  const params = new URLSearchParams({
    additional_correct: String(additionalCorrect),
    additional_incorrect: String(additionalIncorrect)
  });
  return apiGet<WhatIfResponse>(`/api/s2p/performance/what-if?${params.toString()}`);
}

export async function fetchS2PSummary(): Promise<PerformanceSummaryResponse> {
  return apiGet<PerformanceSummaryResponse>("/api/s2p/performance/summary");
}

export async function getNoveltyStatus(): Promise<NoveltyStatusResponse> {
  return apiGet<NoveltyStatusResponse>("/api/s2p/novelty/status");
}

export async function getNoveltyHistory(limit = 50): Promise<NoveltyHistoryResponse> {
  const params = new URLSearchParams({ limit: String(limit) });
  return apiGet<NoveltyHistoryResponse>(`/api/s2p/novelty/history?${params.toString()}`);
}

export async function getNoveltyTriggeredDecisions(limit = 10): Promise<NoveltyTriggeredResponse> {
  const params = new URLSearchParams({ limit: String(limit) });
  return apiGet<NoveltyTriggeredResponse>(`/api/s2p/novelty/triggered-decisions?${params.toString()}`);
}

export async function getAllCentroids(): Promise<CentroidAllResponse> {
  return apiGet<CentroidAllResponse>("/api/s2p/centroid/all");
}

export async function getCentroid(category: string, action: string): Promise<CentroidCell> {
  return apiGet<CentroidResponse>(
    `/api/s2p/centroid/${encodeURIComponent(category)}/${encodeURIComponent(action)}`
  );
}

export async function getCentroidExplanation(decisionId: string): Promise<CentroidExplanation> {
  return apiGet<CentroidExplanation>(`/api/s2p/centroid/explain/${encodeURIComponent(decisionId)}`);
}

export async function getCentroidDrift(category: string, action: string): Promise<DriftResponse> {
  return apiGet<DriftResponse>(
    `/api/s2p/centroid/drift/${encodeURIComponent(category)}/${encodeURIComponent(action)}`
  );
}

export async function getDKWeights(): Promise<DKWeightsResponse> {
  return apiGet<DKWeightsResponse>("/api/s2p/explorer/dk-weights");
}

export interface FactorRecommendation {
  factor_name?: string;
  factorName?: string;
  current_dk_weight?: number;
  currentDkWeight?: number;
  signal_contribution_pct?: number;
  signalContributionPct?: number;
  outcome_correlation?: number;
  outcomeCorrelation?: number;
  verdict?: string;
  replacement_suggestion?: string | null;
  replacementSuggestion?: string | null;
  estimated_impact_pp?: number;
  estimatedImpactPp?: number;
}

export interface FactorAnalysisResponse {
  factors?: FactorRecommendation[];
  count?: number;
  advisory?: boolean;
}

export interface FactorRecommendationsResponse {
  recommendations?: FactorRecommendation[];
  count?: number;
  advisory?: boolean;
}

export interface FactorProposalResponse {
  factor?: string;
  replacement?: string;
  estimated_pp?: number;
  estimatedPp?: number;
  rationale?: string;
  advisory?: boolean;
}

export async function getFactorAnalysis(): Promise<FactorAnalysisResponse> {
  return apiGet<FactorAnalysisResponse>("/api/s2p/factors/analysis");
}

export async function getFactorRecommendations(): Promise<FactorRecommendationsResponse> {
  return apiGet<FactorRecommendationsResponse>("/api/s2p/factors/recommendations");
}

export async function proposeFactorReplacement(factor: string): Promise<FactorProposalResponse> {
  return apiPost<FactorProposalResponse>("/api/s2p/factors/propose", {
    factor,
    candidates: ["tariff_exposure", "supplier_geo_exposure", "cash_discount_capture"]
  });
}

export async function getReceipts(limit = 50): Promise<ReceiptsResponse> {
  const params = new URLSearchParams({ limit: String(limit) });
  return apiGet<ReceiptsResponse>(`/api/s2p/evidence/receipts?${params.toString()}`);
}

export async function getChainIntegrity(): Promise<ChainIntegrityResponse> {
  return apiGet<ChainIntegrityResponse>("/api/s2p/evidence/chain-integrity");
}

export async function getAuditPack(): Promise<AuditPackResponse> {
  return apiGet<AuditPackResponse>("/api/s2p/evidence/audit-pack");
}

export async function getSimulationScenarios(): Promise<SimulationScenariosResponse> {
  return apiGet<SimulationScenariosResponse>("/api/s2p/simulation/scenarios");
}

export async function getImpactSummary(): Promise<ImpactSummaryResponse> {
  return apiGet<ImpactSummaryResponse>("/api/s2p/simulation/impact-summary");
}

export async function getExtendedDiscoveries(): Promise<ExtendedDiscoveryResponse> {
  return apiGet<ExtendedDiscoveryResponse>("/api/s2p/discovery/extended");
}

export async function getComplianceScreening(): Promise<ComplianceScreeningResponse> {
  return apiGet<ComplianceScreeningResponse>("/api/s2p/governance/compliance-screening");
}

export async function getRationalizationRecs(): Promise<RationalizationResponse> {
  return apiGet<RationalizationResponse>("/api/s2p/governance/rationalization");
}

export async function fetchAutoApproveStats(): Promise<AutoApproveStats> {
  return apiGet<AutoApproveStats>("/api/s2p/auto-approve/stats");
}

export async function fetchExpansionProof(category?: string): Promise<ExpansionProof> {
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return apiGet<ExpansionProof>(`/api/s2p/auto-approve/expansion-proof${suffix}`);
}

export async function fetchIntents(): Promise<unknown> {
  return apiGet<unknown>("/api/s2p/control-tower/intents");
}

export async function classifyInvoice(invoiceId?: string, category?: string): Promise<unknown> {
  const params = new URLSearchParams();
  if (invoiceId) params.set("invoice_id", invoiceId);
  if (category) params.set("category", category);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return apiGet<unknown>(`/api/s2p/control-tower/classify${suffix}`);
}

export async function fetchCTQueue(limit = 20): Promise<unknown> {
  const params = new URLSearchParams({ limit: String(limit) });
  return apiGet<unknown>(`/api/s2p/control-tower/queue?${params.toString()}`);
}

export async function fetchVariants(): Promise<unknown> {
  return apiGet<unknown>("/api/s2p/pvg/variants");
}

export async function fetchImpact(period = "annual"): Promise<unknown> {
  const params = new URLSearchParams({ period });
  return apiGet<unknown>(`/api/s2p/pvg/impact?${params.toString()}`);
}

export async function fetchFinancialImpact(): Promise<FinancialImpactSummaryResponse> {
  return apiGet<FinancialImpactSummaryResponse>("/api/s2p/financial-impact");
}

export async function fetchFinancialImpactTrend(): Promise<FinancialImpactTrendResponse> {
  return apiGet<FinancialImpactTrendResponse>("/api/s2p/financial-impact/trend");
}

export async function fetchFinancialImpactCategory(category: string): Promise<FinancialImpactCategoryResponse> {
  return apiGet<FinancialImpactCategoryResponse>(
    `/api/s2p/financial-impact/${encodeURIComponent(category)}`
  );
}

export async function fetchLeakage(): Promise<unknown> {
  return apiGet<unknown>("/api/s2p/pvg/leakage");
}

export async function fetchCycleTime(): Promise<unknown> {
  return apiGet<unknown>("/api/s2p/pvg/cycle-time");
}

export async function fetchSuppliers(): Promise<SupplierProfilesResponse> {
  return fetchSupplierProfiles();
}

export async function fetchSupplierProfiles(): Promise<SupplierProfilesResponse> {
  return apiGet<SupplierProfilesResponse>("/api/s2p/suppliers");
}

export async function fetchDecliningSuppliers(): Promise<SupplierProfilesResponse> {
  return apiGet<SupplierProfilesResponse>("/api/s2p/suppliers/declining");
}

export async function fetchSupplierProfile(supplierId: string): Promise<SupplierProfileDetail> {
  return apiGet<SupplierProfileDetail>(`/api/s2p/suppliers/${encodeURIComponent(supplierId)}/profile`);
}

export async function fetchSupplierHistory(
  supplierId: string,
  limit = 200
): Promise<SupplierHistoryResponse> {
  const params = new URLSearchParams({ limit: String(limit) });
  return apiGet<SupplierHistoryResponse>(
    `/api/s2p/suppliers/${encodeURIComponent(supplierId)}/history?${params.toString()}`
  );
}

export async function fetchSupplierHeatmap(supplierId: string): Promise<unknown> {
  return apiGet<unknown>(`/api/s2p/suppliers/${encodeURIComponent(supplierId)}/heatmap`);
}

export async function getPaymentStrategy(): Promise<PaymentOptimizationResponse> {
  return apiGet<PaymentOptimizationResponse>("/api/s2p/suppliers/payment-strategy");
}

export async function getPaymentBehavior(supplierId: string): Promise<PaymentBehavior> {
  const params = new URLSearchParams({ supplier_id: supplierId });
  return apiGet<PaymentBehavior>(`/api/s2p/suppliers/payment-behavior?${params.toString()}`);
}

export async function fetchSupplierClustering(): Promise<unknown> {
  return apiGet<unknown>("/api/s2p/suppliers/clustering");
}

export async function getSupplierClusters(): Promise<ClusteringResponse> {
  return apiGet<ClusteringResponse>("/api/s2p/suppliers/clusters");
}

export async function getSupplierSimilarity(supplierId: string): Promise<SupplierSimilarityResponse> {
  const params = new URLSearchParams({ supplier_id: supplierId });
  return apiGet<SupplierSimilarityResponse>(`/api/s2p/suppliers/similarity?${params.toString()}`);
}
