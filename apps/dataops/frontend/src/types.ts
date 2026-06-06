import type { ConservationStatusLevel, FactorItem } from "../../../../copilot_sdk/frontend";

export type PipelineStatus = "healthy" | "active" | "warning" | "degraded" | "critical" | string;
export type AlertSeverity = "low" | "medium" | "high" | "critical" | string;
export type AlertStatus = "active" | "monitoring" | "resolved" | string;

export interface Health {
  status?: string;
  domain?: string;
  graphConnected?: boolean;
  graphSource?: string;
  engine?: string;
}

export interface PipelineSystem {
  name: string;
  displayName?: string;
  slaMinutes?: number;
  businessCriticality?: number;
  sourceReliability?: number;
  owner?: string;
  status?: PipelineStatus;
  lastRun?: string;
  description?: string;
  alertCount?: number;
  activeAlertCount?: number;
  upstreamCount?: number;
  downstreamCount?: number;
  upstream?: string[];
  downstream?: string[];
}

export interface FactorMap {
  impactScope?: number;
  sourceReliability?: number;
  recurrenceFrequency?: number;
  downstreamUrgency?: number;
  dataFreshness?: number;
  businessCriticality?: number;
  [key: string]: number | undefined;
}

export interface DataOpsAlert {
  alertId: string;
  alert_id?: string;
  eventId?: string;
  event_id?: string;
  dataset?: string;
  system?: string;
  systemName?: string;
  system_name?: string;
  systemDisplay?: string;
  system_display?: string;
  category?: string;
  actionTaken?: string;
  action_taken?: string;
  isCorrect?: boolean;
  is_correct?: boolean;
  severity?: AlertSeverity;
  recurrenceCount?: number;
  recurrence_count?: number;
  status?: AlertStatus;
  factors?: FactorMap;
  autoResolved?: boolean;
  auto_resolved?: boolean;
  aeRecommendation?: unknown;
  timestamp?: string;
  createdAt?: string;
  created_at?: string;
  detectedAt?: string;
  detected_at?: string;
  lastRun?: string;
  last_run?: string;
}

export interface AlertGroupAlert {
  alertId?: string;
  alert_id?: string;
  systemName?: string;
  system_name?: string;
  category?: string;
  severity?: AlertSeverity;
}

export interface AlertGroup {
  rootSystem?: string;
  root_system?: string;
  rootDisplay?: string;
  root_display?: string;
  alerts?: AlertGroupAlert[];
  cascadingSystems?: string[];
  cascading_systems?: string[];
  alertCount?: number;
  alert_count?: number;
}

export interface AlertGroupsResponse {
  groups?: AlertGroup[];
  ungrouped?: AlertGroupAlert[];
  totalAlerts?: number;
  total_alerts?: number;
  totalGroups?: number;
  total_groups?: number;
}

export interface AlertDetail {
  source?: string;
  alert?: DataOpsAlert;
  error?: string;
  alertId?: string;
}

export interface DependencyNode {
  system?: string;
  name?: string;
  displayName?: string;
  depth?: number;
  slaMinutes?: number;
  businessCriticality?: number;
  children?: DependencyNode[];
}

export interface BlastRadius {
  source?: string;
  alertId?: string;
  system?: string;
  affectedSystem?: string;
  tree?: DependencyNode;
  downstreamTree?: DependencyNode;
  totalAffected?: number;
  maxCriticality?: number;
  minSla?: number;
}

export interface AEImpactBreakdownEntry {
  alertsPrevented?: number;
  estimatedHoursSaved?: number;
}

export interface AEImpact {
  autoResolvedCount?: number;
  accuracy?: number;
  activeRules?: string[];
  rejectedRules?: string[];
  breakdown?: Record<string, AEImpactBreakdownEntry>;
  rejectedExample?: {
    variantId?: string;
    reason?: string;
  };
}

export interface Incident {
  incidentId?: string;
  title?: string;
  estimatedCost?: number;
  primaryAlertId?: string;
  affectedSystems?: string[];
  affectedDatasets?: string[];
  fingerprintInsight?: {
    sourceReliability?: number;
    recurrenceFrequency?: number;
    businessCriticality?: number;
    summary?: string;
  };
}

export interface PatternOriginStep {
  copilot?: string;
  ruleId?: string;
  description?: string;
  contribution?: string;
  warmStartPrior?: number;
}

export interface PatternOriginPattern {
  id?: string;
  variantId?: string;
  sourceCopilot?: string | null;
  sourceRule?: string | null;
  match?: Record<string, unknown>;
}

export interface GenealogyStage {
  copilot?: string;
  winRate?: number | null;
  win_rate?: number | null;
  decisions?: number | null;
  warmStart?: number | null;
  warm_start?: number | null;
}

export interface RuleGenealogyData {
  stages?: GenealogyStage[];
  improvement?: string;
  narrative?: string;
}

export interface PatternOrigin {
  source?: string;
  narrative?: string;
  chain?: PatternOriginStep[];
  genealogy?: RuleGenealogyData;
  patterns?: PatternOriginPattern[];
  rejected?: Array<{ id?: string; variantId?: string; reason?: string }>;
}

export interface ConservationMetrics {
  signal?: number;
  thetaMin?: number;
  headroom?: number;
}

export interface ConservationEvent {
  eventId?: string;
  timestamp?: string;
  requestedAction?: string;
  status?: "approved" | "denied" | string;
  reason?: string;
  metrics?: ConservationMetrics;
}

export interface ConservationHistory {
  events?: ConservationEvent[];
}

export interface PatternTransfer {
  transferId: string;
  sourceSystem: string;
  sourcePattern: string;
  targetSystem: string;
  targetAction: string;
  transferDate?: string;
  status: string;
  confidence: number;
  decisionsSinceTransfer: number;
  accuracyAtTarget: number | null;
  savingsEstimate: number | null;
  description: string;
}

export interface TransferStatusResponse {
  transfers: PatternTransfer[];
  summary: {
    totalTransfers: number;
    active: number;
    monitoring: number;
    pending: number;
    cumulativeSavings: number;
  };
}

export interface ConservationState {
  domain?: string;
  verifiedCount?: number;
  correctCount?: number;
  totalDecisions?: number;
  penaltyRatio?: number;
  signal?: number | null;
  thetaMin?: number | null;
  headroom?: number | null;
  status?: ConservationStatusLevel;
  passed?: boolean;
  currentThreshold?: number;
}

export interface ConservationWhatIfRequest {
  alpha: number;
  q: number;
  V: number;
  thetaMin?: number;
}

export interface TrajectoryPoint {
  decisions: number;
  iks: number;
  winRate: number;
  timestamp?: number;
}

export interface TrajectoryResponse {
  points?: TrajectoryPoint[];
  currentIks?: number;
  currentWinRate?: number;
  decisionsTotal?: number;
  daysActive?: number;
}

export interface FingerprintResponse {
  factors?: FactorItem[];
  overallWinRate?: number;
  perCategoryPrecision?: Record<string, number>;
  decisionsAnalyzed?: number;
}

export type EvolutionStatus = "promoted" | "rejected" | "shadow" | "created";

export interface EvolutionVariant {
  id: string;
  name: string;
  status: EvolutionStatus;
  description: string;
  shadowCount?: number;
  shadowWinRate?: number;
  conservationAtPromotion?: number;
  rejectReason?: string;
  sourceCopilot?: string;
  sourceRule?: string;
}

export interface FactorValue {
  value?: number;
  source?: string;
  detail?: string;
}

export interface FactorAutoFillResponse {
  source?: string;
  alertId?: string;
  factors?: Record<string, FactorValue>;
  allAutoComputed?: boolean;
}

export interface RecurrenceResponse {
  source?: string;
  alertId?: string;
  system?: string;
  category?: string;
  priorCount?: number;
  recurrenceFrequency?: number;
}

export interface AERecommendation {
  id?: string;
  variantId?: string;
  artifactType?: string;
  description?: string;
  impact?: string;
  confidence?: number;
  matchReason?: string;
  action?: string;
}

export interface AERecommendationResponse {
  alertId?: string;
  hasRecommendation?: boolean;
  recommendations?: AERecommendation[];
  count?: number;
  source?: string;
}

export interface SimilarAlert {
  eventId?: string;
  dataset?: string;
  category?: string;
  actionTaken?: string;
  isCorrect?: boolean;
  similarity?: number;
}

export interface SimilarAlertsResponse {
  similar?: SimilarAlert[];
  count?: number;
}

export interface DecisionEntry {
  decisionId?: string | null;
  alertId?: string | null;
  eventId?: string | null;
  system?: string | null;
  dataset?: string | null;
  category?: string | null;
  actionTaken?: string | null;
  scoreAction?: string | null;
  scoreConfidence?: number | null;
  outcome?: string | null;
  isCorrect?: boolean | null;
  date?: string | null;
  source?: string;
  factors?: Record<string, number> | null;
}

export interface ActionBreakdown {
  count?: number;
  correct?: number;
  winRate?: number | null;
  win_rate?: number | null;
}

export interface DecisionSummary {
  totalDecisions?: number;
  correct?: number;
  accuracy?: number | null;
  byAction?: Record<string, ActionBreakdown>;
  byCategory?: Record<string, ActionBreakdown>;
}

export interface DecisionExplorerResponse {
  decisions?: DecisionEntry[];
  total?: number;
  filtersApplied?: {
    system?: string | null;
    category?: string | null;
    action?: string | null;
    correct?: string | null;
  };
  summary?: DecisionSummary;
}

export interface CategoryAccuracy {
  category?: string;
  total?: number;
  correct?: number;
  accuracy?: number | null;
  trend?: "declining" | "improving" | "stable" | string;
  recentAccuracy?: number | null;
  alertLevel?: "critical" | "warning" | "ok" | string;
  alert?: boolean;
}

export interface AccuracyByCategoryResponse {
  categories?: Record<string, CategoryAccuracy>;
  overallAccuracy?: number | null;
  categoriesDeclining?: string[];
  categoriesImproving?: string[];
  totalDecisions?: number;
}

export interface CentroidShift {
  factor?: string;
  from?: number;
  to?: number;
  delta?: number;
}

export interface CentroidSnapshot {
  decisionIndex?: number;
  label?: string;
  centroidsSample?: Record<string, number>;
  topShifts?: CentroidShift[];
  note?: string;
}

export interface CentroidHistoryResponse {
  snapshots?: CentroidSnapshot[];
  factorNames?: string[];
  totalDecisions?: number;
}

export interface CentroidCheckpoint {
  decisionId?: string;
  decision_id?: string;
  category?: string;
  centroids?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  createdAt?: string;
  created_at?: string;
}

export interface SelfCentroidHistoryResponse {
  checkpoints?: CentroidCheckpoint[];
  total?: number;
}

export interface SelfCategoryAccuracy {
  category?: string;
  accuracy?: number;
  total?: number;
  correct?: number;
  alert?: boolean;
}

export interface SelfAccuracyByCategoryResponse {
  categories?: SelfCategoryAccuracy[];
  threshold?: number;
  overallVerified?: number;
  overall_verified?: number;
}

export interface SelfDecisionEntry {
  decisionId?: string;
  decision_id?: string;
  entityId?: string;
  entity_id?: string;
  category?: string;
  recommendedAction?: string;
  recommended_action?: string;
  actualAction?: string;
  actual_action?: string;
  action?: string;
  confidence?: number;
  factors?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  isCorrect?: boolean;
  is_correct?: boolean;
  createdAt?: number | string;
  created_at?: number | string;
  verifiedAt?: number | string;
  verified_at?: number | string;
}

export interface SelfDecisionExplorerResponse {
  decisions?: SelfDecisionEntry[];
  total?: number;
}

export interface Transformation {
  id?: string;
  name?: string;
  type?: string;
  source?: string;
  target?: string;
  avgDurationMinutes?: number;
  avgRows?: number;
  schemaColumns?: string[];
  lastRun?: string;
  status?: string;
}

export interface TransformationsResponse {
  system?: string;
  transformations?: Transformation[];
  summary?: {
    total?: number;
    totalDurationMinutes?: number;
    bottleneck?: string | null;
    bottleneckPct?: number;
  };
}

export interface BottleneckStep {
  id?: string;
  name?: string;
  durationMinutes?: number;
  pctOfTotal?: number;
  rows?: number;
  type?: string;
  status?: string;
}

export interface BottleneckRecommendation {
  action?: string;
  detail?: string;
  estimatedSpeedup?: string;
  estimatedSavingsMinutes?: number;
}

export interface BottleneckResponse {
  system?: string;
  totalDurationMinutes?: number;
  bottleneck?: BottleneckStep | null;
  recommendation?: BottleneckRecommendation | null;
  allStepsRanked?: BottleneckStep[];
}

export interface DownstreamImpact {
  system?: string;
  severity?: string;
  detail?: string;
}

export interface SchemaChange {
  sourceTable?: string;
  column?: string;
  changeType?: string;
  detected?: string;
  downstreamImpact?: number;
  impactedSystems?: string[];
  downstreamImpacts?: DownstreamImpact[];
  proposedFix?: string;
  alertsPrevented?: number;
}

export interface SchemaImpactResponse {
  system?: string;
  schemaChanges?: SchemaChange[];
  totalChanges?: number;
  totalImpacts?: number;
  totalAlertsPreventable?: number;
  sapPoCount?: number;
}

export interface OperationalRule {
  id?: string;
  name?: string;
  type?: string;
  category?: string;
  status?: string;
  system?: string;
  trigger?: string;
  recommendation?: string;
  description?: string;
  estimatedImpact?: string;
  expectedImpact?: string;
}

export interface OperationalRulesResponse {
  source?: string;
  rules?: OperationalRule[];
  total?: number;
  summary?: {
    proposed?: number;
    shadow?: number;
    promoted?: number;
    rejected?: number;
    [key: string]: number | undefined;
  };
}

export interface ProcessSignalMetric {
  name?: string;
  label?: string;
  value?: number | string;
  baseline?: number | string;
  unit?: string;
  deltaPct?: number;
}

export interface ProcessSignalVariant {
  id?: string;
  description?: string;
  reworkRatePct?: number;
  baselinePct?: number;
  [key: string]: string | number | boolean | undefined;
}

export interface ProcessSignalCorrelation {
  alertSystem?: string;
  processSignal?: string;
  confidence?: number;
  narrative?: string;
  signal?: string;
  factor?: string;
}

export interface ProcessSignalsResponse {
  system?: string;
  source?: string;
  signals?: Record<string, number | string>;
  metrics?: ProcessSignalMetric[];
  variant?: ProcessSignalVariant;
  correlation?: ProcessSignalCorrelation;
  celonisLive?: boolean;
  sapPoCount?: number;
  engine?: string;
  narrative?: string;
}

export interface ProcessTimelineActivity {
  id?: string;
  name?: string;
  avgDuration?: number;
  normalDuration?: number;
  currentDuration?: number;
  automationRate?: number;
  reworkRate?: number;
  isBottleneck?: boolean;
  slowdownMultiplier?: number | null;
}

export interface ProcessTimelineResponse {
  processModels?: Array<Record<string, unknown>>;
  activities?: ProcessTimelineActivity[];
  bottleneckId?: string;
  normalDuration?: number;
  currentDuration?: number;
  slowdownMultiplier?: number | null;
  dollarCalibration?: Record<string, number>;
  crossGraphRefs?: Record<string, unknown>;
}

export interface EnterpriseSystemHealth {
  connected?: boolean;
  status?: string;
  source?: string;
  live?: boolean;
  cached?: boolean;
  recordCount?: number;
  kpiCount?: number;
  nodeCount?: number;
  lastSync?: string | null;
  total?: number;
  count?: number;
  detail?: string;
  error?: string;
}

export interface EnterpriseHealth {
  sap?: EnterpriseSystemHealth;
  celonis?: EnterpriseSystemHealth;
  graph?: EnterpriseSystemHealth;
  overall?: "healthy" | "degraded" | "disconnected" | string;
  engineVersion?: string;
}

export interface SapPurchaseOrder {
  PurchaseOrder?: string;
  CompanyCode?: string;
  Supplier?: string;
  PurchaseOrderType?: string;
  CreationDate?: string;
  DocumentCurrency?: string;
  PurchasingOrganization?: string;
  PurchasingGroup?: string;
  PurchaseOrderDate?: string;
  [key: string]: unknown;
}

export interface SapPurchaseOrdersResponse {
  source?: string;
  total?: number;
  purchaseOrders?: SapPurchaseOrder[];
}

export interface ApplyFixConservationCheck {
  status?: string;
  currentAutomation?: number;
  projectedAutomation?: number;
  thetaMin?: number;
  safe?: boolean;
}

export interface ApplyFixRequest {
  alertId: string;
  option: string;
  optionLabel: string;
  entityType: "PurchaseOrder";
  entityId: string;
  payload: {
    matchingParameter: string;
  };
}

export interface ApplyFixResponse {
  status?: string;
  alertId?: string;
  option?: string;
  optionLabel?: string;
  sapResponse?: {
    d?: {
      PurchaseOrder?: string;
      Status?: string;
      MatchingParameter?: string;
      LastChangedDateTime?: string;
      [key: string]: unknown;
    };
    [key: string]: unknown;
  };
  conservationCheck?: ApplyFixConservationCheck;
  estimatedSavings?: string;
  timestamp?: string;
}

export interface CelonisKnowledgeModel {
  id?: string;
  name?: string;
  description?: string;
  [key: string]: unknown;
}

export interface CelonisKpi {
  id?: string;
  name?: string;
  value?: number | string;
  unit?: string;
  [key: string]: unknown;
}

export interface ProcessActivity {
  name?: string;
  activity?: string;
  durationHours?: number;
  avgDurationHours?: number;
  caseCount?: number;
  bottleneck?: boolean;
  bottleneckCause?: string;
  system?: string;
  [key: string]: unknown;
}

export interface CrossGraphInsight {
  finding?: string;
  title?: string;
  detail?: string;
  confidence?: number;
  monthlyImpactUsd?: number;
  annualImpactUsd?: number;
  annualizedSavingsUsd?: number;
  preventableImpactUsd?: number;
  sources?: string[];
  [key: string]: unknown;
}

export interface ProcessRecommendation {
  title?: string;
  recommendation?: string;
  annualizedSavingsUsd?: number;
  [key: string]: unknown;
}

export interface CompoundingTrajectory {
  annualSavingsUsd?: number;
  [key: string]: unknown;
}

export interface ProcessData {
  source?: string;
  processModel?: string;
  variant?: string;
  variantFrequency?: number;
  totalCases?: number;
  activities?: ProcessActivity[];
  crossGraphInsights?: CrossGraphInsight[];
  recommendations?: ProcessRecommendation[];
  compoundingTrajectory?: CompoundingTrajectory;
  knowledgeModels?: CelonisKnowledgeModel[];
  kpis?: CelonisKpi[];
  [key: string]: unknown;
}

export interface CelonisProcessDataResponse {
  source?: string;
  knowledgeModels?: CelonisKnowledgeModel[];
  kpis?: CelonisKpi[];
  processData?: ProcessData;
}

export interface Resolution {
  decisionId?: string | null;
  decision_id?: string | null;
  alertId?: string;
  alert_id?: string;
  date?: string;
  actionTaken?: string;
  action_taken?: string;
  outcome?: string;
  isCorrect?: boolean;
  is_correct?: boolean;
  category?: string;
  resolutionTimeMinutes?: number | null;
  resolution_time_minutes?: number | null;
  source?: string;
}

export interface SystemHistoryResponse {
  system?: string;
  resolutions?: Resolution[];
  total?: number;
  accuracy?: number | null;
  actionBreakdown?: Record<string, ActionBreakdown>;
  action_breakdown?: Record<string, ActionBreakdown>;
  bestAction?: string | null;
  best_action?: string | null;
  worstAction?: string | null;
  worst_action?: string | null;
}

export interface LifecycleEvent {
  type?: string;
  date?: string;
  detail?: string;
}

export interface RuleWithLifecycle {
  id?: string | null;
  variantId?: string | null;
  name?: string | null;
  description?: string | null;
  status?: string | null;
  winRate?: number | null;
  decisionsEvaluated?: number | null;
  rejectedReason?: string | null;
  sourceCopilot?: string | null;
  sourceRule?: string | null;
  warmStartPrior?: number | null;
  lifecycleEvents?: LifecycleEvent[];
}

export interface RuleLifecycleResponse {
  rules?: RuleWithLifecycle[];
  total?: number;
  summary?: {
    promoted?: number;
    rejected?: number;
    shadow?: number;
    proposed?: number;
    [key: string]: number | undefined;
  };
}

export interface AuditTrailStep {
  step?: string;
  label?: string;
  detail?: string;
  timestamp?: string | null;
  source?: string;
  data?: Record<string, unknown>;
  variantId?: string | null;
  variant_id?: string | null;
  action?: string | null;
  confidence?: number | null;
  actionTaken?: string | null;
  action_taken?: string | null;
  followedAe?: boolean | null;
  followed_ae?: boolean | null;
  isCorrect?: boolean | null;
  is_correct?: boolean | null;
  reward?: number | null;
}

export interface AuditTrailResponse {
  alertId?: string;
  alert_id?: string;
  system?: string | null;
  chain?: AuditTrailStep[];
  complete?: boolean;
}

export interface AuditTrailEntry {
  decisionId?: string;
  decision_id?: string;
  category?: string;
  recommendedAction?: string;
  recommended_action?: string;
  actualAction?: string;
  actual_action?: string;
  confidence?: number;
  factors?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  outcomeMetadata?: Record<string, unknown>;
  outcome_metadata?: Record<string, unknown>;
  isCorrect?: boolean;
  is_correct?: boolean;
  createdAt?: number | string;
  created_at?: number | string;
  verifiedAt?: number | string;
  verified_at?: number | string;
}

export interface SelfAuditTrailResponse {
  decision?: AuditTrailEntry | null;
  outcome?: AuditTrailEntry | null;
  chainComplete?: boolean;
  chain_complete?: boolean;
  trails?: AuditTrailEntry[];
  total?: number;
  error?: string;
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
  iksBefore?: number;
  iksAfter?: number;
  centroidDelta?: number;
  decisionsTotal?: number;
  outcome?: string;
  reward?: number;
  previousReward?: number | null;
  rewardMultiplier?: number;
}

export interface AlertMetadataPayload {
  decisionId: string;
  alertId?: string;
  systemName?: string;
  category?: string | null;
  actionTaken?: string;
  aeSuggested?: boolean;
  followedAe?: boolean;
  factors?: Record<string, number>;
}
