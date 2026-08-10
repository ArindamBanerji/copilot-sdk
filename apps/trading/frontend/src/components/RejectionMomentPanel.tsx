import { useEffect, useState } from "react";
import { fetchEvolutionSummary } from "../api";
import { fetchRejectionSummary } from "../api";
import type { EvolutionSummaryResponse, RejectionSummaryResponse } from "../api";
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
  const [summary, setSummary] = useState<EvolutionSummaryResponse | null>(null);
  const [aggregate, setAggregate] = useState<RejectionSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchEvolutionSummary(), fetchRejectionSummary()])
      .then(([payload, aggregatePayload]) => {
        if (!cancelled) {
          setSummary(payload);
          setAggregate(aggregatePayload);
        }
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

  const events = summary?.recent_events || [];
  const rejected = events.filter((event) => event.event_type === "rejected");
  const promoted = events.filter((event) => event.event_type === "promoted");
  const tested = aggregate?.totalTested ?? events.filter((event) => ["rejected", "promoted"].includes(event.event_type || "")).length;
  const promotedCount = aggregate?.totalPromoted ?? promoted.length;
  const rejectedCount = aggregate?.totalRejected ?? rejected.length;

  return (
    <section className="copilot-card p-4" data-testid="rejection-moment-panel">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-base font-semibold">Rejection Moment</h2>
        {summary && <ProvenanceBadge source="learned" />}
      </div>
      {loading && <p className="mt-3 text-sm trading-muted">Loading rejection summary...</p>}
      {!loading && error && <p className="mt-3 text-sm trading-muted">Rejection summary unavailable.</p>}
      {!loading && !error && (
        <div className="mt-4 space-y-4">
          <div className="grid gap-3 md:grid-cols-3">
            <Stat label="Tested" value={String(tested)} />
            <Stat label="Promoted" value={String(promotedCount)} />
            <Stat label="Rejected" value={String(rejectedCount)} />
          </div>
          <div>
            <div className="text-sm font-semibold">Recent rejections</div>
            {rejected.length === 0 ? (
              <p className="mt-2 text-sm trading-muted">No rejected variants yet.</p>
            ) : (
              <div className="mt-2 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <tbody>
                    {rejected.slice(0, 5).map((event, index) => (
                      <tr key={`${event.variant_id}-${event.timestamp}-${index}`} className="border-t" style={{ borderColor: "var(--copilot-border)" }}>
                        <td className="py-2 pr-3 font-mono text-xs">{event.variant_id || "unknown"}</td>
                        <td className="py-2 pr-3">{LABELS[event.reason || ""] || event.reason || "unspecified"}</td>
                        <td className="py-2 trading-muted">{event.timestamp || "recent"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
          <div>
            <div className="text-sm font-semibold">Recent promotions</div>
            {promoted.length === 0 ? (
              <p className="mt-2 text-sm trading-muted">No promoted variants yet.</p>
            ) : (
              <div className="mt-2 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <tbody>
                    {promoted.slice(0, 5).map((event, index) => (
                      <tr key={`${event.variant_id}-${event.timestamp}-${index}`} className="border-t" style={{ borderColor: "var(--copilot-border)" }}>
                        <td className="py-2 pr-3 font-mono text-xs">{event.variant_id || "unknown"}</td>
                        <td className="py-2 pr-3">PROMOTED</td>
                        <td className="py-2 trading-muted">{event.timestamp || "recent"}</td>
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
