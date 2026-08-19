import { useEffect, useState } from "react";
import {
  fetchVolatilityDispersion,
  fetchVolatilityRichCheap,
  fetchVolatilitySharpe,
  fetchVolatilityTailBets,
  fetchVolatilityVrp,
} from "../api";
import type { VolatilitySurfaceResponse } from "../types";

function numberText(value: unknown, suffix = ""): string {
  return typeof value === "number" && Number.isFinite(value) ? `${value.toFixed(2)}${suffix}` : "-";
}

function evidenceText(payload: VolatilitySurfaceResponse | null): string {
  return payload?.evidence_tier || "T-O";
}

export default function VolatilityScenarioPanel() {
  const [surfaces, setSurfaces] = useState<VolatilitySurfaceResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      fetchVolatilitySharpe(),
      fetchVolatilityVrp(),
      fetchVolatilityRichCheap(),
      fetchVolatilityDispersion(),
      fetchVolatilityTailBets(),
    ])
      .then((next) => {
        if (!cancelled) setSurfaces(next);
      })
      .catch((error) => console.debug("volatility scenario surfaces unavailable", error))
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const [sharpe, vrp, richCheap, dispersion, tail] = surfaces;
  return (
    <section data-testid="volatility-scenario-panel" className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm uppercase tracking-wide trading-muted">TRD-V1 / V2 / V5 / V6 / V7</p>
          <h2 className="mt-1 text-xl font-semibold">Volatility scenario surfaces</h2>
        </div>
        <span data-testid="volatility-scenario-evidence" className="rounded-full border px-2 py-1 text-xs trading-muted">
          Evidence: {evidenceText(sharpe || null)}
        </span>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <div data-testid="volatility-surface-sharpe" className="rounded-md border p-3">
          <div className="text-xs trading-muted">Cluster-adjusted Sharpe</div>
          <div className="mt-1 text-xl font-semibold">{loading ? "-" : numberText(sharpe?.quality_adjusted_score)}</div>
        </div>
        <div data-testid="volatility-surface-vrp" className="rounded-md border p-3">
          <div className="text-xs trading-muted">VRP / tail dependence</div>
          <div className="mt-1 text-xl font-semibold">{loading ? "-" : numberText(vrp?.vrp_spread_mean)}</div>
        </div>
        <div data-testid="volatility-surface-rich-cheap" className="rounded-md border p-3">
          <div className="text-xs trading-muted">Regime rich / cheap</div>
          <div className="mt-1 text-xl font-semibold">{loading ? "-" : richCheap?.band || "-"}</div>
        </div>
        <div data-testid="volatility-surface-dispersion" className="rounded-md border p-3">
          <div className="text-xs trading-muted">Dispersion follow-rate</div>
          <div className="mt-1 text-xl font-semibold">{loading ? "-" : numberText(dispersion?.follow_rate, "")}</div>
        </div>
        <div data-testid="volatility-surface-tail" className="rounded-md border p-3">
          <div className="text-xs trading-muted">Effective bets in tail</div>
          <div className="mt-1 text-xl font-semibold">{loading ? "-" : numberText(tail?.effective_bets)}</div>
        </div>
      </div>
      <p data-testid="volatility-surface-observation" className="mt-4 text-sm trading-muted">
        {sharpe?.observation || "Observation: volatility surfaces are loading."} No forward action is inferred.
      </p>
    </section>
  );
}
