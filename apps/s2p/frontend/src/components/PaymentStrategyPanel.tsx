import { useEffect, useState } from "react";

import { getPaymentStrategy } from "../api";
import type { PaymentBehavior, PaymentOptimizationResponse } from "../types";

function formatCurrencyShort(value: number): string {
  if (!Number.isFinite(value) || value <= 0) {
    return "$0";
  }

  if (value >= 1_000_000) {
    const precision = value >= 10_000_000 ? 0 : 1;
    return `$${(value / 1_000_000).toFixed(precision)}M`;
  }

  if (value >= 1_000) {
    return `$${Math.round(value / 1_000)}K`;
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function strategyLabel(strategy: PaymentBehavior["recommended_strategy"]): string {
  if (strategy === "early_pay") return "Early pay";
  if (strategy === "on_time") return "On-time";
  return "Extend";
}

function strategyMark(strategy: PaymentBehavior["recommended_strategy"]): string {
  if (strategy === "early_pay") return "+";
  if (strategy === "on_time") return "=";
  return ">";
}

function strategyTone(strategy: PaymentBehavior["recommended_strategy"]): string {
  if (strategy === "early_pay") return "bg-emerald-100 text-emerald-800";
  if (strategy === "on_time") return "bg-slate-100 text-slate-700";
  return "bg-sky-100 text-sky-800";
}

function riskTone(risk: string): string {
  const normalized = risk.toLowerCase();
  if (normalized === "high") return "text-red-700";
  if (normalized === "medium") return "text-amber-700";
  return "text-emerald-700";
}

export function PaymentStrategyPanel() {
  const [data, setData] = useState<PaymentOptimizationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    setLoading(true);
    setError(false);

    getPaymentStrategy()
      .then((response) => {
        if (cancelled) return;

        if (response) {
          setData(response);
        } else {
          setData(null);
          setError(true);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setData(null);
          setError(true);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const strategies = data?.strategies ?? [];

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">Working capital</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-950">Payment Timing Optimization.</h2>
        </div>
        {data ? (
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
            {data.summary}
          </span>
        ) : null}
      </div>

      {loading ? (
        <div className="mt-4 rounded-lg border border-dashed border-slate-200 p-4 text-sm text-slate-600">
          Loading payment strategy...
        </div>
      ) : error ? (
        <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          Unable to load payment strategy.
        </div>
      ) : strategies.length === 0 ? (
        <div className="mt-4 rounded-lg border border-dashed border-slate-200 p-4 text-sm text-slate-600">
          No payment strategies are available yet.
        </div>
      ) : (
        <>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <SummaryMetric label="Discount opportunity" value={formatCurrencyShort(data?.total_discount_opportunity ?? 0)} />
            <SummaryMetric label="Suppliers analyzed" value={String(data?.suppliers_analyzed ?? strategies.length)} />
            <SummaryMetric label="DPO improvement" value={`+${data?.dpo_improvement_days ?? 0} days`} />
            <SummaryMetric label="Strategy rows" value={String(strategies.length)} />
          </div>

          <div className="mt-4 overflow-hidden rounded-lg border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-3 py-2">Strategy</th>
                  <th className="px-3 py-2">Supplier</th>
                  <th className="px-3 py-2">Terms</th>
                  <th className="px-3 py-2">Discount</th>
                  <th className="px-3 py-2">Confidence</th>
                  <th className="px-3 py-2">Reason</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {strategies.map((strategy) => (
                  <PaymentStrategyRow key={strategy.supplier_id} strategy={strategy} />
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </article>
  );
}

function SummaryMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-xl font-semibold text-slate-950">{value}</p>
    </div>
  );
}

function PaymentStrategyRow({ strategy }: { strategy: PaymentBehavior }) {
  return (
    <tr>
      <td className="px-3 py-3 align-top">
        <span className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-semibold ${strategyTone(strategy.recommended_strategy)}`}>
          <span aria-hidden="true">{strategyMark(strategy.recommended_strategy)}</span>
          {strategyLabel(strategy.recommended_strategy)}
        </span>
      </td>
      <td className="px-3 py-3 align-top font-semibold text-slate-950">{strategy.supplier_name}</td>
      <td className="px-3 py-3 align-top text-slate-600">{strategy.current_terms}</td>
      <td className="px-3 py-3 align-top text-slate-600">{formatCurrencyShort(strategy.discount_opportunity)}</td>
      <td className="px-3 py-3 align-top text-slate-600">{formatPercent(strategy.confidence)}</td>
      <td className="px-3 py-3 align-top text-slate-600">
        <p>{strategy.reason}</p>
        <p className="mt-1 text-xs text-slate-500">
          OTIF correlation {strategy.payment_otif_correlation.toFixed(2)} - delayed risk{" "}
          <span className={riskTone(strategy.risk_if_delayed)}>{strategy.risk_if_delayed}</span>
        </p>
      </td>
    </tr>
  );
}
