import { useEffect, useState } from "react";
import { fetchFinancialImpact } from "../api";
import type { FinancialImpactBucket, FinancialImpactSummaryResponse } from "../types";

function formatCurrency(value?: number): string {
  if (typeof value !== "number") return "n/a";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function label(value: string): string {
  return value.replace(/_/g, " ");
}

export function FinancialImpactCard() {
  const [impact, setImpact] = useState<FinancialImpactSummaryResponse | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!expanded) return;
    let cancelled = false;
    setLoading(true);
    fetchFinancialImpact()
      .then((response) => {
        if (!cancelled) setImpact(response ?? null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [expanded]);

  const breakdown = impact?.by_category ?? {};
  const total = impact?.net_savings ?? impact?.total_recovered;
  const topCategories: Array<[string, FinancialImpactBucket]> = Object.entries(breakdown)
    .sort(([, a], [, b]) => (b.recovered ?? 0) - (a.recovered ?? 0))
    .slice(0, 3);
  const cards: Array<[string, FinancialImpactBucket]> = topCategories.length
    ? topCategories
    : [["verified_decisions", {
      count: impact?.verified_decisions ?? 0,
      amount: 0,
      at_risk: impact?.total_at_risk ?? 0,
      recovered: impact?.total_recovered ?? 0
    }]];

  return (
    <article className="copilot-card p-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Financial impact</p>
      <div className="mt-2 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-950">Recovered impact</h2>
          <p className="mt-1 text-sm text-slate-500">Receipt-backed recovery and at-risk exposure from verified outcomes.</p>
        </div>
        <p className="text-2xl font-semibold text-slate-950">
          {expanded && loading ? "Loading..." : expanded ? formatCurrency(total) : "On demand"}
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
      ) : loading ? null : impact ? (
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {cards.map(([name, item]) => {
            return (
              <div key={name} className="rounded-md border border-slate-200 bg-white p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label(name)}</p>
                <p className="mt-2 text-lg font-semibold text-slate-950">{formatCurrency(item.recovered)}</p>
                <p className="mt-1 text-xs text-slate-500">{item.count ?? 0} verified decisions</p>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-500">Financial impact data is unavailable.</p>
      )}
    </article>
  );
}
