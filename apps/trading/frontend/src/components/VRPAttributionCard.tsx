import { useEffect, useState } from "react";
import { fetchVrpAttribution } from "../api";
import type { VrpAttributionResponse } from "../types";
import ProvenanceBadge from "./ProvenanceBadge";

function pct(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? `${Math.round(value * 100)}%` : "-";
}

function num(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(2) : "-";
}

export default function VRPAttributionCard() {
  const [payload, setPayload] = useState<VrpAttributionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchVrpAttribution()
      .then((data) => {
        if (!cancelled) setPayload(data);
      })
      .catch((loadError) => {
        console.debug("vrp attribution unavailable", loadError);
        if (!cancelled) setError("VRP attribution unavailable.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <div className="h-24 animate-pulse rounded-md bg-white/10" />;
  if (error) return <div className="text-sm text-red-500">{error}</div>;
  if (!payload) return null;

  return (
    <section className="copilot-card p-5" data-testid="vrp-attribution-card">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm uppercase tracking-wide trading-muted">V2 volatility diagnostic</p>
          <h2 className="mt-1 text-xl font-semibold">VRP Edge or Insurance</h2>
        </div>
        <ProvenanceBadge source={payload?.provenance || "accumulating"} />
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <div>
          <div className="text-xs uppercase tracking-wide trading-muted">Low-tail capture</div>
          <div className="text-2xl font-semibold">{pct(payload?.dayZero ? null : payload?.lowTailCapturePct)}</div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide trading-muted">High-tail loss ratio</div>
          <div className="text-2xl font-semibold">{num(payload?.dayZero ? null : payload?.highTailLossRatio)}x</div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide trading-muted">VRP decisions</div>
          <div className="text-2xl font-semibold">{payload?.totalVrpDecisions ?? 0}</div>
        </div>
      </div>
      {payload?.dayZero ? (
        <p className="mt-3 text-sm trading-muted">Awaiting {payload.decisionsUntilMeasured ?? 0} more decisions before measured magnitude.</p>
      ) : null}
      <p className="mt-3 text-xs trading-muted">Diagnostic only. Substantiation: {payload?.substantiation || "T-O"}.</p>
    </section>
  );
}
