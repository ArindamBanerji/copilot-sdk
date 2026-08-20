import { useEffect, useState } from "react";
import { fetchPromotionStatus } from "../api";
import type { PromotionRecord } from "../types";
import ProvenanceBadge from "./ProvenanceBadge";

const STAGES = ["discovered", "shadowing", "promoted", "measuring", "kept", "rolled_back", "transferred"];

function label(stage: string): string {
  return stage.replace("_", " ").toUpperCase();
}

function lastTimestamp(record: PromotionRecord): string | null {
  const history = record.stage_history ?? [];
  const value = history[history.length - 1]?.timestamp ?? history[history.length - 1]?.created_at;
  return typeof value === "string" ? value : null;
}

export function ExceptionExtinctionTimeline() {
  const [records, setRecords] = useState<PromotionRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchPromotionStatus().then((response) => {
      if (!cancelled) setRecords(response?.categories ?? []);
    }).finally(() => {
      if (!cancelled) setLoading(false);
    });
    return () => { cancelled = true; };
  }, []);

  return (
    <article data-testid="exception-extinction-timeline" className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">S2P-EXTINCT</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-950">Exception extinction lifecycle</h2>
          <p className="mt-1 text-sm text-slate-600">Discover → shadow → promote → measure → keep or rollback → transfer.</p>
        </div>
        <ProvenanceBadge source="context" />
      </div>

      <div className="mt-5 overflow-x-auto">
        <div className="flex min-w-[720px] items-center gap-2 text-[11px] font-semibold text-slate-500">
          {STAGES.map((stage, index) => (
            <div key={stage} className="flex flex-1 items-center gap-2">
              <span>{label(stage)}</span>
              {index < STAGES.length - 1 && <span className="h-px flex-1 bg-slate-200" />}
            </div>
          ))}
        </div>
      </div>

      {loading ? <p className="mt-5 text-sm text-slate-500">Loading promotion lifecycle...</p> : records.length === 0 ? (
        <p className="mt-5 rounded-md bg-slate-50 p-4 text-sm text-slate-600">Promotion lifecycle unavailable; no authority records loaded.</p>
      ) : (
        <div className="mt-5 space-y-3">
          {records.map((record) => {
            const stage = record.current_stage ?? "discovered";
            const emphasized = stage === "promoted" || stage === "kept";
            return (
              <div key={record.record_id} data-testid={`extinction-${record.decision_class}`} className="rounded-lg border border-slate-200 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="font-medium text-slate-900">{record.decision_class}</span>
                  <span className={`rounded-full px-2 py-1 text-xs font-semibold ${emphasized ? "bg-emerald-100 text-emerald-800" : stage === "rolled_back" ? "bg-rose-100 text-rose-800" : "bg-slate-100 text-slate-700"}`}>
                    {label(stage)}
                  </span>
                </div>
                <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                  <span>Shadow decisions: {record.shadow_decisions ?? 0}</span>
                  <span>Measured: {record.measurement_decisions ?? 0}</span>
                  {lastTimestamp(record) && <span>Last transition: {lastTimestamp(record)}</span>}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </article>
  );
}

export default ExceptionExtinctionTimeline;
