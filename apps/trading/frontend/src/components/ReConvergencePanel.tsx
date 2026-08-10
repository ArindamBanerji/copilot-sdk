import { useEffect, useMemo, useState } from "react";
import { fetchCentroidHistory, fetchSituationRegime } from "../api";
import type { CentroidCheckpoint, SelfCentroidHistoryResponse, SituationRegimeResponse } from "../types";

const REGIMES = ["trending", "ranging", "volatile"] as const;
type Regime = (typeof REGIMES)[number];

/**
 * TRD-S7: Re-Convergence Moment — regime-indexed judgment memory.
 *
 * ARCH LABEL: This is an experimental capability. Results are from
 * controlled experiments, not production measurements.
 *
 * The curves remain illustrative until EXP-REGIME supplies measured
 * cold-start and regime-indexed convergence observations.
 */
export default function ReConvergencePanel() {
  const [history, setHistory] = useState<SelfCentroidHistoryResponse | null>(null);
  const [situation, setSituation] = useState<SituationRegimeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchCentroidHistory(100), fetchSituationRegime()])
      .then(([nextHistory, nextSituation]) => {
        if (cancelled) return;
        setHistory(nextHistory);
        setSituation(nextSituation);
      })
      .catch((error) => {
        console.debug("re-convergence experiment data unavailable", error);
        if (!cancelled) setUnavailable(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const checkpoints = Array.isArray(history?.checkpoints) ? history.checkpoints : [];
  const currentRegime = canonicalRegime(situation?.regime) || latestRegime(checkpoints) || "ranging";
  const depth = useMemo(() => regimeDepth(checkpoints), [checkpoints]);
  const gamma = findGamma(checkpoints);

  return (
    <section data-testid="reconvergence-panel" className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: "var(--copilot-primary)" }}>
              TRD-S7 / ARCH
            </p>
            <span className="rounded-full border border-fuchsia-300/50 bg-fuchsia-500/15 px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-fuchsia-100">
              Experimental — labeled roadmap
            </span>
          </div>
          <h2 className="mt-2 text-xl font-semibold">Re-convergence</h2>
          <p className="mt-1 max-w-2xl text-sm trading-muted">
            Cold-start versus regime-indexed convergence after a regime break. This is an experimental capability; results are not production measurements.
          </p>
        </div>
        <span className={`rounded-full border px-3 py-1 text-sm font-semibold ${regimeClass(currentRegime)}`}>
          {loading ? "Loading regime…" : currentRegime}
        </span>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="text-xs uppercase tracking-wide trading-muted">Current regime</div>
          <div data-testid="reconvergence-regime" className="mt-1 text-lg font-semibold capitalize">{currentRegime}</div>
        </div>
        <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="text-xs uppercase tracking-wide trading-muted">Checkpoint depth</div>
          <div data-testid="reconvergence-depth" className="mt-1 text-lg font-semibold">
            {depth[currentRegime]} checkpoints in '{currentRegime}'
          </div>
        </div>
        <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="text-xs uppercase tracking-wide trading-muted">γ_regime</div>
          <div data-testid="reconvergence-gamma" className="mt-1 text-lg font-semibold">
            {gamma ? `${gamma.value.toFixed(2)}${gamma.confidence == null ? "" : ` (${Math.round(gamma.confidence * 100)}% confidence)`}` : "Experiment pending"}
          </div>
        </div>
      </div>

      <div className="mt-5 rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h3 className="font-semibold">Convergence curve overlay</h3>
            <p className="text-xs trading-muted">Illustrative ARCH curves — experiment pending</p>
          </div>
          <div className="flex gap-3 text-xs trading-muted">
            <span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-slate-300" />Cold-start</span>
            <span><i className="mr-1 inline-block h-2 w-2 rounded-full bg-fuchsia-300" />Regime-indexed</span>
          </div>
        </div>
        <svg viewBox="0 0 520 150" role="img" aria-label="Illustrative cold-start and regime-indexed convergence curves" className="h-40 w-full">
          <line x1="36" y1="16" x2="36" y2="126" stroke="currentColor" opacity="0.2" />
          <line x1="36" y1="126" x2="500" y2="126" stroke="currentColor" opacity="0.2" />
          <path d="M36 112 C120 108 155 95 210 80 S330 48 500 28" fill="none" stroke="#cbd5e1" strokeWidth="3" strokeDasharray="7 5" />
          <path d="M36 112 C105 94 140 68 190 52 S310 32 500 24" fill="none" stroke="#f0abfc" strokeWidth="3" />
          <text x="40" y="143" className="fill-current text-[10px]" opacity="0.6">learning steps</text>
          <text x="40" y="12" className="fill-current text-[10px]" opacity="0.6">convergence</text>
        </svg>
        {unavailable ? <p className="text-xs trading-muted">Experiment inputs unavailable; showing the labeled placeholder.</p> : null}
      </div>
    </section>
  );
}

function canonicalRegime(value: unknown): Regime | null {
  const normalized = String(value || "").toLowerCase();
  return REGIMES.includes(normalized as Regime) ? normalized as Regime : null;
}

function latestRegime(checkpoints: CentroidCheckpoint[]): Regime | null {
  for (let index = checkpoints.length - 1; index >= 0; index -= 1) {
    const checkpoint = checkpoints[index];
    const tag = canonicalRegime(checkpoint.regime_tag) || canonicalRegime(checkpoint.metadata?.regime_tag);
    if (tag) return tag;
  }
  return null;
}

function regimeDepth(checkpoints: CentroidCheckpoint[]): Record<Regime, number> {
  return REGIMES.reduce((counts, regime) => {
    counts[regime] = checkpoints.filter((checkpoint) => (
      canonicalRegime(checkpoint.regime_tag) === regime || canonicalRegime(checkpoint.metadata?.regime_tag) === regime
    )).length;
    return counts;
  }, { trending: 0, ranging: 0, volatile: 0 });
}

function findGamma(checkpoints: CentroidCheckpoint[]): { value: number; confidence?: number } | null {
  for (const checkpoint of checkpoints) {
    const payload = checkpoint.metadata || checkpoint;
    const value = Number(payload.gamma_regime ?? payload.gammaRegime);
    if (Number.isFinite(value)) {
      const confidenceValue = Number(payload.gamma_confidence ?? payload.gammaConfidence);
      return { value, confidence: Number.isFinite(confidenceValue) ? confidenceValue : undefined };
    }
  }
  return null;
}

function regimeClass(regime: Regime): string {
  if (regime === "trending") return "border-emerald-300/50 bg-emerald-500/15 text-emerald-100";
  if (regime === "volatile") return "border-red-300/50 bg-red-500/15 text-red-100";
  return "border-amber-300/50 bg-amber-500/15 text-amber-100";
}
