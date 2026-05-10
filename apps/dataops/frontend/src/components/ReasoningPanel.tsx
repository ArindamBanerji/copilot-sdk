import { DATAOPS_ACTIONS } from "./ActionPicker";
import { DATAOPS_FACTORS } from "./FactorAutoFill";
import type {
  FactorAutoFillResponse,
  FingerprintResponse,
  ScoreResponse,
  SimilarAlert,
} from "../types";

interface ReasoningPanelProps {
  scoreResult: ScoreResponse;
  similarAlerts: SimilarAlert[];
  fingerprint: FingerprintResponse | null;
  factorValues: FactorAutoFillResponse | null;
  actionNames?: string[];
}

interface FactorDriver {
  key: string;
  label: string;
  value: number;
  fingerprint?: {
    weight: number;
    sigma: number;
  };
}

interface ActionEvidence {
  action: string;
  correct: number;
  total: number;
  winRate: number;
}

const ACTION_LABELS: Record<string, string> = {
  auto_approve: "Auto approve",
  investigate: "Investigate",
  escalate_to_owner: "Escalate to owner",
  pause_downstream: "Pause downstream",
  refer_to_specialist: "Refer to specialist",
};

export default function ReasoningPanel({
  scoreResult,
  similarAlerts,
  fingerprint,
  factorValues,
  actionNames,
}: ReasoningPanelProps) {
  const factors = buildFactorDrivers(scoreResult, factorValues, fingerprint).slice(0, 2);
  const evidence = buildHistoricalEvidence(similarAlerts);
  const probabilityRows = buildProbabilityRows(scoreResult, actionNames);
  const decisionsAnalyzed = getDecisionsAnalyzed(fingerprint);
  const hasFingerprint = Boolean(fingerprint?.factors?.length);

  return (
    <section className="copilot-card p-4">
      <div className="mb-4">
        <h2 className="dataops-section-title">Why This Recommendation?</h2>
        <p className="text-sm dataops-muted">
          Current graph factors, similar decisions, and model confidence behind {scoreResult.action || "this action"}.
        </p>
      </div>

      <div className="grid gap-4">
        <section className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
            Factor Analysis
          </h3>
          {factors.length > 0 ? (
            <div className="grid gap-3">
              {!hasFingerprint ? (
                <p className="text-xs dataops-muted">
                  Fingerprint not yet available; showing highest current factor values.
                </p>
              ) : null}
              {factors.map((factor) => (
                <div key={factor.key} className="rounded-md p-3" style={{ background: "var(--copilot-surface-muted)" }}>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
                        {factor.label}
                      </div>
                      <p className="mt-1 text-xs dataops-muted">{factorInsight(factor)}</p>
                    </div>
                    <span className="font-semibold" style={{ color: "var(--copilot-primary)" }}>
                      {formatPercent(factor.value)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm dataops-muted">No factor values available for this score.</p>
          )}
        </section>

        <section className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
            Historical Evidence
          </h3>
          {evidence.length === 0 ? (
            <p className="text-sm dataops-muted">No similar decisions found. This is a novel situation.</p>
          ) : (
            <div className="grid gap-3">
              <p className="text-sm dataops-muted">{historicalNarrative(evidence[0])}</p>
              {evidence.map((row) => (
                <div key={row.action} className="flex items-center justify-between gap-3 text-sm">
                  <span style={{ color: "var(--copilot-text)" }}>{labelForAction(row.action)}</span>
                  <span className="dataops-muted">
                    {row.correct}/{row.total} · {formatPercent(row.winRate)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
            Confidence Breakdown
          </h3>
          <div className="grid gap-2">
            {probabilityRows.map((row) => (
              <div key={row.action}>
                <div className="mb-1 flex items-center justify-between text-xs">
                  <span style={{ color: row.recommended ? "var(--copilot-primary)" : "var(--copilot-text-muted)" }}>
                    {row.label}
                  </span>
                  <span style={{ color: "var(--copilot-text)" }}>{formatPercent(row.probability)}</span>
                </div>
                <div className="h-2 rounded-full" style={{ background: "var(--copilot-surface-muted)" }}>
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${clampUnit(row.probability) * 100}%`,
                      background: row.recommended ? "var(--copilot-primary)" : "var(--copilot-accent)",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>

        <footer className="text-xs dataops-muted">
          {typeof decisionsAnalyzed === "number"
            ? `Learned from ${decisionsAnalyzed} verified decisions.`
            : "Learning history unavailable."}
        </footer>
      </div>
    </section>
  );
}

function buildFactorDrivers(
  scoreResult: ScoreResponse,
  factorValues: FactorAutoFillResponse | null,
  fingerprint: FingerprintResponse | null,
): FactorDriver[] {
  const scoreFactors = scoreResult.factors || {};
  const fingerprintByName = new Map(
    (fingerprint?.factors || []).map((factor) => [factor.name, factor]),
  );

  return DATAOPS_FACTORS.map((factor) => {
    const fallback = factorValues?.factors?.[factor.key] || factorValues?.factors?.[factor.camelKey];
    const value = numberOr(scoreFactors[factor.key] ?? scoreFactors[factor.camelKey] ?? fallback?.value, NaN);
    const fingerprintFactor = fingerprintByName.get(factor.key) || fingerprintByName.get(factor.camelKey);
    return {
      key: factor.key,
      label: displayName(factor.key),
      value,
      fingerprint: fingerprintFactor
        ? {
            weight: numberOr(fingerprintFactor.weight, 0),
            sigma: numberOr(fingerprintFactor.sigma, 0),
          }
        : undefined,
    };
  })
    .filter((factor) => Number.isFinite(factor.value))
    .sort((left, right) => right.value - left.value);
}

function buildHistoricalEvidence(alerts: SimilarAlert[]): ActionEvidence[] {
  const counts = new Map<string, { correct: number; total: number }>();
  for (const alert of alerts) {
    const raw = alert as SimilarAlert & { action_taken?: string; is_correct?: boolean };
    const action = stringOr(alert.actionTaken || raw.action_taken) || "unknown";
    const current = counts.get(action) || { correct: 0, total: 0 };
    current.total += 1;
    if (Boolean(alert.isCorrect ?? raw.is_correct)) {
      current.correct += 1;
    }
    counts.set(action, current);
  }

  return Array.from(counts.entries())
    .map(([action, value]) => ({
      action,
      correct: value.correct,
      total: value.total,
      winRate: value.total > 0 ? value.correct / value.total : 0,
    }))
    .sort((left, right) => right.winRate - left.winRate || right.total - left.total);
}

function buildProbabilityRows(scoreResult: ScoreResponse, actionNames?: string[]) {
  const actionOrder = actionNames?.length ? actionNames : DATAOPS_ACTIONS.map((action) => action.value);
  return DATAOPS_ACTIONS.map((action, index) => {
    const sourceIndex = actionOrder.findIndex((name) => name === action.value || name === action.scoreLabel || name === action.label);
    const probabilityIndex = sourceIndex >= 0 ? sourceIndex : index;
    const probability = numberOr(scoreResult.probabilities?.[probabilityIndex], 0);
    return {
      action: action.value,
      label: labelForAction(action.value),
      probability: clampUnit(probability),
      recommended: probabilityIndex === scoreResult.actionIndex || scoreResult.action === action.scoreLabel || scoreResult.action === action.label,
    };
  });
}

function factorInsight(factor: FactorDriver): string {
  const valueSignal = factor.value > 0.7 ? "HIGH" : factor.value > 0.4 ? "moderate" : "low";
  if (!factor.fingerprint) {
    return `${valueSignal} current alert driver.`;
  }

  const { weight, sigma } = factor.fingerprint;
  let learnedSignal = "moderate signal";
  if (weight > 0.5 && sigma < 0.15) {
    learnedSignal = "dominant, clean signal";
  } else if (sigma > 0.2) {
    learnedSignal = "noisy, inconsistent outcomes";
  }
  return `${valueSignal} current driver; learned profile marks this as ${learnedSignal}.`;
}

function historicalNarrative(best: ActionEvidence): string {
  if (best.winRate > 0.5) {
    return `${labelForAction(best.action)} has the best track record for this factor profile.`;
  }
  return "Mixed results -- no clear winner among similar decisions.";
}

function getDecisionsAnalyzed(fingerprint: FingerprintResponse | null): number | undefined {
  const raw = fingerprint as (FingerprintResponse & { decisions_analyzed?: number }) | null;
  const value = raw?.decisionsAnalyzed ?? raw?.decisions_analyzed;
  const number = Number(value);
  return Number.isFinite(number) ? number : undefined;
}

function displayName(key: string): string {
  const names: Record<string, string> = {
    impact_scope: "Impact scope",
    source_reliability: "Source reliability",
    recurrence_frequency: "Recurrence",
    downstream_urgency: "Downstream urgency",
    data_freshness: "Data freshness",
    business_criticality: "Business criticality",
  };
  return names[key] || key.replace(/_/g, " ");
}

function labelForAction(action: string): string {
  return ACTION_LABELS[action] || action.replace(/_/g, " ");
}

function formatPercent(value: number): string {
  return `${Math.round(clampUnit(value) * 100)}%`;
}

function clampUnit(value: number): number {
  if (!Number.isFinite(value)) {
    return 0;
  }
  return Math.max(0, Math.min(1, value));
}

function numberOr(value: unknown, fallback: number): number {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function stringOr(value: unknown): string {
  return typeof value === "string" ? value : "";
}
