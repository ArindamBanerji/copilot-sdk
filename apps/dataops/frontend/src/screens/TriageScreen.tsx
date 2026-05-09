import { useEffect, useMemo, useState } from "react";
import { ScoreResultCard } from "../../../../../copilot_sdk/frontend";
import {
  getAeRecommendation,
  getAlert,
  getAlertDeps,
  getAlertFactors,
  getAlertRecurrence,
  learnAlert,
  saveAlertMetadata,
  scoreAlert,
} from "../api";
import ActionPicker, { actionFromScoreLabel, labelForAction } from "../components/ActionPicker";
import DependencyTree from "../components/DependencyTree";
import FactorAutoFill, { buildScoreFactors } from "../components/FactorAutoFill";
import RecurrenceBadge from "../components/RecurrenceBadge";
import type {
  AERecommendation,
  AERecommendationResponse,
  AlertDetail,
  BlastRadius,
  FactorAutoFillResponse,
  LearnResponse,
  RecurrenceResponse,
  ScoreResponse,
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

export default function TriageScreen({ selectedAlertId, onBack }: TriageScreenProps) {
  const [data, setData] = useState<TriageData>({
    detail: null,
    deps: null,
    factors: null,
    recurrence: null,
    recommendation: null,
  });
  const [loading, setLoading] = useState(false);
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

  useEffect(() => {
    if (!selectedAlertId) {
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);
    setSelectedAction(null);
    setScore(null);
    setRewardLine(null);
    setIksDelta(undefined);

    Promise.all([
      getAlert(selectedAlertId),
      getAlertDeps(selectedAlertId),
      getAlertFactors(selectedAlertId),
      getAlertRecurrence(selectedAlertId),
      getAeRecommendation(selectedAlertId),
    ])
      .then(([detail, deps, factors, recurrence, recommendation]) => {
        if (!cancelled) {
          setData({ detail, deps, factors, recurrence, recommendation });
        }
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Could not load alert triage context.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedAlertId]);

  const alert = data.detail?.alert || null;
  const primaryRecommendation = useMemo(
    () => data.recommendation?.recommendations?.[0] || null,
    [data.recommendation],
  );

  async function handleAction(action: string) {
    if (!alert?.category || !selectedAlertId) {
      setError("Alert category is required before scoring.");
      return;
    }

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

  if (!selectedAlertId) {
    return (
      <section className="copilot-card p-6">
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
    return <TriageFrame onBack={onBack} message="Loading alert graph context..." />;
  }

  return (
    <div className="grid gap-4">
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
              {alert?.system || "unknown system"} · {formatCategory(alert?.category)} · {alert?.severity || "unknown"} severity
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

      {error ? (
        <div className="copilot-card p-4 text-sm" style={{ color: "var(--copilot-danger)" }}>{error}</div>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_28rem]">
        <div className="grid gap-4">
          <DependencyTree deps={data.deps} />
          <FactorAutoFill response={data.factors} />
        </div>
        <div className="grid content-start gap-4">
          <ActionPicker
            recommendation={primaryRecommendation}
            selectedAction={selectedAction}
            disabled={scoring}
            onAction={handleAction}
          />
          {score ? (
            <ScoreResultCard
              result={score}
              onConfirm={(decisionId) => void handleConfirm(decisionId)}
              onOverride={(decisionId, action) => void handleConfirm(decisionId, actionFromScoreLabel(action))}
              iksDelta={iksDelta}
              rewardLine={rewardLine || undefined}
            />
          ) : (
            <section className="copilot-card p-4 text-sm dataops-muted">
              {scoring ? "Scoring selected action..." : "Choose an action to score this alert."}
            </section>
          )}
        </div>
      </div>
    </div>
  );
}

function TriageFrame({ onBack, message }: { onBack: () => void; message: string }) {
  return (
    <section className="copilot-card p-6">
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
