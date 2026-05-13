import { useEffect, useState } from "react";
import { fetchLeakage } from "../api";

type LeakageInvoice = {
  invoice_id?: string;
  supplier_id?: string;
  supplier_name?: string;
  amount?: number;
  amount_variance_ratio?: number;
  variance_ratio?: number;
  commodity_index_correlation?: number;
  commodity_correlation?: number;
  at_risk_amount?: number;
  at_risk_usd?: number;
};

type LeakageResponse = {
  flagged_invoices?: LeakageInvoice[];
  items?: LeakageInvoice[];
  total_at_risk?: number;
  estimated_leakage_usd?: number;
  count?: number;
  flagged_count?: number;
  rule?: string;
};

function ensureArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

function formatCurrency(value?: number): string {
  if (typeof value !== "number") return "n/a";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPct(value?: number): string {
  if (typeof value !== "number") return "n/a";
  return `${Math.round(value * 100)}%`;
}

export function LeakageDetectionPanel() {
  const [data, setData] = useState<LeakageResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchLeakage()
      .then((response) => {
        if (!cancelled) setData((response as LeakageResponse | null) ?? null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const flagged = ensureArray<LeakageInvoice>(data?.flagged_invoices ?? data?.items);
  const total = data?.total_at_risk ?? data?.estimated_leakage_usd;

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Leakage detection</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-950">PVG at-risk invoices</h2>
        </div>
        <span className="rounded bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-800">
          {loading ? "Loading" : `${data?.flagged_count ?? data?.count ?? flagged.length} flagged`}
        </span>
      </div>

      {loading ? (
        <p className="mt-4 text-sm text-slate-500">Loading leakage signals...</p>
      ) : !data ? (
        <p className="mt-4 text-sm text-slate-500">Leakage data is unavailable.</p>
      ) : flagged.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">No invoices currently meet the backend leakage rule.</p>
      ) : (
        <>
          <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 p-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-800">Total at risk</p>
            <p className="mt-1 text-2xl font-semibold text-slate-950">{formatCurrency(total)}</p>
          </div>
          <div className="mt-4 divide-y divide-slate-100">
            {flagged.slice(0, 6).map((invoice, index) => {
              const variance = invoice.amount_variance_ratio ?? invoice.variance_ratio;
              const correlation = invoice.commodity_index_correlation ?? invoice.commodity_correlation;
              return (
                <div key={invoice.invoice_id ?? `leakage-${index}`} className="py-3">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <span className="font-mono text-xs font-semibold text-slate-700">{invoice.invoice_id ?? "invoice"}</span>
                    <span className="text-sm font-semibold text-slate-950">{formatCurrency(invoice.at_risk_amount ?? invoice.at_risk_usd)}</span>
                  </div>
                  <p className="mt-1 text-xs text-slate-600">
                    {invoice.supplier_name ?? invoice.supplier_id ?? "Supplier"} · amount {formatCurrency(invoice.amount)} · variance {formatPct(variance)} · commodity correlation {formatPct(correlation)}
                  </p>
                </div>
              );
            })}
          </div>
        </>
      )}
    </article>
  );
}
