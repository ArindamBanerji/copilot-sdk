import { useEffect, useState } from "react";
import { getNoveltyStatus } from "../api";
import type { NoveltyPerCategory, NoveltyStatusResponse } from "../types";

function percent(value?: number): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "n/a";
}

function categoryMetrics(value: NoveltyPerCategory | number): NoveltyPerCategory {
  if (typeof value === "number") return { novelty_rate: value };
  return value;
}

function label(value: string): string {
  return value.replace(/_/g, " ");
}

export function NoveltyStatusPanel() {
  const [data, setData] = useState<NoveltyStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    getNoveltyStatus()
      .then((response) => {
        if (cancelled) return;
        if (!response) {
          setError("Distribution monitor is unavailable.");
          setData(null);
          return;
        }
        setData(response);
      })
      .catch(() => {
        if (!cancelled) {
          setError("Distribution monitor is unavailable.");
          setData(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const categories = Object.entries(data?.per_category ?? {});

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Novelty detection</p>
          <h2 className="mt-1 text-xl font-semibold text-slate-950">Distribution Monitor</h2>
        </div>
        {loading ? <span className="text-sm text-slate-500">Loading distribution status...</span> : null}
      </div>

      {error ? <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}

      {!loading && !error && data ? (
        <>
          <div className="mt-4 grid gap-3 sm:grid-cols-4">
            <Metric label="Novelty rate" value={percent(data.novelty_rate)} />
            <Metric label="Alert status" value={data.alert_active ? "ALERT" : "Normal"} />
            <Metric label="Decisions in window" value={data.total_in_window} />
            <Metric label="Window size" value={data.window_size} />
          </div>

          {categories.length > 0 ? (
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {categories.map(([category, rawMetrics]) => {
                const metrics = categoryMetrics(rawMetrics);
                return (
                  <div key={category} className="rounded-md border border-slate-200 bg-white p-3">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-semibold capitalize text-slate-900">{label(category)}</p>
                      <span className="text-xs font-semibold text-slate-500">{percent(metrics.novelty_rate)}</span>
                    </div>
                    <div className="mt-3 h-2 rounded-full bg-slate-100">
                      <div
                        className="h-2 rounded-full bg-amber-500"
                        style={{ width: `${Math.min(Math.max((metrics.novelty_rate ?? 0) * 100, 0), 100)}%` }}
                      />
                    </div>
                    <p className="mt-2 text-xs text-slate-500">
                      {metrics.novelty_count ?? 0} novel of {metrics.total_in_window ?? 0} decisions
                    </p>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-500">
              No category-level novelty history is available yet.
            </p>
          )}
        </>
      ) : null}
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-lg font-semibold text-slate-950">{value}</p>
    </div>
  );
}
