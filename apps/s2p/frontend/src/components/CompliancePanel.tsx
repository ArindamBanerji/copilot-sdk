import { useEffect, useState } from "react";
import { fetchS2PCompliance } from "../api";
import type { ComplianceResponse } from "../types";

function percent(value?: number) {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "n/a";
}

export function CompliancePanel() {
  const [data, setData] = useState<ComplianceResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchS2PCompliance().then((response) => {
      if (!cancelled) setData(response);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const flagged = data?.flagged_invoices ?? data?.flaggedInvoices ?? [];

  return (
    <article className="copilot-card p-5">
      <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Compliance</p>
      <h2 className="mt-1 text-xl font-semibold text-slate-950">Tax and regulatory evidence</h2>
      {!data ? (
        <p className="mt-4 text-sm text-slate-500">Loading compliance summary...</p>
      ) : (
        <>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <Metric label="Compliant" value={percent(data.compliant_pct ?? data.compliantPct)} />
            <Metric label="Flagged" value={data.flagged_count ?? data.flaggedCount ?? 0} />
            <Metric label="Total invoices" value={data.total} />
          </div>
          <div className="mt-4 space-y-2">
            {flagged.slice(0, 5).map((invoice) => (
              <div key={invoice.invoice_id ?? invoice.invoiceId} className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm">
                <span className="font-mono text-xs font-semibold text-slate-700">{invoice.invoice_id ?? invoice.invoiceId}</span>
                <span className="ml-3 text-slate-700">{invoice.category}</span>
              </div>
            ))}
          </div>
        </>
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
