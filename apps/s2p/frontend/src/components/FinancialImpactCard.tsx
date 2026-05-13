import { useEffect, useState } from "react";
import { fetchImpact } from "../api";

type BreakdownItem = {
  amount?: number;
  pct?: number;
};

type ImpactResponse = {
  period?: string;
  total_savings?: number;
  total_savings_usd?: number;
  annual_target?: number;
  annual_target_usd?: number;
  breakdown?: Record<string, BreakdownItem>;
};

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
  const [impact, setImpact] = useState<ImpactResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchImpact("annual")
      .then((response) => {
        if (!cancelled) setImpact((response as ImpactResponse | null) ?? null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const breakdown = impact?.breakdown ?? {};
  const total = impact?.total_savings_usd ?? impact?.total_savings;

  return (
    <article className="copilot-card p-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Financial impact</p>
      <div className="mt-2 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-950">PVG savings</h2>
          <p className="mt-1 text-sm text-slate-500">Annual leakage, cycle-time, and auto-approve opportunity.</p>
        </div>
        <p className="text-2xl font-semibold text-slate-950">
          {loading ? "Loading..." : formatCurrency(total)}
        </p>
      </div>

      {loading ? null : impact ? (
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {["leakage_prevented", "cycle_time_saved", "auto_approve_efficiency"].map((name) => {
            const item = breakdown[name] ?? {};
            return (
              <div key={name} className="rounded-md border border-slate-200 bg-white p-3">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label(name)}</p>
                <p className="mt-2 text-lg font-semibold text-slate-950">{formatCurrency(item.amount)}</p>
                <p className="mt-1 text-xs text-slate-500">{typeof item.pct === "number" ? `${item.pct}%` : "n/a"} of target</p>
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
