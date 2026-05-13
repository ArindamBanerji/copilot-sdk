import { useEffect, useState } from "react";
import { fetchS2PSummary } from "../api";
import type { PerformanceSummaryResponse } from "../types";

function percent(value?: number) {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "n/a";
}

function money(value?: number) {
  if (typeof value !== "number") return "n/a";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

export function OperationalSummary() {
  const [data, setData] = useState<PerformanceSummaryResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchS2PSummary().then((response) => {
      if (!cancelled) setData(response);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <article className="copilot-card p-5">
      <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Operational summary</p>
      <h2 className="mt-1 text-xl font-semibold text-slate-950">Learning, approvals, savings</h2>
      {!data ? (
        <p className="mt-4 text-sm text-slate-500">Loading operational summary...</p>
      ) : (
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <Metric label="Scored" value={data.total_scored ?? data.totalScored ?? 0} />
          <Metric label="Accuracy" value={percent(data.accuracy)} />
          <Metric label="Auto approve" value={percent(data.auto_approve_rate ?? data.autoApproveRate)} />
          <Metric label="Savings estimate" value={money(data.savings_estimate_usd ?? data.savingsEstimateUsd)} />
          <Metric label="Annual target" value={money(data.annual_target_usd ?? data.annualTargetUsd)} />
          <Metric label="Penalty ratio" value={`${data.penalty_ratio ?? data.penaltyRatio ?? 5}:1`} />
        </div>
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
