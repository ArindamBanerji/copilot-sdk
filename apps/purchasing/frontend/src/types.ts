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
  | "supplier_lead_time";

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

export interface CentroidCheckpoint {
  decisionId?: string;
  category?: string;
  centroids?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  createdAt?: string;
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
