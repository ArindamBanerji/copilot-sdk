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

export interface PatternOrigin {
  source?: string;
  narrative?: string;
  chain?: PatternOriginStep[];
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
  engine?: string;
  narrative?: string;
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

export interface ActionBreakdown {
  count?: number;
  correct?: number;
  winRate?: number | null;
  win_rate?: number | null;
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
  actionTaken?: string;
  aeSuggested?: boolean;
  followedAe?: boolean;
  factors?: Record<string, number>;
}
