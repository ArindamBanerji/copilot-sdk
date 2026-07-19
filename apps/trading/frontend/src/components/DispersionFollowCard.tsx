import { useEffect, useState } from "react";
import { fetchDispersionFollow } from "../api";
import type { DispersionFollowResponse } from "../types";
import ProvenanceBadge from "./ProvenanceBadge";

function money(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? `$${Math.round(value).toLocaleString()}` : "-";
}

function pct(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? `${Math.round(value * 100)}%` : "-";
}

export default function DispersionFollowCard() {
  const [payload, setPayload] = useState<DispersionFollowResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchDispersionFollow()
      .then((data) => {
        if (!cancelled) setPayload(data);
      })
      .catch((loadError) => {
        console.debug("dispersion follow unavailable", loadError);
        if (!cancelled) setError("Dispersion follow-rate unavailable.");
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
    <section className="copilot-card p-5" data-testid="dispersion-follow-card">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm uppercase tracking-wide trading-muted">V6 volatility diagnostic</p>
          <h2 className="mt-1 text-xl font-semibold">Dispersion Follow-Rate</h2>
        </div>
        <ProvenanceBadge source={payload?.provenance || "accumulating"} />
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-4">
        <div><div className="text-xs uppercase tracking-wide trading-muted">Signals</div><div className="text-2xl font-semibold">{payload?.signalsFired ?? 0}</div></div>
        <div><div className="text-xs uppercase tracking-wide trading-muted">Followed</div><div className="text-2xl font-semibold">{payload?.followed ?? 0}</div></div>
        <div><div className="text-xs uppercase tracking-wide trading-muted">Follow-rate</div><div className="text-2xl font-semibold">{pct(payload?.dayZero ? null : payload?.followRate)}</div></div>
        <div><div className="text-xs uppercase tracking-wide trading-muted">Skipped value</div><div className="text-2xl font-semibold">{money(payload?.dayZero ? null : payload?.skippedValue)}</div></div>
      </div>
      {payload?.dayZero ? (
        <p className="mt-3 text-sm trading-muted">Awaiting {payload.decisionsUntilMeasured ?? 0} more decisions before measured magnitude.</p>
      ) : null}
      <p className="mt-3 text-xs trading-muted">Diagnostic only. Substantiation: {payload?.substantiation || "T-O"}.</p>
    </section>
  );
}
