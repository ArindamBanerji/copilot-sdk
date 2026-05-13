import { useEffect, useState } from "react";
import { fetchSupplierHeatmap } from "../api";

type HeatmapCategory = {
  category?: string;
  invoice_count?: number;
  exception_count?: number;
  exception_rate?: number;
};

type HeatmapResponse = {
  supplier_id?: string;
  categories?: HeatmapCategory[];
  invoice_count?: number;
};

function ensureArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

function formatPct(value?: number): string {
  if (typeof value !== "number") return "n/a";
  return `${Math.round(value * 100)}%`;
}

function intensity(rate?: number): string {
  const value = rate ?? 0;
  if (value >= 0.67) return "bg-red-100 text-red-800 border-red-200";
  if (value >= 0.34) return "bg-amber-100 text-amber-800 border-amber-200";
  return "bg-emerald-50 text-emerald-800 border-emerald-200";
}

export function SupplierHeatmap({ supplierId }: { supplierId?: string }) {
  const [data, setData] = useState<HeatmapResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (!supplierId) {
      setData(null);
      return () => {
        cancelled = true;
      };
    }
    setLoading(true);
    fetchSupplierHeatmap(supplierId)
      .then((response) => {
        if (!cancelled) setData((response as HeatmapResponse | null) ?? null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [supplierId]);

  const categories = ensureArray<HeatmapCategory>(data?.categories);

  return (
    <article className="copilot-card p-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Supplier heatmap</p>
      <h2 className="mt-1 text-lg font-semibold text-slate-950">Category exception pattern</h2>
      {!supplierId ? (
        <p className="mt-4 text-sm text-slate-500">Select a supplier to view category heatmap.</p>
      ) : loading ? (
        <p className="mt-4 text-sm text-slate-500">Loading supplier heatmap...</p>
      ) : !data ? (
        <p className="mt-4 text-sm text-slate-500">Supplier heatmap is unavailable.</p>
      ) : categories.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">No heatmap categories available.</p>
      ) : (
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {categories.map((category, index) => (
            <div
              key={category.category ?? `category-${index}`}
              className={`rounded-md border p-3 ${intensity(category.exception_rate)}`}
            >
              <div className="flex flex-wrap justify-between gap-3">
                <p className="text-sm font-semibold capitalize">{(category.category ?? "category").replace(/_/g, " ")}</p>
                <p className="text-sm font-semibold">{formatPct(category.exception_rate)}</p>
              </div>
              <p className="mt-1 text-xs">
                {category.invoice_count ?? 0} invoices · {category.exception_count ?? 0} exceptions
              </p>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}
