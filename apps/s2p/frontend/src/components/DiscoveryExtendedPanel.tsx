import { useEffect, useState } from "react";
import { getExtendedDiscoveries } from "../api";
import type { ExtendedDiscovery, ExtendedDiscoveryResponse } from "../types";

function percent(value?: number): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "n/a";
}

function label(value: string): string {
  return value.replace(/_/g, " ");
}

export function DiscoveryExtendedPanel() {
  const [data, setData] = useState<ExtendedDiscoveryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    getExtendedDiscoveries()
      .then((response) => {
        if (cancelled) return;
        if (!response) {
          setError("Cross-system discoveries are unavailable.");
          setData(null);
          return;
        }
        setData(response);
      })
      .catch(() => {
        if (!cancelled) {
          setError("Cross-system discoveries are unavailable.");
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
  const byType = Object.entries(data?.by_type ?? {});

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Connected signals</p>
          <h2 className="mt-1 text-xl font-semibold text-slate-950">Cross-System Discovery</h2>
        </div>
        {loading ? <span className="text-sm text-slate-500">Loading discoveries...</span> : null}
      </div>

      {error ? <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}

      {!loading && !error && discoveries.length === 0 ? (
        <p className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-500">
          No extended discoveries are available.
        </p>
      ) : null}

      {!loading && !error && data && discoveries.length > 0 ? (
        <>
          <div className="mt-4 grid gap-3 md:grid-cols-[220px_1fr]">
            <div className="rounded-md border border-slate-200 bg-white p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Sources connected</p>
              <p className="mt-2 text-2xl font-semibold text-slate-950">{data.sources_connected}</p>
            </div>
            <div className="rounded-md border border-slate-200 bg-white p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Distribution by type</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {byType.map(([type, count]) => (
                  <span key={type} className="rounded border border-slate-200 bg-slate-50 px-2 py-1 text-xs font-semibold text-slate-700">
                    {label(type)}: {count}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-4 space-y-3">
            {discoveries.map((discovery) => (
              <DiscoveryRow key={discovery.discovery_id} discovery={discovery} />
            ))}
          </div>
        </>
      ) : null}
    </article>
  );
}

function DiscoveryRow({ discovery }: { discovery: ExtendedDiscovery }) {
  const width = Math.min(Math.max(discovery.correlation_strength * 100, 0), 100);
  return (
    <div className="rounded-md border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-mono text-xs font-semibold text-slate-500">{discovery.discovery_id}</p>
          <h3 className="mt-1 text-sm font-semibold text-slate-950">{discovery.title}</h3>
          <p className="mt-1 text-xs capitalize text-slate-500">{label(discovery.type)}</p>
        </div>
        <span className="rounded border border-amber-200 bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-700">
          {percent(discovery.correlation_strength)}
        </span>
      </div>

      <div className="mt-3 h-2 rounded-full bg-slate-100">
        <div className="h-2 rounded-full bg-amber-500" style={{ width: `${width}%` }} />
      </div>

      <div className="mt-3 grid gap-2 text-sm md:grid-cols-2">
        <p className="rounded bg-slate-50 p-2 text-slate-600">
          Impact <span className="font-semibold text-slate-950">{discovery.impact_estimate}</span>
        </p>
        <p className="rounded bg-slate-50 p-2 text-slate-600">
          Detections <span className="font-semibold text-slate-950">{discovery.detection_count}</span>
        </p>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {discovery.propagation_path.map((step) => (
          <span key={step} className="rounded border border-slate-200 bg-white px-2 py-1 text-xs text-slate-600">
            {label(step)}
          </span>
        ))}
      </div>
    </div>
  );
}
