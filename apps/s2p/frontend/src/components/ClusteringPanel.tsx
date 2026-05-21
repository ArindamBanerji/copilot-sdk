import { useEffect, useState } from "react";

import { getSupplierClusters } from "../api";
import type { BehavioralCluster, ClusteringResponse } from "../types";

function formatCurrencyShort(value: number): string {
  if (!Number.isFinite(value) || value === 0) {
    return "$0";
  }

  const sign = value < 0 ? "-" : "";
  const absoluteValue = Math.abs(value);

  if (absoluteValue >= 1_000_000) {
    const precision = absoluteValue >= 10_000_000 ? 0 : 1;
    return `${sign}$${(absoluteValue / 1_000_000).toFixed(precision)}M`;
  }

  if (absoluteValue >= 1_000) {
    return `${sign}$${Math.round(absoluteValue / 1_000)}K`;
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function potentialLabel(potential: BehavioralCluster["consolidation_potential"]): string {
  return `${potential.charAt(0).toUpperCase()}${potential.slice(1)} potential`;
}

function cardTone(potential: BehavioralCluster["consolidation_potential"]): string {
  if (potential === "high") {
    return "border-amber-300 bg-amber-50";
  }

  if (potential === "medium") {
    return "border-sky-200 bg-sky-50";
  }

  return "border-slate-200 bg-white";
}

function badgeTone(potential: BehavioralCluster["consolidation_potential"]): string {
  if (potential === "high") {
    return "bg-amber-100 text-amber-800";
  }

  if (potential === "medium") {
    return "bg-sky-100 text-sky-800";
  }

  return "bg-slate-100 text-slate-700";
}

export function ClusteringPanel() {
  const [data, setData] = useState<ClusteringResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    setLoading(true);
    setError(false);

    getSupplierClusters()
      .then((response) => {
        if (cancelled) {
          return;
        }

        if (response) {
          setData(response);
        } else {
          setData(null);
          setError(true);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setData(null);
          setError(true);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const clusters = data?.clusters ?? [];

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">Supplier consolidation</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-950">Behavioral Clusters</h2>
        </div>
        {data ? (
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
            {data.method.replace(/_/g, " ")}
          </span>
        ) : null}
      </div>

      {loading ? (
        <div className="mt-4 rounded-lg border border-dashed border-slate-200 p-4 text-sm text-slate-600">
          Loading supplier clusters...
        </div>
      ) : error ? (
        <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          Unable to load supplier clusters.
        </div>
      ) : clusters.length === 0 ? (
        <div className="mt-4 rounded-lg border border-dashed border-slate-200 p-4 text-sm text-slate-600">
          No supplier clusters are available yet.
        </div>
      ) : (
        <>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs uppercase tracking-wide text-slate-500">Clusters</p>
              <p className="mt-1 text-xl font-semibold text-slate-950">{clusters.length}</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs uppercase tracking-wide text-slate-500">Suppliers</p>
              <p className="mt-1 text-xl font-semibold text-slate-950">{data?.total_suppliers ?? 0}</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs uppercase tracking-wide text-slate-500">Candidates</p>
              <p className="mt-1 text-xl font-semibold text-slate-950">
                {data?.consolidation_candidates ?? 0}
              </p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs uppercase tracking-wide text-slate-500">Annual Savings</p>
              <p className="mt-1 text-xl font-semibold text-slate-950">
                {formatCurrencyShort(data?.estimated_annual_savings ?? 0)}
              </p>
            </div>
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            {clusters.map((cluster) => (
              <section
                key={cluster.cluster_id}
                className={`rounded-lg border p-4 ${cardTone(cluster.consolidation_potential)}`}
              >
                <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h3 className="text-base font-semibold text-slate-950">{cluster.label}</h3>
                    <p className="mt-1 text-sm text-slate-600">
                      {cluster.members.length} supplier{cluster.members.length === 1 ? "" : "s"}
                    </p>
                  </div>
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-semibold ${badgeTone(
                      cluster.consolidation_potential
                    )}`}
                  >
                    {potentialLabel(cluster.consolidation_potential)}
                  </span>
                </div>

                <div className="mt-4 flex items-center justify-between rounded-md bg-white/70 px-3 py-2">
                  <span className="text-sm text-slate-600">Estimated savings</span>
                  <span className="text-sm font-semibold text-slate-950">
                    {formatCurrencyShort(cluster.estimated_savings)}
                  </span>
                </div>

                <div className="mt-4">
                  <p className="text-xs uppercase tracking-wide text-slate-500">Members</p>
                  {cluster.members.length > 0 ? (
                    <p className="mt-1 text-sm text-slate-700">{cluster.members.join(", ")}</p>
                  ) : (
                    <p className="mt-1 text-sm text-slate-500">No assigned suppliers.</p>
                  )}
                </div>
              </section>
            ))}
          </div>
        </>
      )}
    </article>
  );
}
