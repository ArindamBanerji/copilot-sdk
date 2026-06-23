import type {
  Analytics,
  AutoOrderAuditEvent,
  AutoOrderEvaluateResponse,
  AutoOrderStatus,
  ConservationState,
  FingerprintResponse,
  HistoryDecision,
  IKSSummary,
  Item,
  ItemProfile,
  LearnResponse,
  MatchQueueResponse,
  MatchResult,
  OrderQueueResponse,
  ParRecommendation,
  ParStatus,
  SupplierScorecard,
  TrustExpectedWeightsResponse,
  TrustInsight,
  TrustWeightsResponse,
  OrderFormState,
  OrderMetadataPayload,
  OrderMetadata,
  FactorMap,
  QBOInvoice,
  QBOLeadTimes,
  QBOPricePoint,
  QBOStatus,
  QBOSupplier,
  ScoreResponse,
  SelfAccuracyByCategoryResponse,
  SelfAuditTrailResponse,
  SelfCentroidHistoryResponse,
  SelfDecisionExplorerResponse,
  CategorySpend,
  CommodityIndicesResponse,
  CommodityPricesResponse,
  CommodityStatus,
  CostPerCoverPoint,
  SimilarOrder,
  SpendAlert,
  SpendSummary,
  SupplierSpend,
  TodaySummary,
  TrajectoryResponse,
  Variant,
  VerifyReasonCode,
  VerifyReasonCodesResponse,
  VerifyResponse,
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

export function getQBOVendors(): Promise<QBOSupplier[]> {
  return apiGet<QBOSupplier[]>("/api/purchasing/qbo/vendors");
}

export function getQBOBills(): Promise<QBOInvoice[]> {
  return apiGet<QBOInvoice[]>("/api/purchasing/qbo/bills");
}

export function getQBOStatus(): Promise<QBOStatus> {
  return apiGet<QBOStatus>("/api/purchasing/qbo/status");
}

export function getQBOPriceHistory(vendorId: string, item: string): Promise<QBOPricePoint[]> {
  return apiGet<QBOPricePoint[]>(
    `/api/purchasing/qbo/price-history/${encodeURIComponent(vendorId)}/${encodeURIComponent(item)}`,
  );
}

export function getQBOLeadTimes(vendorId: string): Promise<QBOLeadTimes> {
  return apiGet<QBOLeadTimes>(`/api/purchasing/qbo/lead-times/${encodeURIComponent(vendorId)}`);
}

export function getSpendSummary(days = 7): Promise<SpendSummary> {
  return apiGet<SpendSummary>(withParams("/api/purchasing/spend/summary", { days }));
}

export function getSpendByCategory(days = 30): Promise<CategorySpend[]> {
  return apiGet<CategorySpend[]>(withParams("/api/purchasing/spend/by-category", { days }));
}

export function getSpendAlerts(threshold = 10): Promise<SpendAlert[]> {
  return apiGet<SpendAlert[]>(withParams("/api/purchasing/spend/alerts", { threshold }));
}

export function getSpendBySupplier(days = 30, limit = 10): Promise<SupplierSpend[]> {
  return apiGet<SupplierSpend[]>(withParams("/api/purchasing/spend/by-supplier", { days, limit }));
}

export function getSpendCostPerCover(days = 30): Promise<CostPerCoverPoint[]> {
  return apiGet<CostPerCoverPoint[]>(withParams("/api/purchasing/spend/cost-per-cover", { days }));
}

export function getCommodityIndices(): Promise<CommodityIndicesResponse> {
  return apiGet<CommodityIndicesResponse>("/api/purchasing/commodity/indices");
}

export function getCommodityPrices(category: string): Promise<CommodityPricesResponse> {
  return apiGet<CommodityPricesResponse>(`/api/purchasing/commodity/prices/${encodeURIComponent(category)}`);
}

export function getCommodityStatus(): Promise<CommodityStatus> {
  return apiGet<CommodityStatus>("/api/purchasing/commodity/status");
}

export function getParRecommendations(
  category?: string,
  serviceLevel = 0.95,
): Promise<ParRecommendation[]> {
  const params = { serviceLevel };
  if (category) {
    return apiGet<ParRecommendation[]>(
      withParams(`/api/purchasing/par/recommendations/${encodeURIComponent(category)}`, params),
    );
  }
  return apiGet<ParRecommendation[]>(
    withParams("/api/purchasing/par/recommendations", params),
  );
}

export function getParStatus(): Promise<ParStatus> {
  return apiGet<ParStatus>("/api/purchasing/par/status");
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
  return apiGet<CohortStatusResponse>("/api/purchasing/cohort-status");
}

export function getIKSSummary(): Promise<IKSSummary> {
  return apiGet<IKSSummary>("/api/purchasing/iks/summary");
}

export function getSupplierScorecards(minOrders = 5): Promise<SupplierScorecard[]> {
  return apiGet<SupplierScorecard[]>(
    withParams("/api/purchasing/suppliers/scorecards", { minOrders }),
  );
}

export function getSupplierScorecard(supplierId: string): Promise<SupplierScorecard> {
  return apiGet<SupplierScorecard>(
    `/api/purchasing/supplier/${encodeURIComponent(supplierId)}/scorecard`,
  );
}

export function getTrustWeights(): Promise<TrustWeightsResponse> {
  return apiGet<TrustWeightsResponse>("/api/purchasing/trust-weights");
}

export function getExpectedTrustWeights(): Promise<TrustExpectedWeightsResponse> {
  return apiGet<TrustExpectedWeightsResponse>("/api/purchasing/trust-weights/expected");
}

export function getTrustInsights(): Promise<TrustInsight[]> {
  return apiGet<TrustInsight[]>("/api/purchasing/trust-weights/insights");
}

export function getAutoOrderStatus(): Promise<AutoOrderStatus> {
  return apiGet<AutoOrderStatus>("/api/purchasing/auto-order/status");
}

export function enableAutoOrder(): Promise<AutoOrderStatus> {
  return apiPost<AutoOrderStatus>("/api/purchasing/auto-order/enable", {});
}

export function disableAutoOrder(): Promise<AutoOrderStatus> {
  return apiPost<AutoOrderStatus>("/api/purchasing/auto-order/disable", {});
}

export function getAutoOrderAudit(): Promise<AutoOrderAuditEvent[]> {
  return apiGet<AutoOrderAuditEvent[]>("/api/purchasing/auto-order/audit");
}

export function evaluateAutoOrder(payload: {
  category: string;
  confidence: number;
  orderId?: string;
  decisionId?: string;
  action?: string;
}): Promise<AutoOrderEvaluateResponse> {
  return apiPost<AutoOrderEvaluateResponse>("/api/purchasing/auto-order/evaluate", payload);
}

export function getMatchQueue(): Promise<MatchQueueResponse> {
  return apiGet<MatchQueueResponse>("/api/purchasing/match/queue");
}

export function getOrderQueue(limit?: number): Promise<OrderQueueResponse> {
  return apiGet<OrderQueueResponse>(withParams("/api/purchasing/queue", { limit }));
}

export function postMatch(
  order: Record<string, unknown>,
  delivery?: Record<string, unknown>,
  invoice?: Record<string, unknown>,
): Promise<MatchResult> {
  return apiPost<MatchResult>("/api/purchasing/match", { order, delivery, invoice });
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

export function getVerifyReasonCodes(): Promise<VerifyReasonCodesResponse> {
  return apiGet<VerifyReasonCodesResponse>("/api/purchasing/verify/reason-codes");
}

export function verifyOrder(payload: {
  decisionId: string;
  actualAction: string;
  reasonCode: VerifyReasonCode;
  notes?: string;
}): Promise<VerifyResponse> {
  return apiPost<VerifyResponse>("/api/purchasing/verify", payload);
}
