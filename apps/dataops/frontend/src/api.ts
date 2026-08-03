import type {
  AEImpact,
  AERecommendationResponse,
  AlertGroupsResponse,
  AlertDetail,
  AuditTrailResponse,
  AccuracyByCategoryResponse,
  BlastRadius,
  CentroidHistoryResponse,
  ConservationHistory,
  ConservationState,
  ConservationWhatIfRequest,
  DataOpsAlert,
  DecisionExplorerResponse,
  DIProfilesResponse,
  FactorAutoFillResponse,
  FingerprintResponse,
  Health,
  Incident,
  LearnResponse,
  PatternOrigin,
  PipelineSystem,
  ProcessSignalsResponse,
  RecurrenceResponse,
  ScoreResponse,
  SimilarAlertsResponse,
  SystemHistoryResponse,
  TrajectoryResponse,
  EvolutionVariant,
  CelonisProcessDataResponse,
  EnterpriseHealth,
  RuleLifecycleResponse,
  BottleneckResponse,
  OperationalRulesResponse,
  ProcessData,
  ApplyFixRequest,
  ApplyFixResponse,
  SapPurchaseOrdersResponse,
  SchemaImpactResponse,
  SelfAccuracyByCategoryResponse,
  SelfAuditTrailResponse,
  SelfCentroidHistoryResponse,
  SelfDecisionExplorerResponse,
  TransformationsResponse,
  TransferStatusResponse,
  TrustResponse,
} from "./types";

export const BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8030";

const ACTION_NAMES = [
  "Auto-approve",
  "Investigate",
  "Escalate",
  "Pause downstream",
  "Refer",
];

const ACTION_LABELS: Record<string, string> = {
  auto_approve: "Auto-approve",
  investigate: "Investigate",
  escalate_to_owner: "Escalate",
  pause_downstream: "Pause downstream",
  refer_to_specialist: "Refer",
};

type JsonObject = Record<string, unknown>;

type RawPatternTransfer = JsonObject & {
  transferId?: unknown;
  transfer_id?: unknown;
  sourceSystem?: unknown;
  source_system?: unknown;
  sourcePattern?: unknown;
  source_pattern?: unknown;
  targetSystem?: unknown;
  target_system?: unknown;
  targetAction?: unknown;
  target_action?: unknown;
  transferDate?: unknown;
  transfer_date?: unknown;
  decisionsSinceTransfer?: unknown;
  decisions_since_transfer?: unknown;
  accuracyAtTarget?: unknown;
  accuracy_at_target?: unknown;
  savingsEstimate?: unknown;
  savings_estimate?: unknown;
  status?: unknown;
  confidence?: unknown;
  description?: unknown;
};

type RawTransferSummary = JsonObject & {
  totalTransfers?: unknown;
  total_transfers?: unknown;
  active?: unknown;
  monitoring?: unknown;
  pending?: unknown;
  cumulativeSavings?: unknown;
  cumulative_savings?: unknown;
};

type RawTransferStatusResponse = JsonObject & {
  transfers?: RawPatternTransfer[];
  summary?: RawTransferSummary;
};

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function toCamel(key: string): string {
  return key.replace(/_([a-z])/g, (_match, letter: string) => letter.toUpperCase());
}

export function normalize<T = unknown>(value: unknown): T {
  if (Array.isArray(value)) {
    return value.map((item) => normalize(item)) as T;
  }
  if (!isObject(value)) {
    return value as T;
  }

  const result: JsonObject = {};
  for (const [key, item] of Object.entries(value)) {
    result[toCamel(key)] = normalize(item);
  }
  return result as T;
}

async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${BASE}${path}`);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return normalize<T>(await response.json());
}

async function safeApiGet<T>(path: string): Promise<T | null> {
  try {
    return await apiGet<T>(path);
  } catch {
    return null;
  }
}

async function safeRawApiGet<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(`${BASE}${path}`);
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(toSnakePayload(body)),
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return normalize<T>(await response.json());
}

function toSnakeKey(key: string): string {
  return key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`);
}

function toSnakePayload(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(toSnakePayload);
  }
  if (!isObject(value)) {
    return value;
  }

  const result: JsonObject = {};
  for (const [key, item] of Object.entries(value)) {
    result[toSnakeKey(key)] = toSnakePayload(item);
  }
  return result;
}

export async function getHealth(): Promise<Health> {
  return apiGet<Health>("/health");
}

export async function fetchDIProfiles(): Promise<DIProfilesResponse | null> {
  return safeApiGet<DIProfilesResponse>("/api/di/profiles");
}

export async function getPipelines(): Promise<PipelineSystem[]> {
  const payload = await apiGet<{ pipelines?: PipelineSystem[] }>("/api/context/pipelines");
  return payload.pipelines || [];
}

export async function getAlerts(): Promise<DataOpsAlert[]> {
  const payload = await apiGet<{ alerts?: DataOpsAlert[] }>("/api/context/alerts");
  return payload.alerts || [];
}

export async function getAlertGroups(): Promise<AlertGroupsResponse> {
  return apiGet<AlertGroupsResponse>("/api/context/alert-groups");
}

export async function getAeImpact(): Promise<AEImpact> {
  return apiGet<AEImpact>("/api/ae/impact");
}

export async function getConservationHistory(): Promise<ConservationHistory> {
  return apiGet<ConservationHistory>("/api/ae/conservation-history");
}

export async function getTransferStatus(): Promise<TransferStatusResponse | null> {
  const payload = await safeRawApiGet<RawTransferStatusResponse>("/api/ae/transfer-status");
  if (!payload) {
    return null;
  }
  const summary = payload.summary || {};
  return {
    ...payload,
    transfers: (payload.transfers || []).map((transfer) => ({
      ...transfer,
      transferId: textOr(transfer.transferId ?? transfer.transfer_id),
      sourceSystem: textOr(transfer.sourceSystem ?? transfer.source_system),
      sourcePattern: textOr(transfer.sourcePattern ?? transfer.source_pattern),
      targetSystem: textOr(transfer.targetSystem ?? transfer.target_system),
      targetAction: textOr(transfer.targetAction ?? transfer.target_action),
      transferDate: optionalText(transfer.transferDate ?? transfer.transfer_date),
      decisionsSinceTransfer: numberOr(transfer.decisionsSinceTransfer ?? transfer.decisions_since_transfer, 0),
      accuracyAtTarget: optionalNumber(transfer.accuracyAtTarget ?? transfer.accuracy_at_target),
      savingsEstimate: optionalNumber(transfer.savingsEstimate ?? transfer.savings_estimate),
      status: textOr(transfer.status, "pending"),
      confidence: numberOr(transfer.confidence, 0),
      description: textOr(transfer.description),
    })),
    summary: {
      ...summary,
      totalTransfers: numberOr(summary.totalTransfers ?? summary.total_transfers, 0),
      active: numberOr(summary.active, 0),
      monitoring: numberOr(summary.monitoring, 0),
      pending: numberOr(summary.pending, 0),
      cumulativeSavings: numberOr(summary.cumulativeSavings ?? summary.cumulative_savings, 0),
    },
  };
}

export async function getTrust(): Promise<TrustResponse> {
  return apiGet<TrustResponse>("/api/dataops/trust");
}

export interface CrossSystemAlert {
  alertId?: string;
  alert_id?: string;
  entityId?: string;
  entity_id?: string;
  domains?: string[];
  sourceSignal?: string;
  source_signal?: string;
  relatedSignal?: string;
  related_signal?: string;
  correlation?: number;
  advisory?: boolean;
  timeline?: Array<Record<string, unknown>>;
  title?: string;
  description?: string;
}

export interface CrossSystemResponse {
  alerts?: CrossSystemAlert[];
  provenance?: string;
}

export async function getCrossSystemInsights(): Promise<CrossSystemResponse | null> {
  return safeApiGet<CrossSystemResponse>("/api/discovery/cross-system");
}

export interface CohortExperiment {
  name?: string;
  injectedLift?: number | null;
  recoveredLift?: number | null;
  pass?: boolean;
}

export interface CohortStatusResponse {
  state?: "INSTRUMENT_VALIDATED" | "ACCUMULATING" | "MEASURED" | string;
  instrument?: {
    validated?: boolean;
    provenance?: string;
    sourceArtifact?: string;
    experiments?: CohortExperiment[];
  };
  real?: {
    treatmentN?: number;
    controlN?: number;
    thresholdK?: number;
    magnitude?: number | null;
    provenance?: string;
    status?: string;
  };
  structure?: {
    present?: boolean;
    treatmentN?: number;
    controlN?: number;
    provenance?: string;
  };
}

export function getCohortStatus(): Promise<CohortStatusResponse> {
  return apiGet<CohortStatusResponse>("/api/dataops/cohort-status");
}

export async function getConservationStatus(): Promise<ConservationState> {
  const payload = await apiGet<ConservationState>("/api/conservation/status");
  return {
    ...payload,
    currentThreshold: numberOr(payload.thetaMin, 0.5),
    status: payload.status || "AMBER",
  };
}

export async function postConservationWhatIf(
  body: ConservationWhatIfRequest,
): Promise<ConservationState> {
  const payload = await apiPost<ConservationState>("/api/conservation/what-if", body);
  return {
    ...payload,
    currentThreshold: numberOr(payload.thetaMin, body.thetaMin ?? 0.5),
    status: payload.status || "AMBER",
  };
}

export async function getTrajectory(): Promise<TrajectoryResponse> {
  return apiGet<TrajectoryResponse>("/api/trajectory");
}

export async function getAccuracyByCategory(): Promise<AccuracyByCategoryResponse> {
  return apiGet<AccuracyByCategoryResponse>("/api/context/accuracy-by-category");
}

export async function getCentroidHistory(category?: string): Promise<CentroidHistoryResponse> {
  const params = new URLSearchParams();
  if (category) {
    params.set("category", category);
  }
  const query = params.toString();
  return apiGet<CentroidHistoryResponse>(`/api/context/centroid-history${query ? `?${query}` : ""}`);
}

export async function fetchCentroidHistory(limit = 50): Promise<SelfCentroidHistoryResponse | null> {
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  return safeApiGet<SelfCentroidHistoryResponse>(`/api/self/centroid-history?${params.toString()}`);
}

export async function fetchAccuracyByCategory(threshold = 0.7): Promise<SelfAccuracyByCategoryResponse | null> {
  const params = new URLSearchParams();
  params.set("threshold", String(threshold));
  return safeApiGet<SelfAccuracyByCategoryResponse>(`/api/self/accuracy-by-category?${params.toString()}`);
}

export async function getTransformations(system: string): Promise<TransformationsResponse> {
  return apiGet<TransformationsResponse>(`/api/context/transformations/${encodeURIComponent(system)}`);
}

export async function getBottleneck(system: string): Promise<BottleneckResponse> {
  return apiGet<BottleneckResponse>(`/api/context/bottleneck/${encodeURIComponent(system)}`);
}

export async function getSchemaImpact(system: string, column?: string): Promise<SchemaImpactResponse> {
  const params = new URLSearchParams();
  if (column) {
    params.set("column", column);
  }
  const query = params.toString();
  return apiGet<SchemaImpactResponse>(`/api/context/schema-impact/${encodeURIComponent(system)}${query ? `?${query}` : ""}`);
}

export async function getAlert(id: string): Promise<AlertDetail> {
  return apiGet<AlertDetail>(`/api/context/alert/${encodeURIComponent(id)}`);
}

export async function getAuditTrail(alertId: string): Promise<AuditTrailResponse> {
  return apiGet<AuditTrailResponse>(`/api/context/audit-trail/${encodeURIComponent(alertId)}`);
}

export async function fetchAuditTrail(decisionId?: string): Promise<SelfAuditTrailResponse | null> {
  const params = new URLSearchParams();
  if (decisionId) {
    params.set("decision_id", decisionId);
  }
  const query = params.toString();
  return safeApiGet<SelfAuditTrailResponse>(`/api/self/audit-trail${query ? `?${query}` : ""}`);
}

export async function getAlertDeps(id: string): Promise<BlastRadius> {
  return apiGet<BlastRadius>(`/api/context/alert/${encodeURIComponent(id)}/deps`);
}

export async function getAlertRecurrence(id: string): Promise<RecurrenceResponse> {
  return apiGet<RecurrenceResponse>(`/api/context/alert/${encodeURIComponent(id)}/recurrence`);
}

export async function getAlertFactors(id: string): Promise<FactorAutoFillResponse> {
  return apiGet<FactorAutoFillResponse>(`/api/context/alert/${encodeURIComponent(id)}/factors`);
}

export async function getSimilar(factors: Record<string, number>, category: string): Promise<SimilarAlertsResponse> {
  const params = new URLSearchParams();
  params.set("category", category);
  for (const [key, value] of Object.entries(factors)) {
    params.set(key, String(value));
  }
  return apiGet<SimilarAlertsResponse>(`/api/context/similar?${params.toString()}`);
}

export async function getProcessSignals(system: string): Promise<ProcessSignalsResponse> {
  return apiGet<ProcessSignalsResponse>(`/api/context/process-signals/${encodeURIComponent(system)}`);
}

export async function fetchEnterpriseHealth(): Promise<EnterpriseHealth | null> {
  try {
    return await apiGet<EnterpriseHealth>("/api/dataops/enterprise-health");
  } catch {
    return null;
  }
}

export async function fetchProcessData(): Promise<ProcessData | null> {
  try {
    const payload = await apiGet<CelonisProcessDataResponse | ProcessData>("/api/context/celonis/process-data");
    const response = payload as CelonisProcessDataResponse;
    const processData = response.processData ?? (payload as ProcessData);
    return {
      ...processData,
      source: processData.source ?? response.source,
      knowledgeModels: processData.knowledgeModels ?? response.knowledgeModels,
      kpis: processData.kpis ?? response.kpis,
    };
  } catch {
    return null;
  }
}

export async function fetchSapPurchaseOrders(top = 20): Promise<SapPurchaseOrdersResponse | null> {
  try {
    return await apiGet<SapPurchaseOrdersResponse>(`/api/context/sap/purchase-orders?top=${top}`);
  } catch {
    return null;
  }
}

export async function getSystemHistory(systemName: string, limit = 5): Promise<SystemHistoryResponse> {
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  return apiGet<SystemHistoryResponse>(
    `/api/context/system/${encodeURIComponent(systemName)}/history?${params.toString()}`,
  );
}

export async function getDecisions(filters: {
  system?: string;
  category?: string;
  action?: string;
  correct?: boolean;
  limit?: number;
} = {}): Promise<DecisionExplorerResponse> {
  const params = new URLSearchParams();
  if (filters.system) {
    params.set("system", filters.system);
  }
  if (filters.category) {
    params.set("category", filters.category);
  }
  if (filters.action) {
    params.set("action", filters.action);
  }
  if (typeof filters.correct === "boolean") {
    params.set("correct", filters.correct ? "true" : "false");
  }
  if (typeof filters.limit === "number") {
    params.set("limit", String(filters.limit));
  }
  const query = params.toString();
  return apiGet<DecisionExplorerResponse>(`/api/context/decisions${query ? `?${query}` : ""}`);
}

export async function fetchDecisions(filters: {
  category?: string;
  action?: string;
  verifiedOnly?: boolean;
  limit?: number;
} = {}): Promise<SelfDecisionExplorerResponse | null> {
  const params = new URLSearchParams();
  if (filters.category) {
    params.set("category", filters.category);
  }
  if (filters.action) {
    params.set("action", filters.action);
  }
  if (typeof filters.verifiedOnly === "boolean") {
    params.set("verified_only", filters.verifiedOnly ? "true" : "false");
  }
  if (typeof filters.limit === "number") {
    params.set("limit", String(filters.limit));
  }
  const query = params.toString();
  return safeApiGet<SelfDecisionExplorerResponse>(`/api/self/decisions${query ? `?${query}` : ""}`);
}

export async function getAeRecommendation(alertId: string): Promise<AERecommendationResponse> {
  return apiGet<AERecommendationResponse>(`/api/ae/recommendation/${encodeURIComponent(alertId)}`);
}

export async function getPatternOrigin(): Promise<PatternOrigin> {
  return apiGet<PatternOrigin>("/api/ae/pattern-origin");
}

export async function getIncident(): Promise<Incident> {
  return apiGet<Incident>("/api/ae/incident");
}

export async function getFingerprint(): Promise<FingerprintResponse> {
  return apiGet<FingerprintResponse>("/api/fingerprint");
}

export async function getEvolutionVariants(): Promise<EvolutionVariant[]> {
  const payload = await apiGet<{ variants?: Array<Record<string, unknown>> }>("/api/evolution/variants");
  return (payload.variants || []).map(toEvolutionVariant);
}

export interface EvolutionHistoryItem {
  timestamp?: string;
  category?: string;
  eventType?: string;
  event_type?: string;
  type?: string;
  ruleName?: string;
  rule_name?: string;
  variantId?: string;
  variant_id?: string;
  outcome?: string;
  status?: string;
  domain?: string;
  metadata?: Record<string, unknown> | string;
  [key: string]: unknown;
}

export interface EvolutionHistoryResponse {
  domain?: string;
  events?: EvolutionHistoryItem[];
  count?: number;
}

export interface PromotedEvolutionVariant {
  id?: string;
  name?: string;
  description?: string;
  variantId?: string;
  variant_id?: string;
  ruleName?: string;
  rule_name?: string;
  category?: string;
  status?: "promoted" | "rejected" | string;
  accuracy?: number;
  promotedAt?: string;
  promoted_at?: string;
  timestamp?: string;
  eventType?: string;
  event_type?: string;
  [key: string]: unknown;
}

export interface PromotedEvolutionResponse {
  domain?: string;
  promoted?: Array<PromotedEvolutionVariant | string>;
}

export async function getEvolutionHistory(): Promise<EvolutionHistoryResponse> {
  return (await safeApiGet<EvolutionHistoryResponse>("/api/evolution/history")) ?? { events: [], count: 0 };
}

export async function getPromotedEvolutionRules(): Promise<PromotedEvolutionVariant[]> {
  const payload = await safeApiGet<PromotedEvolutionResponse | Array<PromotedEvolutionVariant | string>>("/api/evolution/promoted");
  const promoted = Array.isArray(payload) ? payload : payload?.promoted;
  return Array.isArray(promoted) ? promoted.map(toPromotedEvolutionVariant) : [];
}

export async function getRuleLifecycle(filters: {
  variantId?: string;
  status?: string;
} = {}): Promise<RuleLifecycleResponse> {
  const params = new URLSearchParams();
  if (filters.variantId) {
    params.set("variant_id", filters.variantId);
  }
  if (filters.status) {
    params.set("status", filters.status);
  }
  const query = params.toString();
  return apiGet<RuleLifecycleResponse>(`/api/ae/rule-lifecycle${query ? `?${query}` : ""}`);
}

export async function getOperationalRules(): Promise<OperationalRulesResponse> {
  return apiGet<OperationalRulesResponse>("/api/ae/operational-rules");
}

export async function scoreAlert(body: unknown): Promise<ScoreResponse> {
  const payload = await apiPost<Omit<ScoreResponse, "actionNames">>("/api/score", body);
  return { ...payload, action: ACTION_LABELS[payload.action] || payload.action, actionNames: ACTION_NAMES };
}

export async function learnAlert(body: unknown): Promise<LearnResponse> {
  return apiPost<LearnResponse>("/api/learn", body);
}

export async function saveAlertMetadata(body: unknown) {
  return apiPost("/api/context/alert-metadata", body);
}

export async function applyFix(body: ApplyFixRequest): Promise<ApplyFixResponse> {
  return apiPost<ApplyFixResponse>("/api/context/apply-fix", body);
}

export function numberOr(value: unknown, fallback: number): number {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function optionalNumber(value: unknown): number | null {
  return value === null || value === undefined ? null : numberOr(value, 0);
}

function textOr(value: unknown, fallback = ""): string {
  return value === null || value === undefined ? fallback : String(value);
}

function optionalText(value: unknown): string | undefined {
  return value === null || value === undefined ? undefined : String(value);
}

function toEvolutionVariant(raw: Record<string, unknown>): EvolutionVariant {
  const metadata = isObject(raw.metadata) ? raw.metadata : {};
  const wins = Number(metadata.wins);
  const total = Number(metadata.total);
  const shadowWinRate = Number.isFinite(wins) && Number.isFinite(total) && total > 0 ? wins / total : undefined;
  return {
    id: String(raw.id || raw.variantId || "variant"),
    name: String(raw.variantId || raw.id || "Evolution variant"),
    status: toEvolutionStatus(raw.eventType, raw.status),
    description: String(raw.description || ""),
    shadowCount: Number.isFinite(total) ? total : undefined,
    shadowWinRate,
    conservationAtPromotion: Number.isFinite(Number(raw.magnitude)) ? Number(raw.magnitude) : undefined,
    rejectReason: typeof metadata.rejectReason === "string" ? metadata.rejectReason : undefined,
    sourceCopilot: typeof raw.sourceCopilot === "string" ? raw.sourceCopilot : undefined,
    sourceRule: typeof raw.sourceRule === "string" ? raw.sourceRule : undefined,
  };
}

function toEvolutionStatus(eventType: unknown, status: unknown): EvolutionVariant["status"] {
  if (eventType === "promotion_approved" || status === "promoted") {
    return "promoted";
  }
  if (eventType === "promotion_rejected" || status === "rejected") {
    return "rejected";
  }
  if (status === "shadow") {
    return "shadow";
  }
  return "created";
}

function toPromotedEvolutionVariant(value: PromotedEvolutionVariant | string): PromotedEvolutionVariant {
  if (typeof value === "string") {
    return {
      variantId: value,
      ruleName: value,
      status: "promoted",
      description: "Promoted DataOps rule.",
    };
  }
  return {
    ...value,
    status: value.status || "promoted",
  };
}
