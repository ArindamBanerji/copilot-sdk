import { useEffect, useState } from "react";
import { fetchSituationSharpeAdjustment } from "../api";
import type { SituationSharpeResponse } from "../types";
import ProvenanceBadge from "./ProvenanceBadge";

function score(value: number | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(1) : "-";
}

export default function VolatilityPanel() {
  const [payload, setPayload] = useState<SituationSharpeResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchSituationSharpeAdjustment()
      .then((next) => {
        if (!cancelled) setPayload(next);
      })
      .catch(() => {
        if (!cancelled) setPayload(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section data-testid="volatility-panel" className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm uppercase tracking-wide trading-muted">TRD-V1 / V2</p>
          <h2 className="mt-1 text-xl font-semibold">Volatility reality check</h2>
        </div>
        <ProvenanceBadge source={payload?.provenance || "illustrative"} />
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="text-xs uppercase tracking-wide trading-muted">Calm-regime Sharpe</div>
          <div data-testid="volatility-raw-sharpe" className="mt-1 text-2xl font-semibold">{loading ? "-" : score(payload?.rawSharpe)}</div>
        </div>
        <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="text-xs uppercase tracking-wide trading-muted">Cluster-adjusted Sharpe</div>
          <div data-testid="volatility-adjusted-sharpe" className="mt-1 text-2xl font-semibold">{loading ? "-" : score(payload?.clusteringAdjustedSharpe)}</div>
        </div>
        <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="text-xs uppercase tracking-wide trading-muted">VRP in low-tail windows</div>
          <div data-testid="volatility-vrp-capture" className="mt-1 text-2xl font-semibold">{loading ? "-" : `${payload?.vrpCaptureLowTailPct ?? "-"}%`}</div>
        </div>
      </div>
      <p className="mt-4 text-sm trading-muted">{payload?.message || "Loading clustering adjustment..."}</p>
      <p className="mt-2 text-sm trading-muted">{payload?.vrpMessage || "VRP attribution is illustrative until volatility observations are measured."}</p>
      <p className="mt-3 text-xs trading-muted">Diagnostic only. Substantiation: {payload?.substantiation || "T-O"}.</p>
    </section>
  );
}
