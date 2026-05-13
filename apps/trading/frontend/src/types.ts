export type NullableNumber = number | null;

export type TradingCategory = "equity_long" | "equity_short" | "crypto_spot" | "options" | "etf";
export type TradingAction = "buy" | "hold" | "sell";

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
  conviction?: NullableNumber;
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
  conviction: number;
  shares: number;
  entryPrice: number;
  portfolioValue: number;
  stopLoss?: number;
  target?: number;
}
