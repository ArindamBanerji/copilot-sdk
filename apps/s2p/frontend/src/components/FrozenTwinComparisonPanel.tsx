import { useEffect, useState } from "react";
import { fetchTwinDrift, fetchTwinStatus } from "../api";
import type { TwinDriftReport, TwinStatusResponse } from "../types";
import ProvenanceBadge from "./ProvenanceBadge";

function numberValue(report: TwinDriftReport | null, keys: string[]): number | null {
  for (const key of keys) {
    const value = report?.[key];
    if (typeof value === "number" && Number.isFinite(value)) return value;
  }
  return null;
}

export function FrozenTwinComparisonPanel() {
  const [status, setStatus] = useState<TwinStatusResponse | null>(null);
  const [drift, setDrift] = useState<TwinDriftReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchTwinStatus(), fetchTwinDrift()]).then(([nextStatus, nextDrift]) => {
      if (!cancelled) { setStatus(nextStatus); setDrift(nextDrift); }
    }).finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const frozen = numberValue(drift, ["frozen_accuracy", "baseline_accuracy", "frozen_score"]);
  const live = numberValue(drift, ["live_accuracy", "current_accuracy", "live_score"]);
  const delta = frozen !== null && live !== null ? live - frozen : numberValue(drift, ["accuracy_delta", "delta"]);

  return (
    <article data-testid="frozen-twin-comparison-panel" className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">S2P-TWIN</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-950">Frozen Twin: day-zero baseline vs live</h2>
          <p className="mt-1 text-sm text-slate-600">The gap between the pinned baseline and live scorer is the value of compounding.</p>
        </div>
        <div className="flex items-center gap-2"><span data-testid="frozen-twin-modeled-label" className="rounded-full bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-800">MODELED / PILOT-TARGET</span><ProvenanceBadge source="context" /></div>
      </div>
      {loading ? <p className="mt-5 text-sm text-slate-500">Loading frozen twin...</p> : (
        <>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">
            <Metric label="Twin state" value={status?.frozen ? "Day-0 frozen" : "Not frozen"} />
            <Metric label="Measured delta" value={delta === null ? "Pending outcomes" : `${delta >= 0 ? "+" : ""}${(delta * 100).toFixed(1)} pp`} />
          </div>
          {frozen !== null && live !== null ? (
            <div className="mt-5 space-y-3" data-testid="frozen-twin-curves">
              <Curve label="Frozen baseline" value={frozen} color="bg-slate-400" />
              <Curve label="Live scorer" value={live} color="bg-amber-500" />
            </div>
          ) : <p className="mt-5 rounded-md bg-slate-50 p-4 text-sm text-slate-600">The twin exists, but its accuracy series is awaiting measured outcomes.</p>}
        </>
      )}
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-md bg-slate-50 p-3"><p className="text-xs uppercase tracking-wide text-slate-500">{label}</p><p className="mt-1 font-semibold text-slate-900">{value}</p></div>; }
function Curve({ label, value, color }: { label: string; value: number; color: string }) { const width = Math.max(0, Math.min(100, value * 100)); return <div><div className="mb-1 flex justify-between text-sm"><span>{label}</span><span className="font-medium">{(value * 100).toFixed(1)}%</span></div><div className="h-3 rounded-full bg-slate-100"><div className={`h-3 rounded-full ${color}`} style={{ width: `${width}%` }} /></div></div>; }

export default FrozenTwinComparisonPanel;
