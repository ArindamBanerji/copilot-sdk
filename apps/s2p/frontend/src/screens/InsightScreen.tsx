import { useEffect, useMemo, useState } from "react";
import { fetchPreviewQueue } from "../api";
import { CentroidExplorerPanel } from "../components/CentroidExplorerPanel";
import { CrossGraphInsightCard } from "../components/CrossGraphInsightCard";
import { DiscoveryExtendedPanel } from "../components/DiscoveryExtendedPanel";
import { EarlyWarningPanel } from "../components/EarlyWarningPanel";
import { FactorFingerprintPanel } from "../components/FactorFingerprintPanel";
import { LeakageDetectionPanel } from "../components/LeakageDetectionPanel";
import { ProcessSignalsPanel } from "../components/ProcessSignalsPanel";
import { SimilarInvoicesPanel } from "../components/SimilarInvoicesPanel";
import type { InvoiceException, PreviewQueueResponse } from "../types";

function invoiceId(invoice?: InvoiceException | null): string {
  return invoice?.invoice_id ?? invoice?.invoiceId ?? invoice?.event_id ?? invoice?.eventId ?? "";
}

function supplierId(invoice?: InvoiceException | null): string {
  return invoice?.supplier_id ?? invoice?.supplierId ?? "";
}

export function InsightScreen() {
  const [queue, setQueue] = useState<PreviewQueueResponse | null>(null);
  const [selectedId, setSelectedId] = useState("");

  useEffect(() => {
    let cancelled = false;
    fetchPreviewQueue().then((data) => {
      if (cancelled) return;
      setQueue(data);
      const first = data.exceptions?.[0];
      if (first) setSelectedId(invoiceId(first));
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const invoices = queue?.exceptions ?? [];
  const selected = useMemo(
    () => invoices.find((invoice) => invoiceId(invoice) === selectedId) ?? invoices[0] ?? null,
    [invoices, selectedId],
  );

  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Invoice intelligence</p>
        <h1 className="mt-1 text-3xl font-semibold text-slate-950">Insight</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">
          Explain why an invoice was flagged by combining factor fingerprint, similar exceptions,
          process signals, and supplier-process correlations.
        </p>
      </div>

      <article className="copilot-card p-5">
        <label className="text-sm font-medium text-slate-700">
          Invoice
          <select
            value={invoiceId(selected)}
            onChange={(event) => setSelectedId(event.target.value)}
            className="mt-2 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm md:max-w-md"
          >
            {invoices.map((invoice) => (
              <option key={invoiceId(invoice)} value={invoiceId(invoice)}>
                {invoiceId(invoice)} · {invoice.supplier_name ?? invoice.supplierName ?? invoice.supplier ?? "Supplier"}
              </option>
            ))}
          </select>
        </label>
      </article>

      <div className="grid gap-4 xl:grid-cols-2">
        <FactorFingerprintPanel invoiceId={invoiceId(selected)} />
        <SimilarInvoicesPanel invoiceId={invoiceId(selected)} />
      </div>
      <CrossGraphInsightCard />
      <EarlyWarningPanel />
      <LeakageDetectionPanel />
      <ProcessSignalsPanel supplierId={supplierId(selected)} />
      <CentroidExplorerPanel />
      <DiscoveryExtendedPanel />
    </section>
  );
}
