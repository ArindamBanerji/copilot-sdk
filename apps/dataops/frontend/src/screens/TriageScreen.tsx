import { useEffect, useMemo, useState } from "react";
import { ScoreResultCard } from "../../../../../copilot_sdk/frontend";
import {
  getAeRecommendation,
  getAlert,
  getAlertDeps,
  getAlertFactors,
  getAlertRecurrence,
  getConservationStatus,
  getFingerprint,
  getProcessSignals,
  getSimilar,
  getSystemHistory,
  learnAlert,
  saveAlertMetadata,
  scoreAlert,
} from "../api";
import ActionPicker, { actionFromScoreLabel, labelForAction } from "../components/ActionPicker";
import ApplyFixModal from "../components/ApplyFixModal";
import { CrossGraphInsightCard } from "../components/CrossGraphInsightCard";
import DependencyTree from "../components/DependencyTree";
import FactorAutoFill, { buildScoreFactors } from "../components/FactorAutoFill";
import ProcessSignalsPanel from "../components/ProcessSignalsPanel";
import RecurrenceBadge from "../components/RecurrenceBadge";
import ResolutionTimeline from "../components/ResolutionTimeline";
import ReasoningPanel from "../components/ReasoningPanel";
import SimilarAlertsPanel from "../components/SimilarAlertsPanel";
import SLACountdown from "../components/SLACountdown";
import type {
  AERecommendation,
  AERecommendationResponse,
  AlertDetail,
  BlastRadius,
  DataOpsAlert,
  FactorAutoFillResponse,
  FingerprintResponse,
  LearnResponse,
  ProcessSignalsResponse,
  RecurrenceResponse,
  ScoreResponse,
  SimilarAlert,
  SystemHistoryResponse,
  ApplyFixResponse,
} from "../types";

interface TriageScreenProps {
  selectedAlertId: string | null;
  onBack: () => void;
}

interface TriageData {
  detail: AlertDetail | null;
  deps: BlastRadius | null;
  factors: FactorAutoFillResponse | null;
  recurrence: RecurrenceResponse | null;
  recommendation: AERecommendationResponse | null;
}

const APPLY_FIX_DEMO = {
  option: "A",
  optionLabel: "Pre-join filter on MATKL_V2 range",
  entityId: "PO-4500001234",
  supplier: "Aster Rubber",
  matchingParameter: "MATKL_V2_FILTER",
  conservationPreview: {
    status: "GREEN",
    currentAutomation: 0.35,
    projectedAutomation: 0.38,
    safe: true,
  },
} as const;

export default function TriageScreen({ selectedAlertId, onBack }: TriageScreenProps) {
  const [data, setData] = useState<TriageData>({
    detail: null,
    deps: null,
    factors: null,
    recurrence: null,
    recommendation: null,
  });
  const [loading, setLoading] = useState(Boolean(selectedAlertId));
  const [criticalSettled, setCriticalSettled] = useState(!selectedAlertId);
  const [error, setError] = useState<string | null>(null);
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [score, setScore] = useState<ScoreResponse | null>(null);
  const [rewardLine, setRewardLine] = useState<{
    reward: number;
    previousReward?: number | null;
    rewardMultiplier?: number;
  } | null>(null);
  const [iksDelta, setIksDelta] = useState<number | undefined>();
  const [scoring, setScoring] = useState(false);
  const [similarAlerts, setSimilarAlerts] = useState<SimilarAlert[]>([]);
  const [similarLoading, setSimilarLoading] = useState(false);
  const [processSignals, setProcessSignals] = useState<ProcessSignalsResponse | null>(null);
  const [processSignalsLoading, setProcessSignalsLoading] = useState(false);
  const [systemHistory, setSystemHistory] = useState<SystemHistoryResponse | null>(null);
  const [systemHistoryLoading, setSystemHistoryLoading] = useState(false);
  const [fingerprint, setFingerprint] = useState<FingerprintResponse | null>(null);
  const [applyFixOpen, setApplyFixOpen] = useState(false);
  const [appliedFix, setAppliedFix] = useState<ApplyFixResponse | null>(null);
  const [conservationThetaMin, setConservationThetaMin] = useState<number | undefined>();

  useEffect(() => {
    if (!selectedAlertId) {
      return;
    }

    let cancelled = false;
    setCriticalSettled(false);
    setConservationThetaMin(undefined);
    setLoading(true);
    setError(null);
    setSelectedAction(null);
    setScore(null);
    setRewardLine(null);
    setIksDelta(undefined);
    setSimilarAlerts([]);
    setProcessSignals(null);
    setSystemHistory(null);
    setFingerprint(null);
    setApplyFixOpen(false);
    setAppliedFix(null);
    setSimilarLoading(false);
    setProcessSignalsLoading(false);
    setSystemHistoryLoading(false);

    Promise.all([
      getAlert(selectedAlertId),
      getAlertDeps(selectedAlertId).catch(() => null),
      getAlertFactors(selectedAlertId).catch(() => null),
      getAlertRecurrence(selectedAlertId).catch(() => null),
      getAeRecommendation(selectedAlertId).catch(() => null),
      getConservationStatus().catch(() => null),
    ])
      .then(([detail, deps, factors, recurrence, recommendation, conservation]) => {
        if (!cancelled) {
          setData({ detail, deps, factors, recurrence, recommendation });
          setConservationThetaMin(conservation?.thetaMin ?? undefined);
        }

        const loadedAlert = detail.alert || null;
        const systemName = getAlertSystemName(loadedAlert);
        if (systemName) {
          setProcessSignalsLoading(true);
          getProcessSignals(systemName)
            .then((payload) => {
              if (!cancelled) {
                setProcessSignals(payload);
              }
            })
            .catch(() => {
              if (!cancelled) {
                setProcessSignals(null);
              }
            })
            .finally(() => {
              if (!cancelled) {
                setProcessSignalsLoading(false);
              }
            });

          setSystemHistoryLoading(true);
          getSystemHistory(systemName, 5)
            .then((payload) => {
              if (!cancelled) {
                setSystemHistory(payload);
              }
            })
            .catch(() => {
              if (!cancelled) {
                setSystemHistory(null);
              }
            })
            .finally(() => {
              if (!cancelled) {
                setSystemHistoryLoading(false);
              }
            });
        }

        if (loadedAlert?.category && factors?.factors) {
          setSimilarLoading(true);
          getSimilar(buildScoreFactors(factors), loadedAlert.category)
            .then((payload) => {
              if (!cancelled) {
                setSimilarAlerts(payload.similar || []);
              }
            })
            .catch(() => {
              if (!cancelled) {
                setSimilarAlerts([]);
              }
            })
            .finally(() => {
              if (!cancelled) {
                setSimilarLoading(false);
              }
            });
        }
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Could not load alert triage context.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setCriticalSettled(true);
          setLoading(false);
        }
      });

    getFingerprint()
      .then((payload) => {
        if (!cancelled) {
          setFingerprint(payload);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setFingerprint(null);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedAlertId]);

  const alert = data.detail?.alert || null;
  const alertSystemName = getAlertSystemName(alert);
  const alertTimestamp = getAlertTimestamp(alert);
  const primaryRecommendation = useMemo(
    () => data.recommendation?.recommendations?.[0] || null,
    [data.recommendation],
  );
  const applyFixReady = Boolean(selectedAlertId && score && rewardLine && APPLY_FIX_DEMO.conservationPreview.safe);
  const dataReady =
    Boolean(selectedAlertId) &&
    !loading &&
    criticalSettled;

  async function handleAction(action: string) {
    if (!alert?.category || !selectedAlertId) {
      setError("Alert category is required before scoring.");
      return;
    }

    setAppliedFix(null);
    setSelectedAction(action);
    setScoring(true);
    setError(null);

    const factors = buildScoreFactors(data.factors);

    try {
      const scored = await scoreAlert({
        category: alert.category,
        factors,
        context: {
          alert_id: selectedAlertId,
          selected_action: action,
          ae_suggested: Boolean(primaryRecommendation),
        },
      });
      setScore(scored);
      await saveAlertMetadata({
        decisionId: scored.decisionId,
        alertId: selectedAlertId,
        systemName: alert.system,
        category: alert.category,
        actionTaken: action,
        aeSuggested: Boolean(primaryRecommendation),
        followedAe: actionMatchesRecommendation(action, primaryRecommendation),
        factors,
      });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Scoring failed.");
    } finally {
      setScoring(false);
    }
  }

  async function handleConfirm(decisionId: string, actionOverride?: string) {
    const actualAction = actionOverride || selectedAction || score?.action;
    if (!actualAction) {
      setError("No action selected for learning.");
      return;
    }

    setAppliedFix(null);
    try {
      const result = await learnAlert({
        decisionId,
        actualAction,
        outcome: "confirmed",
        context: {
          alert_id: selectedAlertId,
          previous_reward: null,
        },
      });
      applyLearnResult(result);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Learning update failed.");
    }
  }

  function applyLearnResult(result: LearnResponse) {
    setRewardLine({
      reward: Number(result.reward || 0),
      previousReward: result.previousReward ?? null,
      rewardMultiplier: result.rewardMultiplier,
    });
    if (typeof result.iksAfter === "number" && typeof result.iksBefore === "number") {
      setIksDelta(result.iksAfter - result.iksBefore);
    }
  }

  function handleApplyFixApplied(result: ApplyFixResponse, appliedAlertId: string) {
    if (appliedAlertId !== selectedAlertId) {
      return;
    }
    setAppliedFix(result);
  }

  if (!selectedAlertId) {
    return (
      <section data-screen-ready={String(!selectedAlertId)} className="copilot-card p-6">
        <button type="button" className="copilot-button-secondary mb-4 px-3 py-2 text-sm" onClick={onBack}>
          Back to Dashboard
        </button>
        <h2 className="text-lg font-semibold" style={{ color: "var(--copilot-text)" }}>
          Triage
        </h2>
        <p className="mt-2 text-sm dataops-muted">Select an alert from Dashboard to triage.</p>
      </section>
    );
  }

  if (loading) {
    return <TriageFrame onBack={onBack} message="Loading alert graph context..." ready={false} />;
  }

  return (
    <div data-screen-ready={String(dataReady)} className="grid gap-4">
      <section className="copilot-card p-5">
        <div className="mb-4 flex items-center justify-between gap-4">
          <button type="button" className="copilot-button-secondary px-3 py-2 text-sm" onClick={onBack}>
            Back to Dashboard
          </button>
          {data.detail?.source ? <span className="text-xs dataops-muted">Source: {data.detail.source}</span> : null}
        </div>

        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-sm font-semibold" style={{ color: "var(--copilot-primary)" }}>
              {selectedAlertId}
            </div>
            <h2 className="mt-1 text-2xl font-semibold" style={{ color: "var(--copilot-text)" }}>
              {alert?.dataset || "Unknown dataset"}
            </h2>
            <p className="mt-2 text-sm dataops-muted">
              {alertSystemName || "unknown system"} · {formatCategory(alert?.category)} · {alert?.severity || "unknown"} severity
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <RecurrenceBadge count={data.recurrence?.priorCount ?? alert?.recurrenceCount} />
            {primaryRecommendation ? (
              <span className="rounded-full px-2 py-1 text-xs font-semibold" style={{ background: "var(--copilot-primary-light)", color: "var(--copilot-primary)" }}>
                AE: {primaryRecommendation.variantId || primaryRecommendation.id || "matched"}
              </span>
            ) : null}
          </div>
        </div>
      </section>

      <SLACountdown
        slaMinutes={data.deps?.minSla}
        alertTimestamp={alertTimestamp}
        systemName={alertSystemName || "unknown system"}
      />

      {error ? (
        <div className="copilot-card p-4 text-sm" style={{ color: "var(--copilot-danger)" }}>{error}</div>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_28rem]">
        <div className="grid gap-4">
          <DependencyTree deps={data.deps} />
          <CrossGraphInsightCard alertId={selectedAlertId} />
          <ResolutionTimeline history={systemHistory} loading={systemHistoryLoading} />
          <ProcessSignalsPanel signals={processSignals} loading={processSignalsLoading} />
          <FactorAutoFill response={data.factors} />
          <SimilarAlertsPanel alerts={similarAlerts} loading={similarLoading} />
        </div>
        <div className="grid content-start gap-4">
          <ActionPicker
            recommendation={primaryRecommendation}
            selectedAction={selectedAction}
            disabled={scoring}
            onAction={handleAction}
          />
          {score ? (
            <>
              <ScoreResultCard
                result={score}
                onConfirm={(decisionId) => void handleConfirm(decisionId)}
                onOverride={(decisionId, action) => void handleConfirm(decisionId, actionFromScoreLabel(action))}
                iksDelta={iksDelta}
                rewardLine={rewardLine || undefined}
              />
              <section className="copilot-card p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-base font-semibold" style={{ color: "var(--copilot-text)" }}>
                      SAP Write-back
                    </h2>
                    <p className="mt-1 text-sm dataops-muted">
                      Confirm the score, then apply the MATKL_V2 guardrail through the fixture-backed SAP endpoint.
                    </p>
                  </div>
                  {appliedFix ? (
                    <span className="rounded-full px-2 py-1 text-xs font-semibold" style={{ background: "rgba(34, 197, 94, 0.12)", color: "var(--copilot-success)" }}>
                      Applied
                    </span>
                  ) : null}
                </div>
                <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                  <div className="text-sm dataops-muted">
                    {appliedFix?.estimatedSavings
                      ? `Estimated savings: ${appliedFix.estimatedSavings}`
                      : applyFixReady
                        ? "Conservation check is ready for SAP fixture write-back."
                        : "Confirm the recommended action before applying to SAP."}
                  </div>
                  <button
                    type="button"
                    className="copilot-button px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-60"
                    disabled={!applyFixReady}
                    onClick={() => setApplyFixOpen(true)}
                  >
                    {appliedFix ? "View Applied Fix" : "Apply to SAP"}
                  </button>
                </div>
              </section>
              <ReasoningPanel
                scoreResult={score}
                similarAlerts={similarAlerts}
                fingerprint={fingerprint}
                factorValues={data.factors}
                actionNames={score.actionNames}
              />
            </>
          ) : (
            <section className="copilot-card p-4 text-sm dataops-muted">
              {scoring ? "Scoring selected action..." : "Choose an action to score this alert."}
            </section>
          )}
        </div>
      </div>
      <ApplyFixModal
        open={applyFixOpen}
        alertId={selectedAlertId}
        option={APPLY_FIX_DEMO.option}
        optionLabel={APPLY_FIX_DEMO.optionLabel}
        entityId={APPLY_FIX_DEMO.entityId}
        supplier={APPLY_FIX_DEMO.supplier}
        matchingParameter={APPLY_FIX_DEMO.matchingParameter}
        conservationPreview={{
          ...APPLY_FIX_DEMO.conservationPreview,
          thetaMin: conservationThetaMin,
        }}
        onClose={() => setApplyFixOpen(false)}
        onApplied={handleApplyFixApplied}
      />
    </div>
  );
}

function TriageFrame({ onBack, message, ready = false }: { onBack: () => void; message: string; ready?: boolean }) {
  return (
    <section data-screen-ready={String(ready)} className="copilot-card p-6">
      <button type="button" className="copilot-button-secondary mb-4 px-3 py-2 text-sm" onClick={onBack}>
        Back to Dashboard
      </button>
      <p className="text-sm dataops-muted">{message}</p>
    </section>
  );
}

function actionMatchesRecommendation(action: string, recommendation: AERecommendation | null): boolean {
  if (!recommendation) {
    return false;
  }
  const normalized = `${recommendation.description || ""} ${recommendation.impact || ""}`.toLowerCase();
  if (normalized.includes(action.replace(/_/g, " ")) || normalized.includes(labelForAction(action).toLowerCase())) {
    return true;
  }
  if (action === "pause_downstream") {
    return normalized.includes("pause");
  }
  if (action === "escalate_to_owner") {
    return normalized.includes("escalate");
  }
  if (action === "auto_approve") {
    return normalized.includes("auto");
  }
  return false;
}

function formatCategory(value?: string): string {
  return value ? value.replace(/_/g, " ") : "uncategorized";
}

function getAlertSystemName(alert: DataOpsAlert | null): string {
  if (!alert) {
    return "";
  }
  const raw = alert as unknown as Record<string, unknown>;
  if (raw.systemName || raw.system_name) {
    return String(raw.systemName || raw.system_name);
  }
  if (typeof raw.system === "string") {
    return raw.system;
  }
  if (isRecord(raw.system)) {
    return stringOr(raw.system.name) || stringOr(raw.system.displayName) || stringOr(raw.system.display_name);
  }
  return "";
}

function getAlertTimestamp(alert: DataOpsAlert | null): string | null {
  if (!alert) {
    return null;
  }
  const raw = alert as unknown as Record<string, unknown>;
  const system = isRecord(raw.system) ? raw.system : {};
  return (
    stringOr(raw.timestamp) ||
    stringOr(raw.createdAt) ||
    stringOr(raw.created_at) ||
    stringOr(raw.detectedAt) ||
    stringOr(raw.detected_at) ||
    stringOr(system.lastRun) ||
    stringOr(system.last_run) ||
    stringOr(raw.lastRun) ||
    stringOr(raw.last_run) ||
    null
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function stringOr(value: unknown): string {
  return typeof value === "string" ? value : "";
}
