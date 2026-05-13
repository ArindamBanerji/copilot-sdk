import { useEffect, useState } from "react";
import { fetchS2PSimilar } from "../api";
import type { SimilarResponse } from "../types";

function money(value?: number) {
  if (typeof value !== "number") return "n/a";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

export function SimilarInvoicesPanel({ invoiceId }: { invoiceId?: string }) {
  const [data, setData] = useState<SimilarResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!invoiceId) {
      setData(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    fetchS2PSimilar(invoiceId, 5)
      .then((response) => {
        if (!cancelled) setData(response);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [invoiceId]);

  return (
    <article className="copilot-card p-5">
      <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Similar invoices</p>
      <h2 className="mt-1 text-xl font-semibold text-slate-950">Nearest exceptions by factor shape</h2>
      {loading ? (
        <p className="mt-4 text-sm text-slate-500">Loading similar invoices...</p>
      ) : !data || data.similar.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">No similar invoice evidence available.</p>
      ) : (
        <div className="mt-4 divide-y divide-slate-100">
          {data.similar.map((invoice) => (
            <div key={invoice.invoice_id ?? invoice.invoiceId} className="py-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="font-mono text-xs font-semibold text-slate-700">
                  {invoice.invoice_id ?? invoice.invoiceId}
                </span>
                <span className="rounded-full bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-800">
                  distance {invoice.distance.toFixed(3)}
                </span>
              </div>
              <p className="mt-1 text-sm font-medium text-slate-950">{invoice.supplier ?? "Unknown supplier"}</p>
              <p className="mt-1 text-xs text-slate-500">
                {invoice.category ?? "uncategorized"} · {money(invoice.amount)}
              </p>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}
