import type { FactorAutoFillResponse, FactorValue } from "../types";

export const DATAOPS_FACTORS = [
  { key: "impact_scope", camelKey: "impactScope", label: "Impact scope" },
  { key: "source_reliability", camelKey: "sourceReliability", label: "Source reliability" },
  { key: "recurrence_frequency", camelKey: "recurrenceFrequency", label: "Recurrence frequency" },
  { key: "downstream_urgency", camelKey: "downstreamUrgency", label: "Downstream urgency" },
  { key: "data_freshness", camelKey: "dataFreshness", label: "Data freshness" },
  { key: "business_criticality", camelKey: "businessCriticality", label: "Business criticality" },
] as const;

interface FactorAutoFillProps {
  response: FactorAutoFillResponse | null;
}

export default function FactorAutoFill({ response }: FactorAutoFillProps) {
  const source = response?.source || "unknown";
  const title = response?.allAutoComputed
    ? "All factors auto-computed from graph"
    : source === "fixture"
      ? "Factors auto-computed from fixture graph"
      : "Factor auto-fill";

  return (
    <section className="copilot-card p-4">
      <div className="mb-4">
        <h2 className="dataops-section-title">{title}</h2>
        <p className="text-sm dataops-muted">Source: {source}</p>
      </div>
      <div className="grid gap-3">
        {DATAOPS_FACTORS.map((factor) => {
          const entry = getFactorEntry(response, factor.key, factor.camelKey);
          const value = clampUnit(entry?.value);
          return (
            <div key={factor.key} className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
              <div className="mb-2 flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>{factor.label}</div>
                  <div className="text-xs dataops-muted">{entry?.source || "missing"}</div>
                </div>
                <span className="font-semibold" style={{ color: "var(--copilot-primary)" }}>{Math.round(value * 100)}%</span>
              </div>
              <div className="h-2 rounded-full" style={{ background: "var(--copilot-surface-muted)" }}>
                <div className="h-full rounded-full" style={{ width: `${value * 100}%`, background: "var(--copilot-primary)" }} />
              </div>
              {entry?.detail ? <div className="mt-2 text-xs dataops-muted">{entry.detail}</div> : null}
            </div>
          );
        })}
      </div>
    </section>
  );
}

export function buildScoreFactors(response: FactorAutoFillResponse | null): Record<string, number> {
  const factors: Record<string, number> = {};
  for (const factor of DATAOPS_FACTORS) {
    const entry = getFactorEntry(response, factor.key, factor.camelKey);
    factors[factor.key] = clampUnit(entry?.value);
  }
  return factors;
}

function getFactorEntry(
  response: FactorAutoFillResponse | null,
  snakeKey: string,
  camelKey: string,
): FactorValue | undefined {
  const factors = response?.factors || {};
  return factors[snakeKey] || factors[camelKey];
}

function clampUnit(value: unknown): number {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return 0;
  }
  return Math.max(0, Math.min(1, number));
}
