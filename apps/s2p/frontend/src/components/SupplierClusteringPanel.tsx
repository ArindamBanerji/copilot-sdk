import { useEffect, useState } from "react";
import { fetchSupplierClustering } from "../api";

type SupplierCluster = {
  cluster_id?: string;
  cluster_name?: string;
  supplier_ids?: string[];
  avg_otif?: number;
  avg_exception_rate?: number;
  description?: string;
};

function ensureArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

function formatPct(value?: number): string {
  if (typeof value !== "number") return "n/a";
  return `${Math.round(value * 100)}%`;
}

export function SupplierClusteringPanel() {
  const [clusters, setClusters] = useState<SupplierCluster[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchSupplierClustering()
      .then((response) => {
        if (!cancelled) {
          setClusters(ensureArray<SupplierCluster>((response as { clusters?: unknown } | null)?.clusters));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <article className="copilot-card p-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Supplier clustering</p>
      <h2 className="mt-1 text-lg font-semibold text-slate-950">Threshold-based cohorts</h2>
      {loading ? (
        <p className="mt-4 text-sm text-slate-500">Loading supplier clusters...</p>
      ) : clusters.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">Supplier clusters are unavailable.</p>
      ) : (
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {clusters.map((cluster, index) => {
            const suppliers = ensureArray<string>(cluster.supplier_ids);
            return (
              <div key={cluster.cluster_id ?? `cluster-${index}`} className="rounded-md border border-slate-200 bg-white p-3">
                <p className="text-sm font-semibold text-slate-950">{cluster.cluster_name ?? "Supplier cluster"}</p>
                <p className="mt-1 text-xs text-slate-500">{cluster.description ?? "Threshold-based supplier group."}</p>
                <dl className="mt-3 grid grid-cols-3 gap-2 text-xs">
                  <Stat label="Suppliers" value={suppliers.length} />
                  <Stat label="OTIF" value={formatPct(cluster.avg_otif)} />
                  <Stat label="Exceptions" value={formatPct(cluster.avg_exception_rate)} />
                </dl>
              </div>
            );
          })}
        </div>
      )}
    </article>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <dt className="text-slate-500">{label}</dt>
      <dd className="mt-1 font-semibold text-slate-950">{value}</dd>
    </div>
  );
}
