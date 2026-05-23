import type {
  AuditPackResponse,
  AutoApproveStats,
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
  ImpactSummaryResponse,
  LearnDecisionRequest,
  LearnDecisionResponse,
  PaymentBehavior,
  PaymentOptimizationResponse,
  PerformanceSummaryResponse,
  PerformanceTrajectoryResponse,
  ProcessSignalsResponse,
  PreviewQueueResponse,
  PreviewSuppliersResponse,
  RuleLifecycleResponse,
  S2PEvolutionRulesResponse,
  S2PEvolutionVariantsResponse,
  S2PPromotionCheckResponse,
  S2PPromotedResponse,
  S2PShadowResultsResponse,
  SupplierHistoryResponse,
  SupplierSimilarityResponse,
  SupplierProfile,
  SupplierProfilesResponse,
  TrendSignal,
  NoveltyHistoryResponse,
  NoveltyStatusResponse,
  ReceiptsResponse,
  RationalizationResponse,
  ScoreInvoiceRequest,
  ScoreInvoiceResponse,
  SimilarResponse,
  SimulationScenariosResponse,
  WhatIfResponse
} from "./types";

export const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8002";

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`);
  if (!response.ok) {
    throw new Error(`GET ${path} failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    throw new Error(`POST ${path} failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function getPreviewQueue(): Promise<PreviewQueueResponse> {
  return apiGet<PreviewQueueResponse>("/api/s2p/preview/queue").catch(() => ({
    exceptions: [],
    total: 0,
    auto_approve_rate: 0,
    confidence_avg: 0
  }));
}

export async function fetchPreviewQueue(): Promise<PreviewQueueResponse> {
  return getPreviewQueue();
}

export async function getPreviewConservation(): Promise<ConservationStatus | null> {
  return apiGet<ConservationStatus>("/api/s2p/preview/conservation").catch(() => null);
}

export async function getPreviewSuppliers(): Promise<PreviewSuppliersResponse> {
  return apiGet<PreviewSuppliersResponse>("/api/s2p/preview/suppliers").catch(() => ({
    suppliers: [],
    total: 0
  }));
}

export async function getFingerprint(): Promise<unknown | null> {
  return apiGet<unknown>("/api/fingerprint").catch(() => null);
}

export async function getTrajectory(): Promise<unknown | null> {
  return apiGet<unknown>("/api/trajectory").catch(() => null);
}

export async function getConservationStatus(): Promise<ConservationStatus | null> {
  return apiGet<ConservationStatus>("/api/conservation/status").catch(() =>
    apiGet<ConservationStatus>("/api/s2p/preview/conservation").catch(() => null)
  );
}

export async function fetchConservation(): Promise<ConservationStatus | null> {
  return getConservationStatus();
}

export async function getExceptionQueue(): Promise<ExceptionQueueResponse> {
  return getPreviewQueue();
}

export async function scoreException(payload: unknown): Promise<unknown | null> {
  return apiPost<unknown>("/api/s2p/score", payload).catch(() => null);
}

export async function verifyDecision(payload: unknown): Promise<unknown | null> {
  return apiPost<unknown>("/api/s2p/outcome", payload).catch(() => null);
}

export async function scoreInvoice(payload: ScoreInvoiceRequest): Promise<ScoreInvoiceResponse | null> {
  return apiPost<ScoreInvoiceResponse>("/api/s2p/score", payload).catch(() => null);
}

export async function learnDecision(payload: LearnDecisionRequest): Promise<LearnDecisionResponse | null> {
  return apiPost<LearnDecisionResponse>("/api/learn", payload).catch(() => null);
}

export async function getEvidenceTemplate(
  invoiceId: string,
  category: string
): Promise<EvidenceTemplateResponse | null> {
  const params = new URLSearchParams({ invoice_id: invoiceId, category });
  return apiGet<EvidenceTemplateResponse>(`/api/s2p/evidence/template?${params.toString()}`).catch(() => null);
}

export async function getSupplierProfile(id: string): Promise<unknown | null> {
  return fetchSupplierProfile(id);
}

export async function fetchS2PFingerprint(invoiceId: string): Promise<FingerprintResponse | null> {
  return apiGet<FingerprintResponse>(
    `/api/s2p/insight/fingerprint?invoice_id=${encodeURIComponent(invoiceId)}`
  ).catch(() => null);
}

export async function fetchS2PSimilar(invoiceId: string, limit = 5): Promise<SimilarResponse | null> {
  const params = new URLSearchParams({ invoice_id: invoiceId, limit: String(limit) });
  return apiGet<SimilarResponse>(`/api/s2p/insight/similar?${params.toString()}`).catch(() => null);
}

export async function getSimilarInvoices(invoiceId: string, limit = 5): Promise<SimilarResponse | null> {
  return fetchS2PSimilar(invoiceId, limit);
}

export async function fetchS2PCrossGraph(): Promise<CrossGraphResponse | null> {
  return apiGet<CrossGraphResponse>("/api/s2p/insight/cross-graph").catch(() => null);
}

export async function fetchS2PProcessSignals(supplierId?: string): Promise<ProcessSignalsResponse | null> {
  const params = new URLSearchParams();
  if (supplierId) params.set("supplier_id", supplierId);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return apiGet<ProcessSignalsResponse>(`/api/s2p/insight/process-signals${suffix}`).catch(() => null);
}

export async function getEarlyWarnings(): Promise<EarlyWarningResponse | null> {
  return apiGet<EarlyWarningResponse>("/api/s2p/suppliers/early-warnings").catch(() => null);
}

export async function getTrendSignals(
  supplierId: string
): Promise<{ supplier_id: string; signals: TrendSignal[] } | null> {
  const params = new URLSearchParams({ supplier_id: supplierId });
  return apiGet<{ supplier_id: string; signals: TrendSignal[] }>(
    `/api/s2p/suppliers/trend-signals?${params.toString()}`
  ).catch(() => null);
}

export async function fetchS2PAuditTrail(invoiceId: string): Promise<AuditTrailResponse | null> {
  return apiGet<AuditTrailResponse>(
    `/api/s2p/evidence/audit-trail/${encodeURIComponent(invoiceId)}`
  ).catch(() => null);
}

export async function getAuditTrail(invoiceId: string): Promise<AuditTrailResponse | null> {
  return fetchS2PAuditTrail(invoiceId);
}

export async function fetchS2PRules(): Promise<RuleLifecycleResponse | null> {
  return apiGet<RuleLifecycleResponse>("/api/s2p/evidence/rules").catch(() => null);
}

export async function fetchS2PEvolutionRules(): Promise<S2PEvolutionRulesResponse | null> {
  return apiGet<S2PEvolutionRulesResponse>("/api/s2p/evolution/rules").catch(() => null);
}

export async function fetchS2PEvolutionVariants(): Promise<S2PEvolutionVariantsResponse | null> {
  return apiGet<S2PEvolutionVariantsResponse>("/api/s2p/evolution/variants").catch(() => null);
}

export async function getS2PEvolutionVariants(): Promise<S2PEvolutionVariantsResponse | null> {
  return fetchS2PEvolutionVariants();
}

export async function getS2PPromotionCheck(): Promise<S2PPromotionCheckResponse | null> {
  return apiGet<S2PPromotionCheckResponse>("/api/s2p/evolution/promotion-check").catch(() => null);
}

export async function resetS2PEvolution(): Promise<{ status: string } | null> {
  return apiPost<{ status: string }>("/api/s2p/evolution/reset", {}).catch(() => null);
}

export async function fetchS2PShadowResults(): Promise<S2PShadowResultsResponse | null> {
  return apiGet<S2PShadowResultsResponse>("/api/s2p/evolution/shadow-results").catch(() => null);
}

export async function fetchS2PPromotedRules(): Promise<S2PPromotedResponse | null> {
  return apiGet<S2PPromotedResponse>("/api/s2p/evolution/promoted").catch(() => null);
}

export async function fetchS2PCompliance(): Promise<ComplianceResponse | null> {
  return apiGet<ComplianceResponse>("/api/s2p/evidence/compliance").catch(() => null);
}

export async function getDiscoveryAlerts(): Promise<DiscoveryResponse | null> {
  return apiGetNullable<DiscoveryResponse>("/api/s2p/discovery/alerts");
}

export async function getDisruptionRecovery(): Promise<DisruptionResponse | null> {
  return apiGetNullable<DisruptionResponse>("/api/s2p/discovery/disruptions");
}

export async function fetchS2PTrajectory(): Promise<PerformanceTrajectoryResponse | null> {
  return apiGet<PerformanceTrajectoryResponse>("/api/s2p/performance/trajectory").catch(() => null);
}

export async function fetchS2PWhatIf(additionalCorrect: number, additionalIncorrect: number): Promise<WhatIfResponse | null> {
  const params = new URLSearchParams({
    additional_correct: String(additionalCorrect),
    additional_incorrect: String(additionalIncorrect)
  });
  return apiGet<WhatIfResponse>(`/api/s2p/performance/what-if?${params.toString()}`).catch(() => null);
}

export async function fetchS2PSummary(): Promise<PerformanceSummaryResponse | null> {
  return apiGet<PerformanceSummaryResponse>("/api/s2p/performance/summary").catch(() => null);
}

export async function getNoveltyStatus(): Promise<NoveltyStatusResponse | null> {
  return apiGet<NoveltyStatusResponse>("/api/s2p/novelty/status").catch(() => null);
}

export async function getNoveltyHistory(limit = 50): Promise<NoveltyHistoryResponse | null> {
  const params = new URLSearchParams({ limit: String(limit) });
  return apiGet<NoveltyHistoryResponse>(`/api/s2p/novelty/history?${params.toString()}`).catch(() => null);
}

export async function getCentroid(category: string, action: string): Promise<CentroidResponse | null> {
  return apiGet<CentroidResponse>(
    `/api/s2p/explorer/centroid/${encodeURIComponent(category)}/${encodeURIComponent(action)}`
  ).catch(() => null);
}

export async function getDrift(category: string): Promise<DriftResponse | null> {
  return apiGet<DriftResponse>(`/api/s2p/explorer/drift/${encodeURIComponent(category)}`).catch(() => null);
}

export async function getDKWeights(): Promise<DKWeightsResponse | null> {
  return apiGet<DKWeightsResponse>("/api/s2p/explorer/dk-weights").catch(() => null);
}

export async function getReceipts(limit = 50): Promise<ReceiptsResponse | null> {
  const params = new URLSearchParams({ limit: String(limit) });
  return apiGet<ReceiptsResponse>(`/api/s2p/evidence/receipts?${params.toString()}`).catch(() => null);
}

export async function getChainIntegrity(): Promise<ChainIntegrityResponse | null> {
  return apiGet<ChainIntegrityResponse>("/api/s2p/evidence/chain-integrity").catch(() => null);
}

export async function getAuditPack(): Promise<AuditPackResponse | null> {
  return apiGet<AuditPackResponse>("/api/s2p/evidence/audit-pack").catch(() => null);
}

export async function getSimulationScenarios(): Promise<SimulationScenariosResponse | null> {
  return apiGet<SimulationScenariosResponse>("/api/s2p/simulation/scenarios").catch(() => null);
}

export async function getImpactSummary(): Promise<ImpactSummaryResponse | null> {
  return apiGet<ImpactSummaryResponse>("/api/s2p/simulation/impact-summary").catch(() => null);
}

export async function getExtendedDiscoveries(): Promise<ExtendedDiscoveryResponse | null> {
  return apiGet<ExtendedDiscoveryResponse>("/api/s2p/discovery/extended").catch(() => null);
}

export async function getComplianceScreening(): Promise<ComplianceScreeningResponse | null> {
  return apiGet<ComplianceScreeningResponse>("/api/s2p/governance/compliance-screening").catch(() => null);
}

export async function getRationalizationRecs(): Promise<RationalizationResponse | null> {
  return apiGet<RationalizationResponse>("/api/s2p/governance/rationalization").catch(() => null);
}

export async function fetchAutoApproveStats(): Promise<AutoApproveStats | null> {
  return apiGet<AutoApproveStats>("/api/s2p/auto-approve/stats").catch(() => null);
}

export async function fetchExpansionProof(category?: string): Promise<ExpansionProof | null> {
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return apiGet<ExpansionProof>(`/api/s2p/auto-approve/expansion-proof${suffix}`).catch(() => null);
}

async function apiGetNullable<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(`${API_URL}${path}`);
    return response.ok ? ((await response.json()) as T) : null;
  } catch {
    return null;
  }
}

export async function fetchIntents(): Promise<unknown | null> {
  return apiGetNullable<unknown>("/api/s2p/control-tower/intents");
}

export async function classifyInvoice(invoiceId?: string, category?: string): Promise<unknown | null> {
  const params = new URLSearchParams();
  if (invoiceId) params.set("invoice_id", invoiceId);
  if (category) params.set("category", category);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return apiGetNullable<unknown>(`/api/s2p/control-tower/classify${suffix}`);
}

export async function fetchCTQueue(limit = 20): Promise<unknown | null> {
  const params = new URLSearchParams({ limit: String(limit) });
  return apiGetNullable<unknown>(`/api/s2p/control-tower/queue?${params.toString()}`);
}

export async function fetchVariants(): Promise<unknown | null> {
  return apiGetNullable<unknown>("/api/s2p/pvg/variants");
}

export async function fetchImpact(period = "annual"): Promise<unknown | null> {
  const params = new URLSearchParams({ period });
  return apiGetNullable<unknown>(`/api/s2p/pvg/impact?${params.toString()}`);
}

export async function fetchLeakage(): Promise<unknown | null> {
  return apiGetNullable<unknown>("/api/s2p/pvg/leakage");
}

export async function fetchCycleTime(): Promise<unknown | null> {
  return apiGetNullable<unknown>("/api/s2p/pvg/cycle-time");
}

export async function fetchSuppliers(): Promise<unknown | null> {
  return fetchSupplierProfiles().catch(() => null);
}

export async function fetchSupplierProfiles(): Promise<SupplierProfilesResponse> {
  return apiGet<SupplierProfilesResponse>("/api/s2p/suppliers");
}

export async function fetchDecliningSuppliers(): Promise<SupplierProfilesResponse> {
  return apiGet<SupplierProfilesResponse>("/api/s2p/suppliers/declining");
}

export async function fetchSupplierProfile(supplierId: string): Promise<SupplierProfile | null> {
  return apiGetNullable<SupplierProfile>(`/api/s2p/suppliers/${encodeURIComponent(supplierId)}/profile`);
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

export async function fetchSupplierHeatmap(supplierId: string): Promise<unknown | null> {
  return apiGetNullable<unknown>(`/api/s2p/suppliers/${encodeURIComponent(supplierId)}/heatmap`);
}

export async function getPaymentStrategy(): Promise<PaymentOptimizationResponse | null> {
  return apiGetNullable<PaymentOptimizationResponse>("/api/s2p/suppliers/payment-strategy");
}

export async function getPaymentBehavior(supplierId: string): Promise<PaymentBehavior | null> {
  const params = new URLSearchParams({ supplier_id: supplierId });
  return apiGetNullable<PaymentBehavior>(`/api/s2p/suppliers/payment-behavior?${params.toString()}`);
}

export async function fetchSupplierClustering(): Promise<unknown | null> {
  return apiGetNullable<unknown>("/api/s2p/suppliers/clustering");
}

export async function getSupplierClusters(): Promise<ClusteringResponse | null> {
  return apiGetNullable<ClusteringResponse>("/api/s2p/suppliers/clusters");
}

export async function getSupplierSimilarity(supplierId: string): Promise<SupplierSimilarityResponse | null> {
  const params = new URLSearchParams({ supplier_id: supplierId });
  return apiGetNullable<SupplierSimilarityResponse>(`/api/s2p/suppliers/similarity?${params.toString()}`);
}
