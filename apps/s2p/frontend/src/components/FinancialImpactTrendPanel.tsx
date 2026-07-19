import { useEffect, useState } from "react";
import { fetchFinancialImpactTrend } from "../api";
import type { FinancialImpactTrendResponse } from "../types";

function formatCurrency(value?: number): string {
  if (typeof value !== "number") return "n/a";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export function FinancialImpactTrendPanel() {
  const [trend, setTrend] = useState<FinancialImpactTrendResponse | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!expanded) return;
    let cancelled = false;
    setLoading(true);
    fetchFinancialImpactTrend()
      .then((response) => {
        if (!cancelled) setTrend(response ?? null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [expanded]);

  const points = trend?.points ?? [];

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Financial impact</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-950">Weekly recovery trend</h2>
          <p className="mt-1 text-sm text-slate-500">Receipt-backed recovered value across the current analysis window.</p>
        </div>
        <p className="text-sm font-semibold text-slate-700">
          {expanded && loading ? "Loading..." : expanded ? `${points.length}/${trend?.window_weeks ?? 12} weeks` : "On demand"}
        </p>
      </div>

      {!expanded ? (
        <button
          type="button"
          onClick={() => setExpanded(true)}
          className="mt-4 text-sm font-semibold text-amber-700 hover:text-amber-800"
        >
          View details
        </button>
      ) : loading ? null : trend && points.length ? (
        <div className="mt-4 space-y-2">
          {points.slice(-6).map((point) => (
            <div key={point.week} className="grid grid-cols-[80px_1fr_auto] items-center gap-3">
              <span className="font-mono text-xs text-slate-500">{point.week}</span>
              <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-emerald-500"
                  style={{
                    width: `${Math.min(
                      100,
                      Math.max(4, (point.total_recovered / Math.max(trend.totals.total_recovered, 1)) * 100)
                    )}%`,
                  }}
                />
              </div>
              <span className="text-sm font-semibold text-slate-900">{formatCurrency(point.total_recovered)}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-500">No dated financial impact data is available yet.</p>
      )}
    </article>
  );
}
