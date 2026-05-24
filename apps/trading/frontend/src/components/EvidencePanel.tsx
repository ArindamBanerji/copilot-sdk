import { useEffect, useState } from "react";
import { fetchEvidence } from "../api";
import type { EvidenceResponse } from "../types";

const FACTOR_LABELS: Record<string, string> = {
  signal_alignment: "Signal alignment",
  market_regime: "Regime fit",
  position_sizing: "Position sizing",
  timing_quality: "Timing",
  risk_reward_actual: "Risk/reward",
  emotional_indicator: "Decision context",
  signal_confidence: "Signal confidence",
};

function pct(value: number | null | undefined): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "-";
  return `${Math.round(value * 100)}%`;
}

function label(value: unknown): string {
  return typeof value === "string" && value ? value.replace(/_/g, " ") : "-";
}

function factorLabel(name: string): string {
  return FACTOR_LABELS[name] || label(name);
}

export default function EvidencePanel({ tradeId }: { tradeId: string }) {
  const [evidence, setEvidence] = useState<EvidenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setUnavailable(false);
      const payload = await fetchEvidence(tradeId);
      if (cancelled) return;
      setEvidence(payload);
      setUnavailable(!payload);
      setLoading(false);
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [tradeId]);

  if (!tradeId) return null;

  if (loading) {
    return (
      <section className="copilot-card p-4">
        <p className="text-sm trading-muted">Loading evidence...</p>
      </section>
    );
  }

  if (unavailable || !evidence) {
    return (
      <section className="copilot-card p-4">
        <h3 className="text-base font-semibold">Evidence</h3>
        <p className="mt-2 text-sm trading-muted">Evidence is unavailable for this trade.</p>
      </section>
    );
  }

  const factorEntries = Object.entries(evidence.factors || {}).filter(([, value]) => typeof value === "number");

  return (
    <section className="copilot-card p-4" style={{ borderLeft: "4px solid var(--copilot-primary)" }}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold">Evidence</h3>
          <p className="mt-1 text-sm trading-muted">Deterministic explanation from the stored trade and factor vector.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="rounded-full px-3 py-1 font-semibold" style={{ background: "var(--copilot-surface-muted)" }}>
            {label(evidence.action)}
          </span>
          <span className="rounded-full px-3 py-1 font-semibold" style={{ background: "var(--copilot-primary)", color: "white" }}>
            {pct(evidence.confidence)}
          </span>
        </div>
      </div>

      <p className="mt-4 text-sm leading-6">{evidence.evidenceText || "No evidence text available."}</p>

      {evidence.factorBreakdown?.length ? (
        <div className="mt-4 grid gap-2">
          {evidence.factorBreakdown.map((line) => (
            <div key={line} className="rounded-md border px-3 py-2 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
              {line}
            </div>
          ))}
        </div>
      ) : null}

      {factorEntries.length ? (
        <div className="mt-4 grid gap-2 md:grid-cols-2">
          {factorEntries.map(([name, value]) => (
            <div key={name} className="rounded-md p-3" style={{ background: "var(--copilot-surface-muted)" }}>
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold">{factorLabel(name)}</span>
                <span>{pct(value)}</span>
              </div>
              <div className="mt-2 h-2 rounded-full" style={{ background: "var(--copilot-border)" }}>
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${Math.max(0, Math.min(1, value)) * 100}%`,
                    background: "var(--copilot-primary)",
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
