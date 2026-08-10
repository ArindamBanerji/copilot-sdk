export type PurchaseCategory =
  | "protein"
  | "produce"
  | "dairy"
  | "dry_goods"
  | "beverages"
  | string;

export type PurchaseAction =
  | "order_as_planned"
  | "order_more"
  | "order_less"
  | "skip"
  | string;

export type PurchasingFactorName =
  | "expected_demand"
  | "day_of_week"
  | "weather_forecast"
  | "event_flag"
  | "historical_waste"
  | "supplier_lead_time"
  | "price_memory_index";

export type FactorMap = Record<PurchasingFactorName, number>;

export type ExpectedDemandChoice = "high" | "above_avg" | "average" | "below_avg" | "low";

export interface MetricBreakdown {
  count?: number;
  correct?: number;
  accuracy?: number;
  totalCostDollars?: number;
  wasteCostDollars?: number;
  stockoutCostDollars?: number;
  wastePctAvg?: number;
  stockoutRate?: number;
  matchedRules?: number;
  [key: string]: unknown;
}

export interface Analytics {
  contrastCard?: {
    aligned?: MetricBreakdown;
    misaligned?: MetricBreakdown;
    [key: string]: unknown;
  };
  counterfactual?: {
    scenario?: string;
    ordersAdjusted?: number;
    affectedOrderIds?: string[];
    dollarsSaved?: number;
    wasteReductionPct?: number;
    explanation?: string;
    [key: string]: unknown;
  };
  categoryAccuracy?: Record<string, MetricBreakdown>;
  dayOfWeek?: Record<string, MetricBreakdown>;
  eventImpact?: Record<string, MetricBreakdown>;
  wasteCostAnalysis?: MetricBreakdown & {
    totalWasteCostDollars?: number;
    totalStockoutCostDollars?: number;
    totalCostDollars?: number;
    averageWastePct?: number;
    stockoutOrders?: number;
    stockoutRate?: number;
    highestWasteOrder?: Record<string, unknown>;
  };
  aeImpact?: {
    managedByRules?: MetricBreakdown;
    unmanaged?: MetricBreakdown;
    estimatedSavingsFromPromotedRules?: number;
    [key: string]: unknown;
  };
  portfolioSummary?: {
    totalOrders?: number;
    accuracy?: number;
    totalCost?: number;
    totalWasteCost?: number;
    totalStockoutCost?: number;
    wasteReductionSinceStartPct?: number;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export interface Item {
  itemId?: string;
  name: string;
  displayName?: string;
  emoji?: string;
  category?: PurchaseCategory;
  unit?: string;
  parLevel?: number;
  defaultQuantityLbs?: number;
  onHandQty?: number;
  unitPrice?: number;
  supplier?: string;
  eventSensitivity?: number;
  usageRange?: string | number[];
  supplierLeadTime?: number;
  source?: string;
  [key: string]: unknown;
}

export interface Weather {
  condition?: string;
  temperatureF?: number;
  precipitationProb?: number;
  precipChance?: number;
  weatherFactor?: number;
  windMph?: number;
  forecast?: string;
  source?: string;
  [key: string]: unknown;
}

export interface TodaySummary {
  date?: string;
  dayOfWeek?: string;
  weather?: Weather;
  events?: Array<Record<string, unknown>>;
  [key: string]: unknown;
}

export interface WasteHistory {
  item?: string;
  wastePct?: number[];
  count?: number;
  totalWasteDollars?: number;
  [key: string]: unknown;
}

export interface ItemProfile {
  item?: Item | string;
  wasteHistory?: WasteHistory | number[];
  wasteAvg?: number;
  wasteTrend?: string;
  aeRules?: Variant[];
  aeManaged?: boolean;
  [key: string]: unknown;
}

export interface Variant {
  id?: string;
  variantId?: string;
  name?: string;
  description?: string;
  eventType?: string;
  status?: string;
  lift?: number;
  graphContext?: string | Record<string, unknown>;
  metadata?: string | Record<string, unknown>;
  magnitude?: number;
  sourceCopilot?: string | null;
  sourceRule?: string | null;
  match?: {
    categories?: string[];
    day?: string;
    eventRequired?: boolean;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export interface OrderMetadata {
  decisionId?: string;
  item?: string;
  itemName?: string;
  displayName?: string;
  category?: string;
  quantityLbs?: number;
  quantity?: number;
  unit?: string;
  expectedDemand?: number;
  expectedDemandChoice?: ExpectedDemandChoice;
  unitPrice?: number;
  cost?: number;
  totalCost?: number;
  stockoutEstimate?: number;
  wasteEstimate?: number;
  riskRatio?: number | null;
  autoComputedFactors?: Partial<FactorMap>;
  day?: string;
  events?: Array<Record<string, unknown>> | string[];
  reward?: number;
  action?: string;
  confirmedAction?: string;
  createdAt?: string;
  [key: string]: unknown;
}

export interface HistoryDecision {
  decisionId?: string;
  id?: string;
  timestamp?: string;
  action?: string;
  actualAction?: string;
  reward?: number;
  score?: number;
  confidence?: number;
  category?: string;
  item?: string;
  metadata?: OrderMetadata;
  factors?: Record<string, number>;
  [key: string]: unknown;
}

export interface JoinedOrder {
  decisionId: string;
  decision?: HistoryDecision;
  metadata?: OrderMetadata;
  item?: Item;
}

export interface ScoreResponse {
  decisionId?: string;
  action?: PurchaseAction;
  actionIndex?: number;
  score?: number;
  confidence?: number;
  probabilities?: number[];
  category?: string;
  recommendedAction?: string;
  factors?: Partial<FactorMap>;
  explanation?: string;
  [key: string]: unknown;
}

export interface LearnResponse {
  decisionId?: string;
  reward?: number;
  previousReward?: number | null;
  rewardMultiplier?: number;
  iksBefore?: number;
  iksAfter?: number;
  decisionsTotal?: number;
  outcome?: string;
  updated?: boolean;
  [key: string]: unknown;
}

export type VerifyReasonCode =
  | "supplier_preference"
  | "price_override"
  | "seasonal_adjustment"
  | "manager_directive"
  | "quality_concern"
  | "par_adjustment"
  | "other";

export interface VerifyReasonOption {
  code: VerifyReasonCode;
  label: string;
}

export interface VerifyReasonCodesResponse {
  reasonCodes: VerifyReasonOption[];
  count: number;
}

export interface VerifyRequest {
  decisionId: string;
  actualAction: string;
  reasonCode: VerifyReasonCode;
  notes?: string;
}

export interface VerifyResponse {
  decisionId: string;
  recommendedAction: string;
  actualAction: string;
  isOverride: boolean;
  reasonCode: VerifyReasonCode;
  notes?: string | null;
  conservationStatus: string;
  conservationQ: number;
  verifiedCount: number;
  metadata?: Record<string, unknown>;
  reward?: number | null;
  rewardRaw?: number | null;
  rewardMultiplier?: number;
  iksBefore?: number | null;
  iksAfter?: number | null;
  centroidDelta?: number | null;
  decisionsTotal?: number | null;
  outcome?: string | null;
  [key: string]: unknown;
}

export interface FingerprintFactor {
  name: string;
  displayName?: string;
  weight?: number;
  sigma?: number;
  interpretation?: string;
  category?: string;
  [key: string]: unknown;
}

export interface FingerprintResponse {
  factors?: FingerprintFactor[] | Record<string, number>;
  signal?: Record<string, number>;
  noise?: Record<string, number>;
  decisionsAnalyzed?: number;
  [key: string]: unknown;
}

export interface TrajectoryResponse {
  currentIks?: number;
  iks?: number;
  decisionsTotal?: number;
  daysActive?: number;
  points?: Array<Record<string, unknown>>;
  trajectory?: Array<Record<string, unknown>>;
  [key: string]: unknown;
}

export interface ConservationState {
  domain?: string;
  verifiedCount?: number;
  correctCount?: number;
  totalDecisions?: number;
  penaltyRatio?: number;
  signal?: number | null;
  q?: number | null;
  accuracy?: number | null;
  thetaMin?: number | null;
  headroom?: number | null;
  status?: string;
  passed?: boolean;
  currentThreshold?: number;
  autoResolveRate?: number;
  alpha?: number;
  [key: string]: unknown;
}

export interface CheckpointQuality {
  window_size: number | null;
  verified_count: number | null;
  correct_count: number | null;
  rolling_accuracy: number | null;
  window_end?: string | null;
  policy_version: string | null;
}

export interface CentroidCheckpoint {
  decisionId?: string;
  category?: string;
  centroids?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  createdAt?: string;
  quality: CheckpointQuality | null;
  [key: string]: unknown;
}

export interface SelfCentroidHistoryResponse {
  checkpoints?: CentroidCheckpoint[];
  total?: number;
}

export interface CategoryAccuracy {
  category?: string;
  accuracy?: number;
  total?: number;
  correct?: number;
  alert?: boolean;
}

export interface SelfAccuracyByCategoryResponse {
  categories?: CategoryAccuracy[];
  threshold?: number;
  overallVerified?: number;
}

export interface SelfDecisionEntry {
  decisionId?: string;
  decision_id?: string;
  category?: string;
  recommendedAction?: string;
  recommended_action?: string;
  actualAction?: string;
  actual_action?: string;
  action?: string;
  confidence?: number;
  factors?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  outcomeMetadata?: Record<string, unknown>;
  isCorrect?: boolean | null;
  createdAt?: string | number;
  verifiedAt?: string | number;
  [key: string]: unknown;
}

export interface SelfDecisionExplorerResponse {
  decisions?: SelfDecisionEntry[];
  total?: number;
}

export type AuditTrailEntry = SelfDecisionEntry;

export interface SelfAuditTrailResponse {
  trails?: AuditTrailEntry[];
  total?: number;
  decision?: SelfDecisionEntry;
  outcome?: SelfDecisionEntry | null;
  chainComplete?: boolean;
  error?: string;
}

export interface SimilarOrder {
  orderId?: string;
  item?: string;
  category?: string;
  dayOfWeek?: string;
  isEventDay?: boolean;
  quantityLbs?: number;
  wastePct?: number;
  stockoutOccurred?: boolean;
  isCorrect?: boolean;
  similarity?: number;
  [key: string]: unknown;
}

export interface OrderFormState {
  itemName?: string;
  category?: string;
  expectedDemandChoice?: ExpectedDemandChoice;
  expectedDemand?: number;
  dayOfWeek?: number;
  weatherForecast?: number;
  eventFlag?: number;
  historicalWaste?: number;
  supplierLeadTime?: number;
  factors?: FactorMap;
}

export interface OrderMetadataPayload extends OrderMetadata {
  decisionId: string;
  item: string;
  displayName?: string;
  emoji?: string;
  category?: string;
  quantity: number;
  unit?: string;
  day?: string;
  events?: Array<Record<string, unknown>>;
  cost: number;
  stockoutEstimate: number;
  wasteEstimate: number;
  riskRatio: number | null;
  autoComputedFactors: FactorMap;
  expectedDemandChoice: ExpectedDemandChoice;
  action?: string;
  confirmedAction?: string;
}

export interface QBOLineItem {
  itemName?: string;
  category?: string;
  quantity?: number;
  unitPrice?: number;
  amount?: number;
  [key: string]: unknown;
}

export interface QBOSupplier {
  recordType?: string;
  supplierId: string;
  supplierName: string;
  archetype?: string;
  primaryCategory?: string;
  active?: boolean;
  balance?: number;
  currency?: string;
  timestamp?: string;
  [key: string]: unknown;
}

export interface QBOInvoice {
  recordType?: string;
  invoiceId?: string;
  supplierId?: string;
  supplierName?: string;
  archetype?: string;
  invoiceDate?: string;
  amount?: number;
  currency?: string;
  orderId?: string | null;
  lineItems?: QBOLineItem[];
  timestamp?: string;
  [key: string]: unknown;
}

export interface QBOStatus {
  connected?: boolean;
  companyName?: string | null;
  realmId?: string | null;
  sourceName?: string;
  entityType?: string;
  error?: string;
  [key: string]: unknown;
}

export interface QBOPricePoint {
  date?: string;
  unitPrice?: number;
  quantity?: number;
  invoiceId?: string;
  [key: string]: unknown;
}

export interface QBOLeadTimes {
  meanDays?: number | null;
  medianDays?: number | null;
  stdDays?: number | null;
  sampleCount?: number;
  byQuarter?: Record<string, number>;
  [key: string]: unknown;
}

export interface SpendSummary {
  totalSpend: number;
  orderCount: number;
  avgOrderAmount?: number;
  costPerCover?: number | null;
  periodStart?: string | null;
  periodEnd?: string | null;
  [key: string]: unknown;
}

export interface CategorySpend {
  category: string;
  totalAmount: number;
  orderCount: number;
  pctOfTotal: number;
  [key: string]: unknown;
}

export interface SpendAlert {
  itemName: string;
  currentPrice: number;
  avgPrice: number;
  variancePct: number;
  supplierName?: string;
  category?: string;
  [key: string]: unknown;
}

export interface SupplierSpend {
  supplierId: string;
  supplierName: string;
  totalAmount: number;
  orderCount: number;
  categories?: string[];
  [key: string]: unknown;
}

export interface CostPerCoverPoint {
  date: string;
  totalSpend: number;
  covers?: number | null;
  costPerCover?: number | null;
  [key: string]: unknown;
}

export interface ProvenancedValue<T> {
  value: T;
  source: string;
  label?: string | null;
  asOf?: string | null;
}

export interface CommodityPricePoint {
  date: string;
  item: string;
  price: number;
  unit: string;
  [key: string]: unknown;
}

export type CommodityPricesResponse = ProvenancedValue<CommodityPricePoint[] | null>;

export type CommodityIndicesResponse = ProvenancedValue<Record<string, number> | null>;

export interface CommodityStatus {
  provider?: string;
  source?: string;
  provenanceTier?: string;
  fredActive?: boolean;
  categories?: string[];
  ttlSeconds?: number;
  [key: string]: unknown;
}

export interface ParRecommendation {
  itemName: string;
  category: string;
  currentPar: number;
  recommendedPar: number;
  avgDailyUsage: number;
  usageStd: number;
  wasteRate: number;
  serviceLevel: number;
  weeklySavingsEstimate: number;
  confidence: "high" | "moderate" | "low" | string;
  seasonalAdjustment?: number | null;
  dataDays: number;
  provenance: string;
  [key: string]: unknown;
}

export interface ParStatus {
  totalItems: number;
  categories: string[];
  dataSource: string;
  provenanceTier: string;
  [key: string]: unknown;
}

export interface IKSSummary {
  iksScore: number;
  perCategory: Record<string, number>;
  verifiedCount: number;
  available: boolean;
  source: string;
  substantiationTier: string;
  dMax?: number;
  [key: string]: unknown;
}

export interface SupplierScorecard {
  supplierId: string;
  supplierName: string;
  tier: "A" | "B" | "C" | string;
  overallScore: number;
  reliabilityPct: number;
  priceTrendPct: number;
  deliveryPerformance: number;
  exceptionRate: number;
  decisionCount: number;
  trend: "improving" | "stable" | "declining" | string;
  summary: string;
  provenance: string;
  [key: string]: unknown;
}

export interface TrustWeightsResponse {
  weights: Record<string, Record<string, number>> | null;
  phase: "learning" | "active" | string;
  decisionsTotal: number;
  decisionsNeeded: number;
  provenance: string;
  [key: string]: unknown;
}

export interface TrustExpectedWeightsResponse {
  weights: Record<string, Record<string, number>>;
  source: string;
  factorLabels?: Record<string, string>;
  [key: string]: unknown;
}

export interface TrustInsight {
  category: string;
  insight: string;
  trapFactor: string;
  trustedFactor: string;
  gap: number;
  [key: string]: unknown;
}

export interface AutoOrderStatus {
  enabled: boolean;
  threshold: number;
  initialThreshold?: number;
  minThreshold?: number;
  spotCheckRate?: number;
  minVerified?: number;
  autoOrderedCount: number;
  spotCheckCount: number;
  errorCount?: number;
  errorRate: number;
  auditCount?: number;
  conservationStatus?: string;
  verifiedCount?: number;
  reason?: string;
  [key: string]: unknown;
}

export interface AutoOrderAuditEvent {
  eventId?: string;
  orderId?: string | null;
  decisionId?: string | null;
  category?: string;
  action?: string;
  confidence?: number;
  threshold?: number;
  autoOrder?: boolean;
  spotCheck?: boolean;
  reason?: string;
  source?: string;
  createdAt?: string;
  [key: string]: unknown;
}

export interface AutoOrderEvaluateResponse {
  autoOrder: boolean;
  reason: string;
  spotCheck: boolean;
  threshold: number;
  event?: AutoOrderAuditEvent;
  learningApplied?: boolean;
  [key: string]: unknown;
}

export interface MatchResult {
  matched?: boolean;
  status?: string;
  orderId?: string;
  supplierId?: string;
  supplierName?: string;
  item?: string;
  amount?: number;
  matchConfidence?: number;
  confidence?: number;
  discrepancyMessages?: string[];
  reasons?: string[];
  [key: string]: unknown;
}

export interface MatchQueueResponse {
  exceptions?: MatchResult[];
  recentResults?: MatchResult[];
  count?: number;
  pendingCount?: number;
  autoMatchedCount?: number;
  exceptionCount?: number;
  source?: string;
  [key: string]: unknown;
}

export interface OrderQueueTopFactor {
  name: string;
  value: number;
  interpretation: string;
}

export interface OrderQueueItem {
  orderId?: string;
  supplierId?: string;
  supplierName?: string;
  category?: string;
  totalAmount?: number;
  recommendedAction?: string;
  confidence?: number;
  priorityScore?: number;
  topFactors?: OrderQueueTopFactor[];
  stockoutRisk?: number;
  financialImpact?: number;
  agingDays?: number;
  whatToOrder?: string;
  howMuch?: number;
  unit?: string;
  factors?: Record<string, number>;
  [key: string]: unknown;
}

export interface OrderQueueResponse {
  queue: OrderQueueItem[];
  count: number;
  conservationStatus?: ConservationState | Record<string, unknown>;
  source?: string;
  [key: string]: unknown;
}
