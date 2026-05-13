import { useEffect, useMemo, useState } from "react";
import { fetchCycleTime } from "../api";

type CycleActivity = {
  id?: string;
  name?: string;
  duration_minutes?: number;
  is_bottleneck?: boolean;
  status?: string;
  system?: string;
};

type CycleTimeResponse = {
  available?: boolean;
  reason?: string;
  activities?: CycleActivity[];
  total_median_minutes?: number;
  bottleneck_name?: string;
  bottleneck_activity?: string;
  bottleneck_pct?: number;
  process_model?: string;
  variant?: string;
};

function ensureArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

function formatMinutes(value?: number): string {
  if (typeof value !== "number") return "n/a";
  if (value >= 60) return `${(value / 60).toFixed(1)}h`;
  return `${Math.round(value)}m`;
}

function formatPct(value?: number): string {
  if (typeof value !== "number") return "n/a";
  return `${Math.round(value * 100)}%`;
}

export function CycleTimePanel() {
  const [data, setData] = useState<CycleTimeResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchCycleTime()
      .then((response) => {
        if (!cancelled) setData((response as CycleTimeResponse | null) ?? null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const activities = ensureArray<CycleActivity>(data?.activities);
  const maxDuration = useMemo(
    () => Math.max(...activities.map((activity) => activity.duration_minutes ?? 0), 1),
    [activities],
  );

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Cycle-time</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-950">Process bottleneck</h2>
        </div>
        <span className="rounded bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-800">
          {data?.available ? "Celonis signal" : "Unavailable"}
        </span>
      </div>

      {loading ? (
        <p className="mt-4 text-sm text-slate-500">Loading cycle-time data...</p>
      ) : !data || data.available === false ? (
        <p className="mt-4 text-sm text-slate-500">{data?.reason ?? "Cycle-time data is unavailable."}</p>
      ) : (
        <>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <Metric label="Total median minutes" value={formatMinutes(data.total_median_minutes)} />
            <Metric label="Bottleneck" value={data.bottleneck_name ?? data.bottleneck_activity ?? "n/a"} />
            <Metric label="Bottleneck share" value={formatPct(data.bottleneck_pct)} />
          </div>
          <div className="mt-5 space-y-3">
            {activities.length === 0 ? (
              <p className="text-sm text-slate-500">No process activities available.</p>
            ) : (
              activities.map((activity, index) => {
                const duration = activity.duration_minutes ?? 0;
                const width = `${Math.max(5, Math.round((duration / maxDuration) * 100))}%`;
                return (
                  <div key={activity.id ?? activity.name ?? `activity-${index}`}>
                    <div className="flex flex-wrap justify-between gap-3 text-sm">
                      <span className="font-medium text-slate-800">{activity.name ?? "Activity"}</span>
                      <span className="text-slate-500">{formatMinutes(duration)}</span>
                    </div>
                    <div className="mt-1 h-2 rounded-full bg-slate-100">
                      <div
                        className={`h-2 rounded-full ${activity.is_bottleneck ? "bg-amber-600" : "bg-slate-400"}`}
                        style={{ width }}
                      />
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </>
      )}
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-sm font-semibold text-slate-950">{value}</p>
    </div>
  );
}
