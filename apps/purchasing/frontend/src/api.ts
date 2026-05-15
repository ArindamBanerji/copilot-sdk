import type {
  Analytics,
  ConservationState,
  FingerprintResponse,
  HistoryDecision,
  Item,
  ItemProfile,
  LearnResponse,
  OrderFormState,
  OrderMetadataPayload,
  OrderMetadata,
  FactorMap,
  ScoreResponse,
  SelfAccuracyByCategoryResponse,
  SelfAuditTrailResponse,
  SelfCentroidHistoryResponse,
  SelfDecisionExplorerResponse,
  SimilarOrder,
  TodaySummary,
  TrajectoryResponse,
  Variant,
  WasteHistory,
  Weather,
} from "./types";

export const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8020";

type JsonValue =
  | null
  | boolean
  | number
  | string
  | JsonValue[]
  | { [key: string]: JsonValue };

function toCamel(key: string): string {
  return key.replace(/_([a-z])/g, (_, char: string) => char.toUpperCase());
}

function toSnake(key: string): string {
  return key.replace(/[A-Z]/g, (char) => `_${char.toLowerCase()}`);
}

function normalize<T>(value: unknown): T {
  if (Array.isArray(value)) {
    return value.map((item) => normalize(item)) as T;
  }

  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [toCamel(key), normalize(item)]),
    ) as T;
  }

  return value as T;
}

function denormalize(value: unknown): JsonValue {
  if (Array.isArray(value)) {
    return value.map((item) => denormalize(item));
  }

  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, item]) => [
        toSnake(key),
        denormalize(item),
      ]),
    ) as JsonValue;
  }

  return value as JsonValue;
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

async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(denormalize(body)),
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return normalize<T>(await response.json());
}

function withParams(path: string, params: Record<string, unknown>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(toSnake(key), String(value));
    }
  });
  const query = search.toString();
  return query ? `${path}?${query}` : path;
}

export function getAnalytics(): Promise<Analytics> {
  return apiGet<Analytics>("/api/context/analytics");
}

export function getItems(): Promise<Item[]> {
  return apiGet<Item[]>("/api/context/items");
}

export function getTodaySummary(): Promise<TodaySummary> {
  return apiGet<TodaySummary>("/api/context/today-summary");
}

export function getWeather(): Promise<Weather> {
  return apiGet<Weather>("/api/context/weather");
}

export function getWasteHistory(item: string): Promise<WasteHistory> {
  return apiGet<WasteHistory>(`/api/context/waste-history/${encodeURIComponent(item)}`);
}

export function getItemProfile(item: string): Promise<ItemProfile> {
  return apiGet<ItemProfile>(`/api/context/item/${encodeURIComponent(item)}/profile`);
}

export async function getOrderMetadata(): Promise<Record<string, OrderMetadata>> {
  const payload = await apiGet<Record<string, OrderMetadata>>("/api/context/order-metadata");
  return payload ?? {};
}

export function saveOrderMetadata(
  metadata: OrderMetadata | OrderMetadataPayload,
): Promise<{ decisionId?: string; metadata?: OrderMetadata }> {
  return apiPost<{ decisionId?: string; metadata?: OrderMetadata }>("/api/context/order-metadata", metadata);
}

export async function getEvolutionVariants(): Promise<Variant[]> {
  const payload = await safeApiGet<{ variants?: Variant[] } | Variant[]>("/api/evolution/variants");
  if (!payload) return [];
  return Array.isArray(payload) ? payload : payload.variants ?? [];
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

export async function getEvolutionHistory(): Promise<EvolutionHistoryResponse> {
  return (await safeApiGet<EvolutionHistoryResponse>("/api/evolution/history")) ?? { events: [], count: 0 };
}

export async function getPromotedEvolutionRules(): Promise<Variant[]> {
  const payload = await safeApiGet<{ promoted?: Variant[] }>("/api/evolution/promoted");
  return payload?.promoted ?? [];
}

export async function getHistory(): Promise<HistoryDecision[]> {
  const payload = await apiGet<{ decisions?: HistoryDecision[] } | HistoryDecision[]>("/api/history");
  return Array.isArray(payload) ? payload : payload.decisions ?? [];
}

export function getFingerprint(): Promise<FingerprintResponse> {
  return apiGet<FingerprintResponse>("/api/fingerprint");
}

export function getTrajectory(): Promise<TrajectoryResponse> {
  return apiGet<TrajectoryResponse>("/api/trajectory");
}

export function getConservationStatus(): Promise<ConservationState> {
  return apiGet<ConservationState>("/api/conservation/status");
}

export function fetchCentroidHistory(limit = 50): Promise<SelfCentroidHistoryResponse | null> {
  return safeApiGet<SelfCentroidHistoryResponse>(withParams("/api/self/centroid-history", { limit }));
}

export function fetchAccuracyByCategory(threshold = 0.7): Promise<SelfAccuracyByCategoryResponse | null> {
  return safeApiGet<SelfAccuracyByCategoryResponse>(withParams("/api/self/accuracy-by-category", { threshold }));
}

export function fetchDecisions(filters: {
  category?: string;
  action?: string;
  verifiedOnly?: boolean;
  limit?: number;
} = {}): Promise<SelfDecisionExplorerResponse | null> {
  return safeApiGet<SelfDecisionExplorerResponse>(withParams("/api/self/decisions", filters));
}

export function fetchAuditTrail(decisionId?: string): Promise<SelfAuditTrailResponse | null> {
  return safeApiGet<SelfAuditTrailResponse>(withParams("/api/self/audit-trail", { decisionId }));
}

export function getSimilarOrders(
  categoryOrForm: string | OrderFormState,
  factors?: FactorMap,
  n = 5,
): Promise<{ similar?: SimilarOrder[]; count?: number }> {
  const form = typeof categoryOrForm === "string" ? undefined : categoryOrForm;
  const category = typeof categoryOrForm === "string" ? categoryOrForm : categoryOrForm.category;
  const factorMap = factors ?? form?.factors;
  return apiGet<{ similar?: SimilarOrder[]; count?: number }>(
    withParams("/api/context/similar", {
      category,
      expectedDemand: factorMap?.expected_demand ?? form?.expectedDemand,
      dayOfWeek: factorMap?.day_of_week ?? form?.dayOfWeek,
      weatherForecast: factorMap?.weather_forecast ?? form?.weatherForecast,
      eventFlag: factorMap?.event_flag ?? form?.eventFlag,
      historicalWaste: factorMap?.historical_waste ?? form?.historicalWaste,
      supplierLeadTime: factorMap?.supplier_lead_time ?? form?.supplierLeadTime,
      n,
    }),
  );
}

export function scoreOrder(body: { category: string; factors: FactorMap; context?: Record<string, unknown> }): Promise<ScoreResponse> {
  return apiPost<ScoreResponse>("/api/score", body);
}

export function learnOrder(payload: {
  decisionId: string;
  actualAction: string;
  outcome?: string;
  context?: Record<string, unknown>;
}): Promise<LearnResponse> {
  return apiPost<LearnResponse>("/api/learn", payload);
}
