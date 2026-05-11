import { useEffect, useState } from "react";
import { getPreviewSuppliers } from "../api";
import type { SupplierProfile } from "../types";

function formatPercent(value?: number): string {
  if (typeof value !== "number") return "n/a";
  return `${Math.round(value * 100)}%`;
}

function formatCurrency(value?: number): string {
  if (typeof value !== "number") return "n/a";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0
  }).format(value);
}

export function SuppliersScreen() {
  const [suppliers, setSuppliers] = useState<SupplierProfile[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getPreviewSuppliers()
      .then((data) => {
        if (!cancelled) setSuppliers(data.suppliers ?? []);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Supplier memory</p>
        <h1 className="mt-1 text-3xl font-semibold text-slate-950">Suppliers</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">
          S2P supplier profiles combine exception history, OTIF behavior, payment terms, and recent
          trend signals so invoice decisions can compound by counterparty.
        </p>
      </div>

      {loading ? (
        <article className="copilot-card p-5 text-sm text-slate-500">Loading preview suppliers...</article>
      ) : suppliers.length === 0 ? (
        <article className="copilot-card p-5 text-sm text-slate-500">No supplier profiles available.</article>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {suppliers.map((supplier) => {
            const exceptionRate = supplier.exception_rate ?? supplier.exceptionRate;
            const otifScore = supplier.otif_score ?? supplier.otifScore;
            const avgInvoiceAmount = supplier.avg_invoice_amount ?? supplier.avgInvoiceAmount;
            const recentTrend = supplier.recent_trend ?? supplier.recentTrend ?? "n/a";
            return (
              <article key={supplier.supplier_id ?? supplier.supplierId ?? supplier.name} className="copilot-card p-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-base font-semibold text-slate-950">{supplier.name}</h2>
                    <p className="mt-1 text-xs font-medium uppercase tracking-wide text-slate-500">
                      {supplier.category ?? "Supplier"}
                    </p>
                  </div>
                  <span className="rounded bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-800">
                    {recentTrend}
                  </span>
                </div>
                <dl className="mt-4 grid grid-cols-3 gap-3 text-sm">
                  <Stat label="Exception rate" value={formatPercent(exceptionRate)} />
                  <Stat label="OTIF" value={formatPercent(otifScore)} />
                  <Stat label="Avg invoice" value={formatCurrency(avgInvoiceAmount)} />
                </dl>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-slate-500">{label}</dt>
      <dd className="mt-1 font-semibold text-slate-950">{value}</dd>
    </div>
  );
}
