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
          <p className="text-sm uppercase tracking-wide trading-muted">V1 volatility diagnostic</p>
          <h2 className="mt-1 text-xl font-semibold">Clustering-Adjusted Sharpe</h2>
        </div>
        <ProvenanceBadge source={payload?.provenance || "accumulating"} />
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <div>
          <div className="text-xs uppercase tracking-wide trading-muted">Naive</div>
          <div className="text-2xl font-semibold">{valueText(payload?.dayZero ? null : payload?.naiveSharpe)}</div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide trading-muted">Cluster adjusted</div>
          <div className="text-2xl font-semibold">{valueText(payload?.dayZero ? null : payload?.adjustedSharpe)}</div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide trading-muted">Inflation</div>
          <div className="text-2xl font-semibold">{valueText(payload?.dayZero ? null : payload?.inflation)}x</div>
        </div>
      </div>
      <DayZero count={payload?.decisionsUntilMeasured} />
      <p className="mt-3 text-xs trading-muted">Diagnostic only. Substantiation: {payload?.substantiation || "T-O"}.</p>
    </section>
  );
}
