import { useEffect, useMemo, useState } from "react";
import { getDisruptionRecovery } from "../api";
import type { DisruptionRecovery, DisruptionResponse } from "../types";

function titleCase(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function currency(value: number): string {
  if (Math.abs(value) >= 1_000_000) return `$${(value / 1_000_000).toLocaleString(undefined, { maximumFractionDigits: 1 })}M`;
  if (Math.abs(value) >= 1_000) return `$${Math.round(value / 1_000)}K`;
  return `$${value.toLocaleString()}`;
}

function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function DisruptionRecoveryPanel() {
  const [data, setData] = useState<DisruptionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    getDisruptionRecovery()
      .then((response) => {
        if (cancelled) return;
        if (!response) {
          setError("Unable to load disruption recovery.");
          setData(null);
          return;
        }
        setData(response);
      })
      .catch(() => {
        if (!cancelled) {
          setError("Unable to load disruption recovery.");
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

  const disruptions = data?.disruptions ?? [];
  const maxRecovery = useMemo(
    () => Math.max(1, ...disruptions.map((disruption) => disruption.recovery_time_days)),
    [disruptions],
  );
  const disruptionType = disruptions[0]?.disruption_type ? titleCase(disruptions[0].disruption_type) : "Disruption";

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Recovery memory</p>
          <h2 className="mt-1 text-xl font-semibold text-slate-950">Disruption Recovery Learning</h2>
        </div>
        {loading ? <span className="text-sm text-slate-500">Loading recovery history...</span> : null}
      </div>

      {error ? <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}

      {!loading && !error && disruptions.length === 0 ? (
        <p className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-500">No disruption recovery history available.</p>
      ) : null}

      {data && disruptions.length > 0 ? (
        <>
          <div className="mt-4 grid gap-3 sm:grid-cols-4">
            <Metric label="Disruption type" value={disruptionType} />
            <Metric label="Disruptions" value={data.total_disruptions} />
            <Metric label="Cumulative savings" value={currency(data.cumulative_savings)} />
            <Metric label="Avg improvement" value={`${Math.round(data.avg_improvement_pct)}%`} />
          </div>

          <div className="mt-5 space-y-4">
            {disruptions.map((disruption) => (
              <RecoveryRow key={disruption.disruption_id} disruption={disruption} maxRecovery={maxRecovery} />
            ))}
          </div>

          <p className="mt-5 rounded-md bg-amber-50 p-3 text-sm text-amber-900">{data.learning_narrative}</p>
        </>
      ) : null}
    </article>
  );
}

function RecoveryRow({
  disruption,
  maxRecovery,
}: {
  disruption: DisruptionRecovery;
  maxRecovery: number;
}) {
  const width = `${Math.max(4, Math.round((disruption.recovery_time_days / maxRecovery) * 100))}%`;
  return (
    <section className="rounded-md border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-950">Occurrence {disruption.occurrence}</h3>
          <p className="mt-1 text-xs text-slate-500">{titleCase(disruption.pattern_reuse)}</p>
        </div>
        <div className="text-right">
          <p className="text-sm font-semibold text-slate-950">{disruption.recovery_time_days} days</p>
          <p className="text-xs text-slate-500">{currency(disruption.recovery_cost)} recovery cost</p>
        </div>
      </div>
      <div className="mt-3 h-3 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-amber-500" style={{ width }} />
      </div>
      <div className="mt-3 flex flex-wrap gap-2 text-xs font-semibold text-slate-600">
        <span>{percent(disruption.improvement_from_first)} faster than first</span>
        <span>{disruption.decisions_applied} decisions applied</span>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-sm font-semibold text-slate-950">{value}</p>
    </div>
  );
}
