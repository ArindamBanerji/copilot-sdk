import { useEffect, useMemo, useState } from "react";
import { fetchPreviewQueue } from "../api";
import { AuditTrailPanel } from "../components/AuditTrailPanel";
import { AuditExportPanel } from "../components/AuditExportPanel";
import { CompliancePanel } from "../components/CompliancePanel";
import { ComplianceScreeningPanel } from "../components/ComplianceScreeningPanel";
import CohortStatusPanel from "../components/CohortStatusPanel";
import { DiscoveryPanel } from "../components/DiscoveryPanel";
import { DisruptionRecoveryPanel } from "../components/DisruptionRecoveryPanel";
import { EvolutionPanel } from "../components/EvolutionPanel";
import FactorInsightPanel from "../components/FactorInsightPanel";
import { ReceiptChainPanel } from "../components/ReceiptChainPanel";
import { RuleLifecyclePanel } from "../components/RuleLifecyclePanel";
import type { InvoiceException, PreviewQueueResponse } from "../types";

function invoiceId(invoice?: InvoiceException | null): string {
  return invoice?.invoice_id ?? invoice?.invoiceId ?? invoice?.event_id ?? invoice?.eventId ?? "";
}

export function EvidenceScreen() {
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
        <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Governance evidence</p>
        <h1 className="mt-1 text-3xl font-semibold text-slate-950">Evidence</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">
          Review the decision audit trail, seeded rule lifecycle, and compliance posture behind S2P
          invoice recommendations.
        </p>
      </div>

      <article className="copilot-card p-5">
        <label className="text-sm font-medium text-slate-700">
          Invoice audit target
          <select
            value={invoiceId(selected)}
            onChange={(event) => setSelectedId(event.target.value)}
            className="mt-2 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm md:max-w-md"
          >
            {invoices.map((invoice) => (
              <option key={invoiceId(invoice)} value={invoiceId(invoice)}>
                {invoiceId(invoice)} · {invoice.category ?? "category"}
              </option>
            ))}
          </select>
        </label>
      </article>

      <AuditTrailPanel invoiceId={invoiceId(selected)} />
      <CohortStatusPanel />
      <FactorInsightPanel />
      <EvolutionPanel />
      <DiscoveryPanel />
      <DisruptionRecoveryPanel />
      <RuleLifecyclePanel />
      <CompliancePanel />
      <ReceiptChainPanel />
      <AuditExportPanel />
      <ComplianceScreeningPanel />
    </section>
  );
}
