import { useEffect, useState } from "react";
import { TransferBadge } from "../../../../../copilot_sdk/frontend";
import { API_URL, getPreviewConservation, getPreviewQueue } from "../api";
import { AutoApprovePanel } from "../components/AutoApprovePanel";
import { ConservationMiniGauge } from "../components/ConservationMiniGauge";
import { ControlTowerPanel } from "../components/ControlTowerPanel";
import { FinancialImpactCard } from "../components/FinancialImpactCard";
import { NoveltyStatusPanel } from "../components/NoveltyStatusPanel";
import { ProcessContextCard } from "../components/ProcessContextCard";
import type { ConservationStatus, InvoiceException, PreviewQueueResponse } from "../types";

function formatPercent(value?: number): string {
  if (typeof value !== "number") return "n/a";
  return `${Math.round(value * 100)}%`;
}

export function DashboardScreen() {
  const [queue, setQueue] = useState<PreviewQueueResponse | null>(null);
  const [conservation, setConservation] = useState<ConservationStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.all([getPreviewQueue(), getPreviewConservation()])
      .then(([queueData, conservationData]) => {
        if (!cancelled) {
          setQueue(queueData);
          setConservation(conservationData);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const autoApproveRate = queue?.auto_approve_rate ?? queue?.autoApproveRate;
  const confidenceAvg = queue?.confidence_avg ?? queue?.confidenceAvg;
  const verifiedDecisions = conservation?.verified_decisions ?? conservation?.verifiedDecisions;
  const recent = queue?.exceptions ?? [];
  const firstInvoice = recent[0];

  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Source-to-Pay</p>
        <h1 className="mt-1 text-3xl font-semibold text-slate-950">Dashboard</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">
          Monitor the S2P exception queue, process bottlenecks, recent recommendations, and the
          conservation state before analysts move into triage.
        </p>
        <div className="mt-3">
          <TransferBadge apiBase={API_URL} />
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <article className="copilot-card p-5">
          <h2 className="text-lg font-semibold text-slate-900">Exception Queue</h2>
          {loading ? (
            <p className="mt-3 text-sm text-slate-500">Loading preview queue...</p>
          ) : (
            <div className="mt-4 grid grid-cols-3 gap-3">
              <Metric label="Total invoices" value={queue?.total ?? 0} />
              <Metric label="Auto-approve rate" value={formatPercent(autoApproveRate)} />
              <Metric label="Avg confidence" value={formatPercent(confidenceAvg)} />
            </div>
          )}
        </article>

        <article className="copilot-card p-5">
          <h2 className="text-lg font-semibold text-slate-900">Conservation Status</h2>
          {loading ? (
            <p className="mt-3 text-sm text-slate-500">Loading conservation preview...</p>
          ) : conservation ? (
            <div className="mt-4 grid grid-cols-3 gap-3">
              <Metric label="Status" value={conservation.status ?? "n/a"} />
              <Metric label="Verified decisions" value={verifiedDecisions ?? 0} />
              <Metric label="Accuracy" value={formatPercent(conservation.accuracy)} />
            </div>
          ) : (
            <p className="mt-3 text-sm text-slate-500">Preview conservation data is unavailable.</p>
          )}
        </article>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_360px]">
        <article className="copilot-card p-5">
          <h2 className="text-lg font-semibold text-slate-900">Recent Decisions</h2>
          {loading ? (
            <p className="mt-3 text-sm text-slate-500">Loading recent decisions...</p>
          ) : recent.length === 0 ? (
            <p className="mt-3 text-sm text-slate-500">No recent invoice decisions available.</p>
          ) : (
            <div className="mt-4 divide-y divide-slate-100">
              {recent.slice(0, 5).map((invoice) => (
                <DecisionRow key={invoiceId(invoice)} invoice={invoice} />
              ))}
            </div>
          )}
        </article>
        <ConservationMiniGauge conservation={conservation} />
      </div>

      <NoveltyStatusPanel />

      <AutoApprovePanel />

      <ProcessContextCard invoice={firstInvoice} />

      <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <ControlTowerPanel />
        <FinancialImpactCard />
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-xl font-semibold text-slate-950">{value}</p>
    </div>
  );
}

function invoiceId(invoice: InvoiceException): string {
  return invoice.invoice_id ?? invoice.invoiceId ?? invoice.event_id ?? invoice.eventId ?? "invoice";
}

function DecisionRow({ invoice }: { invoice: InvoiceException }) {
  const action = invoice.recommended_action ?? invoice.recommendedAction ?? invoice.scored_action ?? invoice.scoredAction ?? "hold_for_review";
  return (
    <div className="py-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <span className="font-mono text-xs font-semibold text-slate-700">{invoiceId(invoice)}</span>
        <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
          {String(action).replace(/_/g, " ")}
        </span>
      </div>
      <p className="mt-1 text-sm text-slate-600">
        {invoice.supplier_name ?? invoice.supplierName ?? invoice.supplier ?? "Unknown supplier"} · {invoice.category ?? "uncategorized"}
      </p>
    </div>
  );
}
