export interface ReasoningPanelProps {
  scoreResult: GenericScoreResult;
  similarItems?: SimilarEvidenceItem[];
  similarAlerts?: SimilarEvidenceItem[];
  fingerprint?: GenericFingerprint | null;
  factorValues?: GenericFactorValues | null;
  actionNames: string[];
  factorNames: string[];
  actionLabels?: Record<string, string>;
  factorLabels?: Record<string, string>;
  title?: string;
}

export interface GenericScoreResult {
  action?: string;
  actionIndex?: number;
  confidence?: number;
  probabilities?: unknown[];
  category?: string;
  factors?: Record<string, unknown>;
}

export interface SimilarEvidenceItem {
  actionTaken?: unknown;
  action_taken?: unknown;
  action?: unknown;
  isCorrect?: unknown;
  is_correct?: unknown;
  correct?: unknown;
  eventId?: unknown;
  event_id?: unknown;
  id?: unknown;
  similarity?: unknown;
}

export interface GenericFingerprint {
  factors?: GenericFingerprintFactor[];
  decisionsAnalyzed?: number;
  decisions_analyzed?: number;
}

export interface GenericFingerprintFactor {
  name?: string;
  weight?: number;
  sigma?: number;
  interpretation?: string;
}

export type GenericFactorValues =
  | Record<string, unknown>
  | {
      factors?: Record<string, unknown>;
    };

interface FactorDriver {
  key: string;
  label: string;
  value: number;
  fingerprint?: {
    weight: number;
    sigma: number;
    interpretation?: string;
  };
}

interface ActionEvidence {
  action: string;
  correct: number;
  total: number;
  winRate: number;
}

export default function ReasoningPanel({
  scoreResult,
  similarItems,
  similarAlerts,
  fingerprint,
  factorValues,
  actionNames,
  factorNames,
  actionLabels,
  factorLabels,
  title = "Why This Recommendation?",
}: ReasoningPanelProps) {
  const items = similarItems || similarAlerts || [];
  const factors = buildFactorDrivers(scoreResult, factorValues, fingerprint, factorNames, factorLabels).slice(0, 2);
  const evidence = buildHistoricalEvidence(items);
  const probabilityRows = buildProbabilityRows(scoreResult, actionNames, actionLabels);
  const decisionsAnalyzed = getDecisionsAnalyzed(fingerprint);
  const hasFingerprint = Boolean(fingerprint?.factors?.length);

  return (
    <section className="copilot-card p-4">
      <div className="mb-4">
        <h2 className="text-base font-semibold" style={{ color: "var(--copilot-text)" }}>
          {title}
        </h2>
        <p className="mt-1 text-sm" style={{ color: "var(--copilot-text-muted)" }}>
          Current factors, similar decisions, and model confidence behind {stringOr(scoreResult.action) || "this action"}.
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
                <p className="text-xs" style={{ color: "var(--copilot-text-muted)" }}>
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
                      <p className="mt-1 text-xs" style={{ color: "var(--copilot-text-muted)" }}>
                        {factorInsight(factor)}
                      </p>
                    </div>
                    <span className="font-semibold" style={{ color: "var(--copilot-primary)" }}>
                      {formatPercent(factor.value)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm" style={{ color: "var(--copilot-text-muted)" }}>
              No factor values available for this score.
            </p>
          )}
        </section>

        <section className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <h3 className="mb-3 text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>
            Historical Evidence
          </h3>
          {evidence.length === 0 ? (
            <p className="text-sm" style={{ color: "var(--copilot-text-muted)" }}>
              No similar decisions found. This is a novel situation.
            </p>
          ) : (
            <div className="grid gap-3">
              <p className="text-sm" style={{ color: "var(--copilot-text-muted)" }}>
                {historicalNarrative(evidence[0], actionLabels)}
              </p>
              {evidence.map((row) => (
                <div key={row.action} className="flex items-center justify-between gap-3 text-sm">
                  <span style={{ color: "var(--copilot-text)" }}>{labelFor(row.action, actionLabels)}</span>
                  <span style={{ color: "var(--copilot-text-muted)" }}>
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

        <footer className="text-xs" style={{ color: "var(--copilot-text-muted)" }}>
          {typeof decisionsAnalyzed === "number"
            ? `Learned from ${decisionsAnalyzed} verified decisions.`
            : "Learning history unavailable."}
        </footer>
      </div>
    </section>
  );
}

function buildFactorDrivers(
  scoreResult: GenericScoreResult,
  factorValues: GenericFactorValues | null | undefined,
  fingerprint: GenericFingerprint | null | undefined,
  factorNames: string[],
  factorLabels?: Record<string, string>,
): FactorDriver[] {
  const scoreFactors = scoreResult.factors || {};
  const fingerprintByName = new Map(
    (fingerprint?.factors || [])
      .filter((factor) => typeof factor.name === "string")
      .map((factor) => [factor.name as string, factor]),
  );

  return factorNames
    .map((key) => {
      const fallback = readFactorValue(factorValues, key);
      const value = numberOr(scoreFactors[key] ?? scoreFactors[toCamelCase(key)] ?? fallback, NaN);
      const fingerprintFactor = fingerprintByName.get(key) || fingerprintByName.get(toCamelCase(key));
      return {
        key,
        label: labelFor(key, factorLabels),
        value,
        fingerprint: fingerprintFactor
          ? {
              weight: numberOr(fingerprintFactor.weight, 0),
              sigma: numberOr(fingerprintFactor.sigma, 0),
              interpretation: stringOr(fingerprintFactor.interpretation),
            }
          : undefined,
      };
    })
    .filter((factor) => Number.isFinite(factor.value))
    .sort((left, right) => right.value - left.value);
}

function readFactorValue(source: GenericFactorValues | null | undefined, key: string): unknown {
  if (!source || typeof source !== "object") {
    return undefined;
  }
  const record = source as Record<string, unknown>;
  const factorMap = isRecord(record.factors) ? record.factors : record;
  const direct = factorMap[key] ?? factorMap[toCamelCase(key)];
  if (isRecord(direct)) {
    return direct.value;
  }
  return direct;
}

function buildHistoricalEvidence(items: SimilarEvidenceItem[]): ActionEvidence[] {
  const counts = new Map<string, { correct: number; total: number }>();
  for (const item of items) {
    const action = stringOr(item.actionTaken ?? item.action_taken ?? item.action) || "unknown";
    const current = counts.get(action) || { correct: 0, total: 0 };
    current.total += 1;
    if (Boolean(item.isCorrect ?? item.is_correct ?? item.correct)) {
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

function buildProbabilityRows(
  scoreResult: GenericScoreResult,
  actionNames: string[],
  actionLabels?: Record<string, string>,
) {
  return actionNames.map((action, index) => {
    const probability = numberOr(scoreResult.probabilities?.[index], 0);
    return {
      action,
      label: labelFor(action, actionLabels),
      probability: clampUnit(probability),
      recommended: isRecommended(scoreResult, action, index, actionLabels),
    };
  });
}

function isRecommended(
  scoreResult: GenericScoreResult,
  action: string,
  index: number,
  actionLabels?: Record<string, string>,
): boolean {
  const scoreAction = stringOr(scoreResult.action).toLowerCase();
  const label = labelFor(action, actionLabels).toLowerCase();
  return (
    index === scoreResult.actionIndex ||
    scoreAction === action.toLowerCase() ||
    scoreAction === label ||
    scoreAction === humanize(action).toLowerCase()
  );
}

function factorInsight(factor: FactorDriver): string {
  const valueSignal = factor.value > 0.7 ? "HIGH" : factor.value > 0.4 ? "moderate" : "low";
  if (!factor.fingerprint) {
    return `${valueSignal} current decision driver.`;
  }

  const { weight, sigma, interpretation } = factor.fingerprint;
  if (interpretation) {
    return `${valueSignal} current driver; learned profile says ${interpretation}.`;
  }

  let learnedSignal = "moderate signal";
  if (weight > 0.5 && sigma < 0.15) {
    learnedSignal = "dominant, clean signal";
  } else if (sigma > 0.2) {
    learnedSignal = "noisy, inconsistent outcomes";
  }
  return `${valueSignal} current driver; learned profile marks this as ${learnedSignal}.`;
}

function historicalNarrative(best: ActionEvidence, actionLabels?: Record<string, string>): string {
  if (best.winRate > 0.5) {
    return `${labelFor(best.action, actionLabels)} has the best track record for this profile.`;
  }
  return "Mixed results -- no clear winner among similar decisions.";
}

function getDecisionsAnalyzed(fingerprint: GenericFingerprint | null | undefined): number | undefined {
  const value = fingerprint?.decisionsAnalyzed ?? fingerprint?.decisions_analyzed;
  const number = Number(value);
  return Number.isFinite(number) ? number : undefined;
}

function labelFor(key: string, labels?: Record<string, string>): string {
  return labels?.[key] || humanize(key);
}

function humanize(key: string): string {
  return key
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/^./, (char) => char.toUpperCase());
}

function toCamelCase(key: string): string {
  return key.replace(/_([a-z])/g, (_, letter: string) => letter.toUpperCase());
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

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
