import { useEffect, useMemo, useState } from "react";
import { fetchS2PProcessSignals } from "../api";
import type { ProcessActivity, ProcessSignalsResponse } from "../types";

function activityName(activity: ProcessActivity) {
  return activity.name ?? activity.activity ?? activity.id ?? activity.activity_id ?? "Process activity";
}

function duration(activity: ProcessActivity) {
  return activity.duration_median_hours ?? activity.durationMedianHours ?? activity.avg_duration_hours ?? activity.avgDurationHours ?? 0;
}

export function ProcessSignalsPanel({ supplierId }: { supplierId?: string }) {
  const [data, setData] = useState<ProcessSignalsResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchS2PProcessSignals(supplierId).then((response) => {
      if (!cancelled) setData(response);
    });
    return () => {
      cancelled = true;
    };
  }, [supplierId]);

  const activities = data?.activities ?? [];
  const maxDuration = useMemo(() => Math.max(1, ...activities.map(duration)), [activities]);

  return (
    <article className="copilot-card p-5">
      <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Process signals</p>
      <h2 className="mt-1 text-xl font-semibold text-slate-950">{data?.process_model ?? data?.processModel ?? "Purchase-to-Pay"}</h2>
      <p className="mt-1 text-sm text-slate-500">{data?.variant ?? "Standard variant"} · Celonis process context</p>
      {activities.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">No process activity data available.</p>
      ) : (
        <div className="mt-5 space-y-3">
          {activities.map((activity, index) => {
            const value = duration(activity);
            const width = Math.max(6, Math.round((value / maxDuration) * 100));
            return (
              <div key={`${activityName(activity)}-${index}`} className="grid gap-2 md:grid-cols-[190px_1fr_72px] md:items-center">
                <div>
                  <p className="text-sm font-medium text-slate-950">{activityName(activity)}</p>
                  {activity.bottleneck ? (
                    <p className="text-xs text-amber-700">bottleneck {activity.bottleneck_cause ?? activity.bottleneckCause ?? ""}</p>
                  ) : null}
                </div>
                <div className="h-3 rounded-md bg-slate-100">
                  <div
                    className={activity.bottleneck ? "h-3 rounded-md bg-amber-500" : "h-3 rounded-md bg-slate-400"}
                    style={{ width: `${width}%` }}
                  />
                </div>
                <p className="text-right text-sm text-slate-600">{value.toFixed(1)}h</p>
              </div>
            );
          })}
        </div>
      )}
    </article>
  );
}
