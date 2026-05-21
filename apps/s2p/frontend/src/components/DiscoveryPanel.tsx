import { useEffect, useState } from "react";
import { getDiscoveryAlerts } from "../api";
import type { CrossSystemDiscovery, DiscoveryResponse } from "../types";

function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function tone(value: number): string {
  if (value >= 0.85) return "border-rose-200 bg-rose-50 text-rose-800";
  if (value >= 0.78) return "border-amber-200 bg-amber-50 text-amber-800";
  return "border-emerald-200 bg-emerald-50 text-emerald-800";
}

function formatPattern(value: string): string {
  return value.replace(/_/g, " ");
}

export function DiscoveryPanel() {
  const [data, setData] = useState<DiscoveryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    getDiscoveryAlerts()
      .then((response) => {
        if (cancelled) return;
        if (!response) {
          setError("Unable to load cross-system discoveries.");
          setData(null);
          return;
        }
        setData(response);
      })
      .catch(() => {
        if (!cancelled) {
          setError("Unable to load cross-system discoveries.");
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

  const discoveries = data?.discoveries ?? [];

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Pattern discovery</p>
          <h2 className="mt-1 text-xl font-semibold text-slate-950">Cross-System Discoveries</h2>
        </div>
        {loading ? <span className="text-sm text-slate-500">Loading discoveries...</span> : null}
      </div>

      {error ? <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}

      {!loading && !error && discoveries.length === 0 ? (
        <p className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-500">No cross-system discoveries available.</p>
      ) : null}

      {data && discoveries.length > 0 ? (
        <>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <Metric label="Discoveries" value={data.total_discoveries} />
            <Metric label="Sources connected" value={data.sources_connected} />
            <Metric label="Highest impact" value={data.highest_impact} />
          </div>
          <div className="mt-4 grid gap-3">
            {discoveries.map((discovery) => (
              <DiscoveryCard key={discovery.discovery_id} discovery={discovery} />
            ))}
          </div>
        </>
      ) : null}
    </article>
  );
}

function DiscoveryCard({ discovery }: { discovery: CrossSystemDiscovery }) {
  return (
    <section className={`rounded-md border p-4 ${tone(discovery.correlation_strength)}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-950">{discovery.title}</h3>
          <p className="mt-1 text-xs font-medium capitalize text-slate-600">{formatPattern(discovery.pattern)}</p>
        </div>
        <span className="rounded-full bg-white/80 px-3 py-1 text-xs font-semibold text-slate-800">
          {percent(discovery.correlation_strength)} correlation
        </span>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {discovery.sources.map((source) => (
          <span key={source} className="rounded-full bg-white/80 px-2 py-1 text-xs font-semibold text-slate-700">
            {source}
          </span>
        ))}
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)]">
        <div className="rounded-md bg-white/80 p-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Impact</p>
          <p className="mt-1 text-sm font-semibold text-slate-950">{discovery.impact_estimate}</p>
          <p className="mt-2 text-xs text-slate-600">{percent(discovery.confidence)} confidence</p>
        </div>
        <div className="rounded-md bg-white/80 p-3">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Recommendation</p>
          <p className="mt-1 text-sm text-slate-700">{discovery.recommendation}</p>
        </div>
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
