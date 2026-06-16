export type NullableNumber = number | null;

export type TradingCategory = "trend_following" | "mean_reversion" | "event_driven" | "income_strategy" | "scalp_intraday";
export type TradingAction = "strong_execution" | "partial_execution" | "poor_execution";

export interface MetricBreakdown {
  count?: number;
  closed?: number;
  wins?: number;
  losses?: number;
  winRate?: NullableNumber;
  pnlDollars?: NullableNumber;
  avgPnlPct?: NullableNumber;
  exposurePct?: NullableNumber;
  exposureDollars?: NullableNumber;
}

export interface PortfolioSummaryData {
  openPositions?: number;
  openExposureDollars?: NullableNumber;
  openExposurePct?: NullableNumber;
  closedTrades?: number;
  winRate?: NullableNumber;
  ytdReturnPct?: NullableNumber;
}

export interface Analytics {
  source?: string;
  seedFile?: string;
  totalTrades?: number;
  closedTrades?: number;
  openPositions?: number;
  categoryCounts?: Record<string, number>;
  thesisCounts?: Record<string, number>;
  contrastCard?: {
    aligned?: { count?: number; tradeIds?: string[] };
    misaligned?: { count?: number; tradeIds?: string[] };
    neutral?: { count?: number; tradeIds?: string[] };
    basis?: string;
  };
  counterfactual?: Record<string, unknown>;
  calendarHeatmap?: Record<string, MetricBreakdown>;
  thesisBreakdown?: Record<string, MetricBreakdown>;
  regimeAnalysis?: Record<string, MetricBreakdown>;
  researchImpact?: {
    bucketBasis?: string;
    buckets?: Record<string, MetricBreakdown>;
  };
  portfolioConcentration?: Record<string, MetricBreakdown>;
  rolling10?: Array<Record<string, unknown>>;
  riskManagement?: Record<string, MetricBreakdown>;
  portfolioSummary?: PortfolioSummaryData;
}

export interface TradeSeedV2 {
  tradeId?: string;
  ticker?: string;
  direction?: TradingAction | string;
  category?: TradingCategory | string;
  thesisType?: string;
  timeframe?: string;
  researchChecklist?: boolean[];
  researchDepth?: NullableNumber;
  signal_alignment?: NullableNumber;
  technicalSignal?: NullableNumber;
  positionSize?: NullableNumber;
  timeHorizon?: NullableNumber;
  marketRegime?: NullableNumber;
  shares?: NullableNumber;
  entryPrice?: NullableNumber;
  portfolioValue?: NullableNumber;
  stopLoss?: NullableNumber;
  target?: NullableNumber;
  rrRatio?: NullableNumber;
  exitPrice?: NullableNumber;
  pnlPct?: NullableNumber;
  pnlDollars?: NullableNumber;
  holdDays?: NullableNumber;
  outcome?: string | null;
  isCorrect?: boolean | null;
  dayOfWeek?: string;
  date?: string;
  actionTaken?: TradingAction | string;
  vixAtEntry?: NullableNumber;
}

export interface TradeMetadata extends TradeSeedV2 {
  decisionId?: string;
  exposurePct?: NullableNumber;
  reward?: NullableNumber;
  createdAt?: string;
  notes?: string;
}

export interface TradeHistoryDecision {
  decisionId?: string;
  category?: string;
  action?: string;
  actionIndex?: number;
  confidence?: number;
  factors?: Record<string, number>;
  createdAt?: string;
  outcome?: string;
  reward?: NullableNumber;
  [key: string]: unknown;
}

export interface JournalAggregate {
  totalTrades?: number;
  winRate?: NullableNumber;
  avgPnl?: NullableNumber;
  totalPnl?: NullableNumber;
  avgConfidence?: NullableNumber;
}

export interface TradeJournalEntry {
  tradeId?: string;
  ticker?: string | null;
  direction?: string | null;
  entryPrice?: NullableNumber;
  exitPrice?: NullableNumber;
  size?: NullableNumber;
  entryTime?: string | null;
  exitTime?: string | null;
  strategyTag?: string | null;
  category?: string | null;
  regime?: string | null;
  pnl?: NullableNumber;
  factors?: Record<string, unknown>;
  optionsFactors?: OptionsFactors;
  optionsAnalyticsOnly?: boolean;
  action?: string | null;
  confidence?: NullableNumber;
  metadata?: Record<string, unknown>;
}

export interface TradesResponse {
  trades?: TradeJournalEntry[];
  count?: number;
  total?: number;
  filtersApplied?: Record<string, string>;
  aggregate?: JournalAggregate;
}

export type TradeDetailResponse = TradeJournalEntry;

export interface AnalyticsGroup extends JournalAggregate {
  key: string;
  count?: number;
}

export interface AnalyticsResponse {
  groupBy?: string;
  groups?: AnalyticsGroup[];
  total?: number;
}

export interface EvidenceResponse {
  tradeId?: string;
  evidenceText?: string;
  factorBreakdown?: string[];
  factors?: Record<string, number>;
  optionsFactors?: OptionsFactors;
  optionsAnalyticsOnly?: boolean;
  action?: string;
  confidence?: NullableNumber;
}

export interface RegimeCurrent {
  regime?: "trending" | "ranging" | "volatile" | string;
  vix?: NullableNumber;
  adx?: NullableNumber;
  spyPrice?: NullableNumber;
  timestamp?: string;
  asOf?: string;
  source?: string;
}

export interface RegimeRecommendation {
  category?: string;
  action?: "increase" | "reduce" | "hold" | string;
  accuracy?: NullableNumber;
  vsBaseline?: NullableNumber;
  delta?: NullableNumber;
  baseline?: NullableNumber;
  currentRegime?: string;
}

export interface RegimeResponse {
  current?: RegimeCurrent;
  accuracyByCategory?: Record<string, Record<string, number>>;
  recommendations?: RegimeRecommendation[];
}

export interface RegimeDetailRecommendation {
  category?: string;
  currentAccuracy?: NullableNumber;
  baselineAccuracy?: NullableNumber;
  deltaPp?: NullableNumber;
  action?: "avoid" | "reduce" | "hold" | "increase" | string;
  shiftPct?: NullableNumber;
  rationale?: string;
  regimeNeutral?: boolean;
  sampleSize?: number;
  minSampleSizeMet?: boolean;
  source?: string;
}

export interface RegimeTransition {
  fromRegime?: string;
  toRegime?: string;
  avgAccuracyDeltaPp?: NullableNumber;
  categoriesAffected?: string[];
  count?: number;
}

export interface RegimeDetailResponse {
  regime?: string;
  recommendations?: RegimeDetailRecommendation[];
  regimeTransitions?: RegimeTransition[];
  conservationSafe?: boolean;
  conservationStatus?: "safe" | "unsafe" | "unknown" | string;
  summary?: string;
  regimeEdgeSummary?: {
    category?: string;
    currentRegime?: string;
    comparisonRegime?: string | null;
    currentAccuracy?: NullableNumber;
    comparisonAccuracy?: NullableNumber;
    edgeDeltaPp?: NullableNumber;
    sampleSizeCurrent?: number;
    sampleSizeComparison?: number;
    source?: string;
    status?: "available" | "insufficient_data" | "unavailable" | string;
    message?: string;
  };
  sizingRecommendation?: {
    action?: "avoid" | "reduce" | "normal" | "increase_small" | string;
    suggestedSizeMultiplier?: NullableNumber;
    maxSizeMultiplier?: NullableNumber;
    reason?: string;
    regime?: string;
    sampleSize?: number;
    minSampleSizeMet?: boolean;
    confidenceStatus?: string;
    advisoryOnly?: boolean;
  };
  transitionAlert?: {
    active?: boolean;
    previousRegime?: string | null;
    currentRegime?: string;
    edgeDeltaPp?: NullableNumber;
    oldRecommendation?: string | null;
    newRecommendation?: string | null;
    message?: string;
    severity?: "info" | "warning" | "critical" | string;
    reason?: string;
  };
  regimeFactorWeights?: {
    status?: "available" | "learning" | "unavailable" | string;
    regime?: string;
    factorWeights?: Array<Record<string, unknown>>;
    source?: string;
    sampleSize?: number;
    reason?: string;
  };
  regimeFactorInfluence?: {
    status?: "available" | "learning" | "unavailable" | string;
    regime?: string;
    factors?: Array<{
      factor?: string;
      influencePp?: NullableNumber;
      winAverage?: NullableNumber;
      lossAverage?: NullableNumber;
      sampleSize?: number;
    }>;
    source?: string;
    sampleSize?: number;
    warning?: string | null;
  };
  dataQuality?: {
    source?: string;
    totalTrades?: number;
    sampledOutcomeTrades?: number;
    minEdgeSample?: number;
    warnings?: string[];
  };
  productHonestyWarnings?: string[];
}

export interface PrescoreRequest {
  ticker: string;
  direction: "long" | "short" | string;
  strategyTag?: string;
  category?: TradingCategory | string;
  sizePct?: number;
}

export interface OptionsFactors {
  ivRvRatio?: NullableNumber;
  greeksExposure?: NullableNumber;
  thetaEfficiency?: NullableNumber;
}

export interface PrescoreResponse {
  recommendation?: "proceed" | "reduce" | "skip" | string;
  confidence?: NullableNumber;
  action?: string;
  factors?: Record<string, number>;
  optionsFactors?: OptionsFactors;
  optionsAnalyticsOnly?: boolean;
  regime?: RegimeCurrent;
  regimeAccuracy?: NullableNumber;
  warnings?: string[];
  evidence?: string;
  category?: string;
  subcategory?: string;
}

export interface PromotionStrategy {
  key?: string;
  strategyKey?: string;
  category?: string;
  strategyTag?: string | null;
  tier?: "paper" | "small_live" | "full_live" | string;
  winRate?: NullableNumber;
  verified?: number;
}

export interface PromotionEvent {
  strategyKey?: string;
  action?: "promote" | "demote" | string;
  fromTier?: string;
  toTier?: string;
  winRate?: NullableNumber;
  verifiedCount?: number;
  reason?: string;
  timestamp?: string;
}

export interface PromotionResponse {
  strategies?: PromotionStrategy[];
  history?: PromotionEvent[];
}

export interface CorrelationPair {
  tickerA?: string;
  tickerB?: string;
  correlation?: NullableNumber;
}

export interface CorrelationAlert {
  level?: "warning" | "critical" | string;
  message?: string;
  value?: NullableNumber;
  tickerA?: string;
  tickerB?: string;
  tickers?: string[];
  correlation?: NullableNumber;
}

export interface CorrelationResponse {
  tickers?: string[];
  matrix?: number[][];
  pairs?: CorrelationPair[];
  avgCorrelation?: NullableNumber;
  maxPair?: CorrelationPair | null;
  alerts?: CorrelationAlert[];
  windowDays?: number;
  source?: string;
  reason?: string;
}

export interface VIXTimingCell {
  count?: number;
  wins?: number;
  accuracy?: NullableNumber;
}

export interface VIXTimingBucket {
  hold?: string;
  holdBucket?: string;
  vix?: string;
  vixBucket?: string;
  accuracy?: NullableNumber;
  count?: number;
}

export interface VIXTimingResponse {
  matrix?: Record<string, Record<string, VIXTimingCell>>;
  bestBucket?: VIXTimingBucket | null;
  worstBucket?: VIXTimingBucket | null;
  recommendations?: string[];
  totalAnalyzed?: number;
  totalSkipped?: number;
  holdLabels?: Record<string, string>;
  vixLabels?: Record<string, string>;
}

export interface TickerData {
  ticker: string;
  name?: string;
  sector?: string;
  price?: NullableNumber;
  value?: NullableNumber;
  change30dPct?: NullableNumber;
  volume?: NullableNumber;
  source?: string;
  marketCapB?: NullableNumber;
  above50ma?: boolean | null;
  rsi?: NullableNumber;
  volRankPctl?: NullableNumber;
}

export interface MarketProvenance {
  source: string;
  as_of?: string | null;
}

export interface JoinedTrade extends TradeMetadata {
  decisionId: string;
  history?: TradeHistoryDecision;
  tickerData?: TickerData;
  confidence?: number;
  scoreAction?: string;
  factors?: Record<string, number>;
}

export interface MarketSnapshot {
  asOf?: string;
  source?: string;
  spy?: TickerData;
  vix?: TickerData;
  sectors?: Array<{ name: string; changePct?: NullableNumber; breadth?: NullableNumber }>;
  sector?: { leader?: string; laggard?: string; breadth?: NullableNumber };
  provenance?: MarketProvenance;
  [key: string]: unknown;
}

export interface ScoreResponse {
  decisionId: string;
  action: string;
  actionIndex: number;
  confidence: number;
  probabilities: number[];
  category: string;
  factors?: Record<string, number>;
  actionNames: string[];
}

export interface LearnResponse {
  decisionId?: string;
  iksBefore?: NullableNumber;
  iksAfter?: NullableNumber;
  centroidDelta?: NullableNumber;
  decisionsTotal?: number;
  reward?: NullableNumber;
  previousReward?: NullableNumber;
  rewardMultiplier?: NullableNumber;
  iksDelta?: NullableNumber;
  [key: string]: unknown;
}

export interface FingerprintResponse {
  factors?: Array<{
    name: string;
    displayName?: string;
    weight?: number;
    sigma?: number;
    interpretation?: string;
    category?: "signal" | "moderate" | "noise";
  }>;
  perCategoryPrecision?: Record<string, number>;
  decisionsAnalyzed?: number;
  [key: string]: unknown;
}

export interface TrustScore {
  variance: number;
  mean: number;
  nSamples: number;
  trustLabel: string;
  sigma: number;
}

export interface HeroInsight {
  overusedFactor: string;
  overusedSigma: number;
  underusedFactor: string;
  underusedSigma: number;
  message: string;
}

export interface TrustAnalysisResponse {
  factors: string[];
  implemented: string[];
  trustScores: Record<string, TrustScore>;
  totalTrades: number;
  heroInsight: HeroInsight | null;
}

export interface DetectedPattern {
  name: string;
  displayName: string;
  description: string;
  frequency: number;
  severity: number;
  affectedTradeCount: number;
  affectedTrades: string[];
  recommendation: string;
}

export interface PatternDetectionResponse {
  patterns: DetectedPattern[];
  totalPatternsDetected?: number;
  totalTradesAnalyzed?: number;
  totalTrades?: number;
  mostSevere?: string | null;
  message?: string;
}

export interface TrajectoryResponse {
  currentIks?: number;
  iks?: number;
  points?: Array<{ decisions: number; iks: number; winRate: number }>;
  currentWinRate?: number;
  decisionsTotal?: number;
  daysActive?: number;
  narrative?: string;
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

export interface CategoryConservation {
  category: string;
  totalTrades: number;
  verified: number;
  correct: number;
  accuracy: number;
  thetaMinProxy: number;
  status: "BOOTSTRAP" | "GREEN" | "AMBER" | "RED" | string;
  canTrade: boolean;
  note: string | null;
}

export interface ConservationBreakdownResponse {
  categories: CategoryConservation[];
  totalCategories: number;
  redCategories: number;
  amberCategories: number;
  greenCategories: number;
  totalVerified: number;
  overallSafe: boolean;
  penaltyRatio: number;
  methodology: string;
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

export interface SimilarTrade {
  tradeId?: string;
  ticker?: string;
  thesisType?: string;
  timeframe?: string;
  researchDepth?: NullableNumber;
  pnlPct?: NullableNumber;
  outcome?: string | null;
  isCorrect?: boolean | null;
  similarity?: number;
}

export interface TradeFormState {
  ticker: string;
  direction: TradingAction;
  category: TradingCategory;
  thesisType: string;
  timeframe: "intraday" | "swing" | "position" | "long";
  researchChecklist: boolean[];
  signal_alignment: number;
  shares: number;
  entryPrice: number;
  portfolioValue: number;
  stopLoss?: number;
  target?: number;
}
