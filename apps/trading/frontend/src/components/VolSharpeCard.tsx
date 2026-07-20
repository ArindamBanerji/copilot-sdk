import { useEffect, useState } from "react";
import { fetchVolSharpe } from "../api";
import type { VolSharpeResponse } from "../types";
import ProvenanceBadge from "./ProvenanceBadge";

function valueText(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(2) : "-";
}

function DayZero({ count }: { count?: number }) {
  if (!count || count <= 0) return null;
  return <p className="mt-3 text-sm trading-muted">Awaiting {count} more decisions before measured magnitude.</p>;
}

export default function VolSharpeCard() {
  const [payload, setPayload] = useState<VolSharpeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchVolSharpe()
      .then((data) => {
        if (!cancelled) setPayload(data);
      })
      .catch((loadError) => {
        console.debug("vol sharpe unavailable", loadError);
        if (!cancelled) setError("Volatility Sharpe unavailable.");
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
    <section className="copilot-card p-5" data-testid="vol-sharpe-card">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm uppercase tracking-wide trading-muted">V1 quality diagnostic</p>
          <h2 className="mt-1 text-xl font-semibold">Risk-Adjusted Decision Quality</h2>
        </div>
        <ProvenanceBadge source={payload?.provenance || "accumulating"} />
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <div>
          <div className="text-xs uppercase tracking-wide trading-muted">Raw quality score</div>
          <div className="text-2xl font-semibold">{valueText(payload?.dayZero ? null : payload?.naiveQualityScore)}</div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide trading-muted">Bootstrap-adjusted quality</div>
          <div className="text-2xl font-semibold">{valueText(payload?.dayZero ? null : payload?.qualityAdjustedScore)}</div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide trading-muted">Bootstrap inflation</div>
          <div className="text-2xl font-semibold">{valueText(payload?.dayZero ? null : payload?.inflation)}x</div>
        </div>
      </div>
      <div className="mt-4 overflow-x-auto">
        <div className="text-xs uppercase tracking-wide trading-muted">By market condition</div>
        <p className="mt-1 text-sm trading-muted">Quality-adjusted decision performance grouped by market regime. Higher means more consistent quality.</p>
        {payload.clusters?.length ? (
          <table className="mt-2 w-full text-left text-sm" data-testid="vol-sharpe-clusters">
            <thead className="trading-muted">
              <tr><th className="pb-1">Market condition</th><th className="pb-1">Decisions</th><th className="pb-1">Quality score</th><th className="pb-1">State</th></tr>
            </thead>
            <tbody>
              {payload.clusters.map((cluster) => (
                <tr key={cluster.clusterId}>
                  <td className="py-1">{cluster.clusterId.replace("regime:", "")}</td>
                  <td className="py-1">{cluster.nDecisions}</td>
                  <td className="py-1">{valueText(cluster.riskAdjustedQuality)}</td>
                  <td className="py-1 capitalize">{cluster.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <p className="mt-2 text-sm trading-muted">Accumulating decisions by market condition.</p>}
      </div>
      <DayZero count={payload?.decisionsUntilMeasured} />
      <p className="mt-3 text-xs trading-muted">Diagnostic only. Substantiation: {payload?.substantiation || "T-O"}.</p>
    </section>
  );
}
