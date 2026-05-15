import type {
  Analytics,
  ConservationState,
  FingerprintResponse,
  LearnResponse,
  MarketSnapshot,
  ScoreResponse,
  SelfAccuracyByCategoryResponse,
  SelfAuditTrailResponse,
  SelfCentroidHistoryResponse,
  SelfDecisionExplorerResponse,
  SimilarTrade,
  TickerData,
  TradeHistoryDecision,
  TradeMetadata,
  TrajectoryResponse,
} from "./types";

export const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8010";

type JsonObject = Record<string, unknown>;

function toCamelKey(key: string): string {
  return key.replace(/_([a-z])/g, (_match, letter: string) => letter.toUpperCase());
}

export function normalizeKeys<T = unknown>(value: unknown): T {
  if (Array.isArray(value)) {
    return value.map((item) => normalizeKeys(item)) as T;
  }
  if (value && typeof value === "object") {
    const output: JsonObject = {};
    for (const [key, nested] of Object.entries(value as JsonObject)) {
      output[toCamelKey(key)] = normalizeKeys(nested);
    }
    return output as T;
  }
  return value as T;
}

async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`GET ${path} failed with ${response.status}`);
  }
  return normalizeKeys<T>(await response.json());
}

async function safeApiGet<T>(path: string): Promise<T | null> {
  try {
    return await apiGet<T>(path);
  } catch {
    return null;
  }
}

async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`POST ${path} failed with ${response.status}`);
  }
  return normalizeKeys<T>(await response.json());
}

export function getAnalytics(): Promise<Analytics> {
  return apiGet<Analytics>("/api/context/analytics");
}

export function getHistory(): Promise<TradeHistoryDecision[]> {
  return apiGet<{ decisions?: TradeHistoryDecision[] } | TradeHistoryDecision[]>("/api/history").then((payload) =>
    Array.isArray(payload) ? payload : payload.decisions || [],
  );
}

export interface EvolutionVariant {
  id?: string;
  variantId?: string;
  name?: string;
  description?: string;
  status?: string;
  eventType?: string;
  sourceRule?: string | null;
  sourceCopilot?: string | null;
  metadata?: Record<string, unknown> | string;
  [key: string]: unknown;
}

export interface EvolutionHistoryEvent {
  eventType?: string;
  ruleName?: string;
  variantId?: string;
  metadata?: Record<string, unknown> | string;
  timestamp?: string;
  [key: string]: unknown;
}

export interface EvolutionHistoryResponse {
  domain?: string;
  events?: EvolutionHistoryEvent[];
  count?: number;
}

export interface EvolutionPromotedResponse {
  domain?: string;
  promoted?: EvolutionVariant[];
}

export async function getEvolutionVariants(): Promise<EvolutionVariant[]> {
  const payload = await safeApiGet<{ variants?: EvolutionVariant[] } | EvolutionVariant[]>("/api/evolution/variants");
  if (!payload) return [];
  return Array.isArray(payload) ? payload : payload.variants ?? [];
}

export async function getEvolutionHistory(): Promise<EvolutionHistoryResponse> {
  return (await safeApiGet<EvolutionHistoryResponse>("/api/evolution/history")) ?? { events: [], count: 0 };
}

export async function getPromotedEvolutionRules(): Promise<EvolutionVariant[]> {
  const payload = await safeApiGet<EvolutionPromotedResponse>("/api/evolution/promoted");
  return payload?.promoted ?? [];
}

export function getTradeMetadata(): Promise<Record<string, TradeMetadata>> {
  return apiGet<Record<string, TradeMetadata>>("/api/context/trade-metadata");
}

export function getMarketSnapshot(): Promise<MarketSnapshot> {
  return apiGet<MarketSnapshot>("/api/context/market-snapshot");
}

export function getTicker(ticker: string): Promise<TickerData> {
  return apiGet<TickerData>(`/api/context/ticker/${encodeURIComponent(ticker.toUpperCase())}`);
}

export function getTrajectory(): Promise<TrajectoryResponse> {
  return apiGet<TrajectoryResponse>("/api/trajectory");
}

export function getConservationStatus(): Promise<ConservationState> {
  return apiGet<ConservationState>("/api/conservation/status");
}

export function fetchCentroidHistory(limit = 50): Promise<SelfCentroidHistoryResponse | null> {
  const params = new URLSearchParams({ limit: String(limit) });
  return safeApiGet<SelfCentroidHistoryResponse>(`/api/self/centroid-history?${params.toString()}`);
}

export function fetchAccuracyByCategory(threshold = 0.7): Promise<SelfAccuracyByCategoryResponse | null> {
  const params = new URLSearchParams({ threshold: String(threshold) });
  return safeApiGet<SelfAccuracyByCategoryResponse>(`/api/self/accuracy-by-category?${params.toString()}`);
}

export function fetchDecisions(filters: {
  category?: string;
  action?: string;
  verifiedOnly?: boolean;
  limit?: number;
} = {}): Promise<SelfDecisionExplorerResponse | null> {
  const params = new URLSearchParams();
  if (filters.category) params.set("category", filters.category);
  if (filters.action) params.set("action", filters.action);
  if (typeof filters.verifiedOnly === "boolean") params.set("verified_only", filters.verifiedOnly ? "true" : "false");
  if (typeof filters.limit === "number") params.set("limit", String(filters.limit));
  const query = params.toString();
  return safeApiGet<SelfDecisionExplorerResponse>(`/api/self/decisions${query ? `?${query}` : ""}`);
}

export function fetchAuditTrail(decisionId?: string): Promise<SelfAuditTrailResponse | null> {
  const params = new URLSearchParams();
  if (decisionId) params.set("decision_id", decisionId);
  const query = params.toString();
  return safeApiGet<SelfAuditTrailResponse>(`/api/self/audit-trail${query ? `?${query}` : ""}`);
}

export function getFingerprint(): Promise<FingerprintResponse> {
  return apiGet<FingerprintResponse>("/api/fingerprint");
}

export function scoreTrade(payload: unknown): Promise<ScoreResponse> {
  return apiPost<ScoreResponse>("/api/score", payload).then((result) => ({
    ...result,
    actionNames: result.actionNames || ["buy", "hold", "sell"],
  }));
}

export function learnTrade(
  decisionId: string,
  action: string,
  outcome = "confirmed",
): Promise<LearnResponse> {
  return apiPost<LearnResponse>("/api/learn", {
    decision_id: decisionId,
    actual_action: action,
    outcome,
  });
}

export function saveTradeMetadata(
  payload: TradeMetadata & Record<string, unknown>,
): Promise<{ decisionId: string; metadata: TradeMetadata }> {
  return apiPost<{ decisionId: string; metadata: TradeMetadata }>("/api/context/trade-metadata", {
    ...payload,
    decision_id: payload.decisionId,
  });
}

export function getSimilarTrades(
  input: {
    category: string;
    conviction: number;
    researchDepth: number;
    technicalSignal: number;
    positionSize: number;
    timeHorizon: number;
    marketRegime: number;
  },
  n = 5,
): Promise<{ similar: SimilarTrade[]; count: number }> {
  const params = new URLSearchParams({
    category: input.category,
    conviction: String(input.conviction),
    research_depth: String(input.researchDepth),
    technical_signal: String(input.technicalSignal),
    position_size: String(input.positionSize),
    time_horizon: String(input.timeHorizon),
    market_regime: String(input.marketRegime),
    n: String(n),
  });
  return apiGet<{ similar: SimilarTrade[]; count: number }>(`/api/context/similar?${params.toString()}`);
}
