import { useEffect, useState } from "react";
import { fetchConservation } from "../api";
import type { ConservationStatus } from "../types";

function pct(value?: number): string {
  if (typeof value !== "number") return "n/a";
  return `${Math.round(value * 100)}%`;
}

export function S2PConservationProjection() {
  const [status, setStatus] = useState<ConservationStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchConservation()
      .then((data) => {
        if (!cancelled) setStatus(data);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const verified = status?.verified_decisions ?? status?.verifiedDecisions ?? status?.verified_count ?? status?.verifiedCount;
  const penalty = status?.penalty_ratio ?? status?.penaltyRatio ?? 5;
  const theta = status?.theta_min ?? status?.thetaMin;
  const q = status?.q ?? status?.accuracy;
  const state = status?.status ?? (status?.passed ? "GREEN" : undefined);

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-slate-950">Conservation Projection</h2>
        <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-amber-800">
          penalty {penalty}:1
        </span>
      </div>
      {loading ? (
        <p className="mt-3 text-sm text-slate-500">Loading conservation status...</p>
      ) : status ? (
        <div className="mt-4 grid gap-3 sm:grid-cols-4">
          <Metric label="Status" value={state ?? "n/a"} />
          <Metric label="q / accuracy" value={pct(q)} />
          <Metric label="Verified" value={verified ?? 0} />
          <Metric label="theta min" value={typeof theta === "number" ? theta.toFixed(3) : "n/a"} />
        </div>
      ) : (
        <p className="mt-3 text-sm text-slate-500">Conservation status is unavailable.</p>
      )}
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-lg font-semibold text-slate-950">{value}</p>
    </div>
  );
}
