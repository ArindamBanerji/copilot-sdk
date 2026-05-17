import type {
  ConservationStatus,
  AuditTrailResponse,
  ComplianceResponse,
  CrossGraphResponse,
  ExceptionQueueResponse,
  FingerprintResponse,
  LearnDecisionRequest,
  LearnDecisionResponse,
  PerformanceSummaryResponse,
  PerformanceTrajectoryResponse,
  ProcessSignalsResponse,
  PreviewQueueResponse,
  PreviewSuppliersResponse,
  RuleLifecycleResponse,
  S2PEvolutionRulesResponse,
  S2PEvolutionVariantsResponse,
  S2PPromotedResponse,
  S2PShadowResultsResponse,
  ScoreInvoiceRequest,
  ScoreInvoiceResponse,
  SimilarResponse,
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

export async function fetchS2PCrossGraph(): Promise<CrossGraphResponse | null> {
  return apiGet<CrossGraphResponse>("/api/s2p/insight/cross-graph").catch(() => null);
}

export async function fetchS2PProcessSignals(supplierId?: string): Promise<ProcessSignalsResponse | null> {
  const params = new URLSearchParams();
  if (supplierId) params.set("supplier_id", supplierId);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return apiGet<ProcessSignalsResponse>(`/api/s2p/insight/process-signals${suffix}`).catch(() => null);
}

export async function fetchS2PAuditTrail(invoiceId: string): Promise<AuditTrailResponse | null> {
  return apiGet<AuditTrailResponse>(
    `/api/s2p/evidence/audit-trail/${encodeURIComponent(invoiceId)}`
  ).catch(() => null);
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

export async function fetchS2PShadowResults(): Promise<S2PShadowResultsResponse | null> {
  return apiGet<S2PShadowResultsResponse>("/api/s2p/evolution/shadow-results").catch(() => null);
}

export async function fetchS2PPromotedRules(): Promise<S2PPromotedResponse | null> {
  return apiGet<S2PPromotedResponse>("/api/s2p/evolution/promoted").catch(() => null);
}

export async function fetchS2PCompliance(): Promise<ComplianceResponse | null> {
  return apiGet<ComplianceResponse>("/api/s2p/evidence/compliance").catch(() => null);
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
  return apiGetNullable<unknown>("/api/s2p/suppliers");
}

export async function fetchSupplierProfile(supplierId: string): Promise<unknown | null> {
  return apiGetNullable<unknown>(`/api/s2p/suppliers/${encodeURIComponent(supplierId)}/profile`);
}

export async function fetchSupplierHeatmap(supplierId: string): Promise<unknown | null> {
  return apiGetNullable<unknown>(`/api/s2p/suppliers/${encodeURIComponent(supplierId)}/heatmap`);
}

export async function fetchSupplierClustering(): Promise<unknown | null> {
  return apiGetNullable<unknown>("/api/s2p/suppliers/clustering");
}
