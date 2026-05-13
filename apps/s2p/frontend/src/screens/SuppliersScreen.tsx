import { useEffect, useMemo, useState } from "react";
import { fetchSuppliers } from "../api";
import { SupplierClusteringPanel } from "../components/SupplierClusteringPanel";
import { SupplierHeatmap } from "../components/SupplierHeatmap";
import { SupplierProfileCard } from "../components/SupplierProfileCard";

type SupplierSummary = {
  supplier_id?: string;
  supplierId?: string;
  name?: string;
  otif_score?: number;
  exception_rate?: number;
  invoice_count?: number;
  trend_direction?: string;
};

function ensureArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

function supplierId(supplier?: SupplierSummary | null): string {
  return supplier?.supplier_id ?? supplier?.supplierId ?? "";
}

function formatPct(value?: number): string {
  if (typeof value !== "number") return "n/a";
  return `${Math.round(value * 100)}%`;
}

export function SuppliersScreen() {
  const [suppliers, setSuppliers] = useState<SupplierSummary[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    fetchSuppliers()
      .then((response) => {
        if (cancelled) return;
        const rows = ensureArray<SupplierSummary>((response as { suppliers?: unknown } | null)?.suppliers);
        setSuppliers(rows);
        if (!selectedId && rows.length > 0) setSelectedId(supplierId(rows[0]));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  const selectedSupplier = useMemo(
    () => suppliers.find((supplier) => supplierId(supplier) === selectedId) ?? suppliers[0] ?? null,
    [selectedId, suppliers],
  );
  const activeId = selectedId || supplierId(selectedSupplier);

  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Supplier memory</p>
        <h1 className="mt-1 text-3xl font-semibold text-slate-950">Suppliers</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">
          Cluster suppliers, inspect OTIF and exception trends, and review category heatmaps for S2P decisions.
        </p>
      </div>

      <SupplierClusteringPanel />

      <div className="grid gap-4 xl:grid-cols-[360px_1fr]">
        <article className="copilot-card p-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Supplier list</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-950">Select supplier</h2>
          {loading ? (
            <p className="mt-4 text-sm text-slate-500">Loading suppliers...</p>
          ) : suppliers.length === 0 ? (
            <p className="mt-4 text-sm text-slate-500">No supplier profiles available.</p>
          ) : (
            <div className="mt-4 space-y-2">
              {suppliers.map((supplier, index) => {
                const id = supplierId(supplier) || `supplier-${index}`;
                const selected = id === activeId;
                return (
                  <button
                    key={id}
                    type="button"
                    onClick={() => setSelectedId(id)}
                    className={`w-full rounded-md border p-3 text-left transition ${
                      selected ? "border-amber-400 bg-amber-50" : "border-slate-200 bg-white hover:border-amber-200"
                    }`}
                  >
                    <span className="block text-sm font-semibold text-slate-950">{supplier.name ?? id}</span>
                    <span className="mt-1 block text-xs text-slate-500">
                      OTIF {formatPct(supplier.otif_score)} · exception rate {formatPct(supplier.exception_rate)}
                    </span>
                    <span className="mt-1 block text-xs text-slate-500">
                      {supplier.invoice_count ?? 0} fixture invoices · {supplier.trend_direction ?? "stable"}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </article>

        <div className="space-y-4">
          <SupplierProfileCard supplierId={activeId} />
          <SupplierHeatmap supplierId={activeId} />
        </div>
      </div>
    </section>
  );
}
