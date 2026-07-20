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

function classificationText(value: VrpAttributionResponse["classification"]): string {
  if (value === "edge") return "Edge";
  if (value === "insurance") return "Insurance";
  if (value === "neutral") return "Neutral";
  return "Accumulating";
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
        <ProvenanceBadge source={payload?.provenance || payload?.status || "instrument_validated"} />
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <div>
          <div className="text-xs uppercase tracking-wide trading-muted">Average IV-RV spread</div>
          <div className="text-2xl font-semibold">{num(payload?.vrpSpreadMean)}</div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide trading-muted">Current IV-RV spread</div>
          <div className="text-2xl font-semibold">{num(payload?.vrpSpreadCurrent)}</div>
        </div>
        <div data-testid="vrp-classification">
          <div className="text-xs uppercase tracking-wide trading-muted">Reading</div>
          <div className="text-2xl font-semibold">{classificationText(payload?.classification)}</div>
        </div>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <div><div className="text-xs uppercase tracking-wide trading-muted">Average implied volatility</div><div className="text-lg font-semibold">{num(payload?.ivMean)}</div></div>
        <div><div className="text-xs uppercase tracking-wide trading-muted">Average realized volatility</div><div className="text-lg font-semibold">{num(payload?.rvMean)}</div></div>
        <div><div className="text-xs uppercase tracking-wide trading-muted">Eligible observations</div><div className="text-lg font-semibold">{payload?.nEligible ?? 0}</div></div>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <div>
          <div className="text-xs uppercase tracking-wide trading-muted">Low-tail capture</div>
          <div className="text-2xl font-semibold">{pct(payload?.tailAttribution?.dayZero ? null : payload?.tailAttribution?.lowTailCapturePct)}</div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide trading-muted">High-tail loss ratio</div>
          <div className="text-2xl font-semibold">{num(payload?.tailAttribution?.dayZero ? null : payload?.tailAttribution?.highTailLossRatio)}x</div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide trading-muted">VRP decisions</div>
          <div className="text-2xl font-semibold">{payload?.tailAttribution?.totalVrpDecisions ?? 0}</div>
        </div>
      </div>
      {payload?.tailAttribution?.dayZero ? (
        <p className="mt-3 text-sm trading-muted">Awaiting {payload.tailAttribution.decisionsUntilMeasured ?? 0} more tail decisions before measured magnitude.</p>
      ) : null}
      {payload?.status === "instrument_validated" ? (
        <p className="mt-3 text-sm trading-muted">Insufficient volatility data. Add implied and realized volatility when logging a trade.</p>
      ) : null}
      <p className="mt-3 text-xs trading-muted">Diagnostic only. Substantiation: {payload?.substantiation || "T-O"}.</p>
    </section>
  );
}
