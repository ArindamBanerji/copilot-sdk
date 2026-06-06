import type {
  Analytics,
  AnalyticsResponse,
  ConservationBreakdownResponse,
  ConservationState,
  CorrelationResponse,
  EvidenceResponse,
  FingerprintResponse,
  LearnResponse,
  MarketSnapshot,
  PatternDetectionResponse,
  PrescoreRequest,
  PrescoreResponse,
  RegimeDetailResponse,
  PromotionResponse,
  RegimeResponse,
  ScoreResponse,
  SelfAccuracyByCategoryResponse,
  SelfAuditTrailResponse,
  SelfCentroidHistoryResponse,
  SelfDecisionExplorerResponse,
  SimilarTrade,
  TickerData,
  TradeDetailResponse,
  TradeHistoryDecision,
  TradeJournalEntry,
  TradeMetadata,
  TradesResponse,
  TrajectoryResponse,
  TrustAnalysisResponse,
  VIXTimingResponse,
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

export interface TradeJournalFilters {
  ticker?: string;
  category?: string;
  strategyTag?: string;
  regime?: string;
  outcome?: "win" | "loss" | "";
  dateFrom?: string;
  dateTo?: string;
  limit?: number;
  offset?: number;
}

function journalQuery(params: TradeJournalFilters = {}): string {
  const query = new URLSearchParams();
  if (params.ticker) query.set("ticker", params.ticker);
  if (params.category) query.set("category", params.category);
  if (params.strategyTag) query.set("strategy_tag", params.strategyTag);
  if (params.regime) query.set("regime", params.regime);
  if (params.outcome) query.set("outcome", params.outcome);
  if (params.dateFrom) query.set("date_from", params.dateFrom);
  if (params.dateTo) query.set("date_to", params.dateTo);
  if (typeof params.limit === "number") query.set("limit", String(params.limit));
  if (typeof params.offset === "number") query.set("offset", String(params.offset));
  return query.toString();
}

export function fetchTrades(params: TradeJournalFilters = {}): Promise<TradesResponse | null> {
  const query = journalQuery(params);
  return safeApiGet<TradesResponse>(`/api/trading/trades${query ? `?${query}` : ""}`);
}

export function fetchTradeDetail(tradeId: string): Promise<TradeDetailResponse | null> {
  return safeApiGet<TradeJournalEntry>(`/api/trading/trades/${encodeURIComponent(tradeId)}`);
}

export function fetchAnalytics(
  groupBy: "category" | "ticker" | "strategy_tag" | "regime" | "month" | "subcategory" = "category",
  params: TradeJournalFilters = {},
): Promise<AnalyticsResponse | null> {
  const query = new URLSearchParams(journalQuery(params));
  query.set("group_by", groupBy);
  return safeApiGet<AnalyticsResponse>(`/api/trading/analytics?${query.toString()}`);
}

export function fetchSubcategoryAnalytics(params: TradeJournalFilters = {}): Promise<AnalyticsResponse | null> {
  return fetchAnalytics("subcategory", params);
}

export function fetchEvidence(tradeId: string): Promise<EvidenceResponse | null> {
  return safeApiGet<EvidenceResponse>(`/api/trading/evidence/${encodeURIComponent(tradeId)}`);
}

export function fetchRegime(): Promise<RegimeResponse | null> {
  return safeApiGet<RegimeResponse>("/api/trading/regime");
}

export function fetchRegimeDetail(): Promise<RegimeDetailResponse | null> {
  return safeApiGet<RegimeDetailResponse>("/api/trading/regime/detail");
}

export function fetchPromotion(): Promise<PromotionResponse | null> {
  return safeApiGet<PromotionResponse>("/api/trading/promotion");
}

export function fetchCorrelation(window = 20): Promise<CorrelationResponse | null> {
  const params = new URLSearchParams({ window: String(window) });
  return safeApiGet<CorrelationResponse>(`/api/trading/correlation?${params.toString()}`);
}

export function fetchVIXTiming(): Promise<VIXTimingResponse | null> {
  return safeApiGet<VIXTimingResponse>("/api/trading/vix-timing");
}

export async function prescoreTrade(payload: PrescoreRequest): Promise<PrescoreResponse | null> {
  try {
    return await apiPost<PrescoreResponse>("/api/trading/prescore", {
      ticker: payload.ticker,
      direction: payload.direction,
      strategy_tag: payload.strategyTag,
      category: payload.category,
      size_pct: payload.sizePct,
    });
  } catch {
    return null;
  }
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

export function getConservationBreakdown(): Promise<ConservationBreakdownResponse | null> {
  return safeApiGet<ConservationBreakdownResponse>("/api/context/conservation-breakdown");
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
} | number = {}): Promise<SelfDecisionExplorerResponse | null> {
  const resolvedFilters = typeof filters === "number" ? { limit: filters } : filters;
  const params = new URLSearchParams();
  if (resolvedFilters.category) params.set("category", resolvedFilters.category);
  if (resolvedFilters.action) params.set("action", resolvedFilters.action);
  if (typeof resolvedFilters.verifiedOnly === "boolean") params.set("verified_only", resolvedFilters.verifiedOnly ? "true" : "false");
  if (typeof resolvedFilters.limit === "number") params.set("limit", String(resolvedFilters.limit));
  const query = params.toString();
  return safeApiGet<SelfDecisionExplorerResponse>(`/api/self/decisions${query ? `?${query}` : ""}`);
}

export function fetchAuditTrail(decisionId?: string, limit = 50): Promise<SelfAuditTrailResponse | null> {
  const params = new URLSearchParams();
  if (decisionId) params.set("decision_id", decisionId);
  if (typeof limit === "number") params.set("limit", String(limit));
  const query = params.toString();
  return safeApiGet<SelfAuditTrailResponse>(`/api/self/audit-trail${query ? `?${query}` : ""}`);
}

export function getFingerprint(): Promise<FingerprintResponse> {
  return apiGet<FingerprintResponse>("/api/fingerprint");
}

export function getTrustAnalysis(): Promise<TrustAnalysisResponse | null> {
  return safeApiGet<TrustAnalysisResponse>("/api/context/trust-analysis");
}

export function getPatterns(): Promise<PatternDetectionResponse | null> {
  return safeApiGet<PatternDetectionResponse>("/api/context/patterns");
}

export function scoreTrade(payload: unknown): Promise<ScoreResponse> {
  return apiPost<ScoreResponse>("/api/score", payload).then((result) => ({
    ...result,
    actionNames: result.actionNames || ["strong_execution", "partial_execution", "poor_execution"],
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
    signal_alignment: number;
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
    signal_alignment: String(input.signal_alignment),
    market_regime: String(input.researchDepth),
    position_sizing: String(input.technicalSignal),
    timing_quality: String(input.positionSize),
    risk_reward_actual: String(input.timeHorizon),
    emotional_indicator: String(input.marketRegime),
    n: String(n),
  });
  return apiGet<{ similar: SimilarTrade[]; count: number }>(`/api/context/similar?${params.toString()}`);
}
