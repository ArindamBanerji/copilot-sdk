import { useEffect, useState } from "react";
import { getPreviewConservation, getPreviewQueue } from "../api";
import type { ConservationStatus, PreviewQueueResponse } from "../types";

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

  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Source-to-Pay</p>
        <h1 className="mt-1 text-3xl font-semibold text-slate-950">Dashboard</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">
          Preview shell for invoice exception management. Dashboard data comes from the S2P preview
          backend while Phase 1 workflow screens remain intentionally inactive.
        </p>
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

      <article className="copilot-card border-amber-200 bg-amber-50 p-5">
        <h2 className="text-base font-semibold text-amber-900">Phase 1 scope note</h2>
        <p className="mt-2 text-sm text-amber-900">
          This scaffold exposes preview data only. Exception scoring, verification, supplier detail
          workflows, and learned decision exploration are reserved for Phase 1.
        </p>
      </article>
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
