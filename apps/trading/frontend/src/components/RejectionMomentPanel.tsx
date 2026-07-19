import { useEffect, useState } from "react";
import { fetchRejectionSummary } from "../api";
import type { RejectionSummaryResponse } from "../api";
import ProvenanceBadge from "./ProvenanceBadge";

// NOTE: This component is duplicated in gen-ai-roi-demo-v4-v50/frontend/src/components/RejectionMomentPanel.tsx.
// If you modify this file, update the counterpart.
// Duplication exists because SDK apps and SOC have separate frontend build pipelines.
// A shared component library would eliminate this but is out of scope for this batch.

const LABELS: Record<string, string> = {
  correctness_floor: "Correctness floor",
  conservation: "Conservation gate",
  variance_stability: "Variance stability",
};

export default function RejectionMomentPanel() {
  const [summary, setSummary] = useState<RejectionSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchRejectionSummary()
      .then((payload) => {
        if (!cancelled) setSummary(payload);
      })
      .catch((loadError) => {
        console.debug("rejection summary unavailable", loadError);
        if (!cancelled) setError("Rejection summary unavailable.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const breakdown = summary?.rejectionBreakdown || {};
  const rejected = summary?.rejectedVariants || [];

  return (
    <section className="copilot-card p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-base font-semibold">Agent Evolution Summary</h2>
        {summary && <ProvenanceBadge source={summary.provenance || "learned"} />}
      </div>
      {loading && <p className="mt-3 text-sm trading-muted">Loading rejection summary...</p>}
      {!loading && error && <p className="mt-3 text-sm trading-muted">Rejection summary unavailable.</p>}
      {!loading && !error && (
        <div className="mt-4 space-y-4">
          <div className="grid gap-3 md:grid-cols-3">
            <Stat label="Tested" value={String(summary?.totalTested ?? 0)} />
            <Stat label="Promoted" value={String(summary?.totalPromoted ?? 0)} />
            <Stat label="Rejected" value={String(summary?.totalRejected ?? 0)} />
          </div>
          <div>
            <div className="text-sm font-semibold">Rejection breakdown</div>
            <div className="mt-2 grid gap-2 md:grid-cols-3">
              {Object.entries(LABELS).map(([key, label]) => (
                <div key={key} className="rounded-md border px-3 py-2" style={{ borderColor: "var(--copilot-border)" }}>
                  <div className="text-xs trading-muted">{label}</div>
                  <div className="text-lg font-semibold">{breakdown[key] ?? 0}</div>
                </div>
              ))}
            </div>
          </div>
          <div>
            <div className="text-sm font-semibold">Recent rejections</div>
            {rejected.length === 0 ? (
              <p className="mt-2 text-sm trading-muted">No rejected variants yet.</p>
            ) : (
              <div className="mt-2 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <tbody>
                    {rejected.slice(0, 5).map((variant) => (
                      <tr key={`${variant.variantId}-${variant.reason}`} className="border-t" style={{ borderColor: "var(--copilot-border)" }}>
                        <td className="py-2 pr-3 font-mono text-xs">{variant.variantId}</td>
                        <td className="py-2 pr-3">{LABELS[variant.reason || ""] || variant.reason}</td>
                        <td className="py-2 trading-muted">{variant.detail}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border px-3 py-2" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="text-xs trading-muted">{label}</div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  );
}
