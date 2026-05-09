import type {
  AEImpact,
  AERecommendationResponse,
  AlertDetail,
  BlastRadius,
  ConservationHistory,
  ConservationState,
  ConservationWhatIfRequest,
  DataOpsAlert,
  FactorAutoFillResponse,
  FingerprintResponse,
  Health,
  Incident,
  LearnResponse,
  PatternOrigin,
  PipelineSystem,
  RecurrenceResponse,
  ScoreResponse,
  TrajectoryResponse,
  EvolutionVariant,
} from "./types";

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8030";

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

export async function getPipelines(): Promise<PipelineSystem[]> {
  const payload = await apiGet<{ pipelines?: PipelineSystem[] }>("/api/context/pipelines");
  return payload.pipelines || [];
}

export async function getAlerts(): Promise<DataOpsAlert[]> {
  const payload = await apiGet<{ alerts?: DataOpsAlert[] }>("/api/context/alerts");
  return payload.alerts || [];
}

export async function getAeImpact(): Promise<AEImpact> {
  return apiGet<AEImpact>("/api/ae/impact");
}

export async function getConservationHistory(): Promise<ConservationHistory> {
  return apiGet<ConservationHistory>("/api/ae/conservation-history");
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

export async function getAlert(id: string): Promise<AlertDetail> {
  return apiGet<AlertDetail>(`/api/context/alert/${encodeURIComponent(id)}`);
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

export function numberOr(value: unknown, fallback: number): number {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
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
