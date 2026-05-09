import type { Analytics, FingerprintResponse } from "../types";

const factorLabels: Record<string, string> = {
  conviction: "Conviction",
  research_depth: "Research",
  technical_signal: "Technical",
  position_size: "Position Size",
  time_horizon: "Time Horizon",
  market_regime: "Market Regime",
};

function level(weight: number): "HIGH" | "MODERATE" | "LOW" {
  if (weight > 0.6) {
    return "HIGH";
  }
  if (weight < 0.2) {
    return "LOW";
  }
  return "MODERATE";
}

function interpretation(weight: number): string {
  if (weight > 0.6) {
    return "strong";
  }
  if (weight < 0.2) {
    return "ignored";
  }
  return "moderate";
}

export default function EngineAssessment({
  factors,
  fingerprint,
  analytics,
  similarCount,
}: {
  factors: Record<string, number>;
  fingerprint?: FingerprintResponse;
  analytics?: Analytics;
  similarCount: number;
}) {
  const fingerprintFactors = fingerprint?.factors || [];
  const weighted = Object.entries(factors).map(([name, value]) => {
    const fp = fingerprintFactors.find((item) => item.name === name);
    return {
      name,
      value,
      weight: fp?.weight ?? value,
      label: fp?.displayName || factorLabels[name] || name,
    };
  });
  const top = [...weighted].sort((a, b) => b.weight - a.weight).slice(0, 3);
  const bottom = [...weighted].sort((a, b) => a.weight - b.weight)[0];

  return (
    <section className="copilot-card p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">Engine Assessment</h2>
          <p className="text-sm trading-muted">
            {similarCount} similar trades found · {analytics?.source || "live scorer"}
          </p>
        </div>
        <div className="rounded-md px-3 py-2 text-sm font-semibold" style={{ background: "var(--copilot-surface-muted)" }}>
          {fingerprint?.decisionsAnalyzed ?? analytics?.closedTrades ?? 0} analyzed
        </div>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-4">
        {top.map((factor) => (
          <FactorTile key={factor.name} {...factor} />
        ))}
        {bottom ? <FactorTile {...bottom} label={`${bottom.label} (lowest)`} /> : null}
      </div>
    </section>
  );
}

function FactorTile({ label, value, weight }: { label: string; value: number; weight: number }) {
  return (
    <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="text-xs trading-muted">{label}</div>
      <div className="mt-1 text-lg font-semibold">{level(weight)}</div>
      <div className="text-xs trading-muted">
        value {value.toFixed(2)} · {interpretation(weight)}
      </div>
    </div>
  );
}
