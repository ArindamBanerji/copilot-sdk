import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fetchDecliningSuppliers, fetchSupplierHistory, fetchSupplierProfiles } from "../api";
import { ClusteringPanel } from "../components/ClusteringPanel";
import { PaymentStrategyPanel } from "../components/PaymentStrategyPanel";
import { RationalizationPanel } from "../components/RationalizationPanel";
import { SupplierHeatmap } from "../components/SupplierHeatmap";
import type { SupplierHistoryEvent, SupplierProfile, SupplierProfilesResponse } from "../types";

type SourceKind = SupplierProfile["source"];

const QUARTERS = ["Q1", "Q2", "Q3", "Q4"] as const;

function supplierId(supplier?: SupplierProfile | null): string {
  return supplier?.supplier_id ?? supplier?.supplierId ?? "";
}

function supplierName(supplier?: SupplierProfile | null): string {
  return supplier?.supplier_name ?? supplier?.name ?? supplierId(supplier) ?? "Supplier";
}

function formatPercent(value: number | null | undefined): string {
  if (typeof value !== "number") return "n/a";
  return `${Math.round(value * 100)}%`;
}

function formatCurrency(value: number | null | undefined): string {
  if (typeof value !== "number") return "n/a";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function sourceLabel(source: SourceKind | string | undefined): string {
  if (source === "computed") return "Live Profiles";
  if (source === "hybrid") return "Fixture + Live";
  return "Demo Data";
}

function sourceClass(source: SourceKind | string | undefined): string {
  if (source === "computed") return "border-emerald-200 bg-emerald-50 text-emerald-800";
  if (source === "hybrid") return "border-sky-200 bg-sky-50 text-sky-800";
  return "border-slate-200 bg-slate-50 text-slate-700";
}

function trendMeta(value: number | null | undefined): { label: string; className: string; mark: string } {
  if (value === null || typeof value !== "number") {
    return { label: "Insufficient data", className: "text-slate-500", mark: "-" };
  }
  if (value > 0) {
    return { label: "Worsening", className: "text-amber-700", mark: "↑" };
  }
  if (value < 0) {
    return { label: "Improving", className: "text-emerald-700", mark: "↓" };
  }
  return { label: "Flat", className: "text-slate-600", mark: "-" };
}

function normalizeProfiles(response: SupplierProfilesResponse): SupplierProfile[] {
  return Array.isArray(response.suppliers) ? response.suppliers : [];
}

export function SuppliersScreen() {
  const [suppliers, setSuppliers] = useState<SupplierProfile[]>([]);
  const [decliningIds, setDecliningIds] = useState<Set<string>>(new Set());
  const [selectedId, setSelectedId] = useState("");
  const [history, setHistory] = useState<SupplierHistoryEvent[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const loadSuppliers = () => {
    setLoading(true);
    setError(false);
    Promise.all([
      fetchSupplierProfiles(),
      fetchDecliningSuppliers().catch(() => ({ suppliers: [], total: 0, source: "unavailable" })),
    ])
      .then(([profilesResponse, decliningResponse]) => {
        const rows = normalizeProfiles(profilesResponse);
        const declining = normalizeProfiles(decliningResponse).map(supplierId).filter(Boolean);
        setSuppliers(rows);
        setDecliningIds(new Set(declining));
        setSelectedId((current) => {
          if (current && rows.some((supplier) => supplierId(supplier) === current)) return current;
          return supplierId(rows[0]) || "";
        });
      })
      .catch(() => {
        setSuppliers([]);
        setDecliningIds(new Set());
        setError(true);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadSuppliers();
  }, []);

  const selectedSupplier = useMemo(
    () => suppliers.find((supplier) => supplierId(supplier) === selectedId) ?? suppliers[0] ?? null,
    [selectedId, suppliers],
  );
  const activeId = selectedId || supplierId(selectedSupplier);

  useEffect(() => {
    let cancelled = false;
    setHistory([]);
    setHistoryError(false);
    if (!activeId) {
      setHistoryLoading(false);
      return () => {
        cancelled = true;
      };
    }
    setHistoryLoading(true);
    fetchSupplierHistory(activeId)
      .then((response) => {
        if (!cancelled) setHistory(Array.isArray(response.events) ? response.events : []);
      })
      .catch(() => {
        if (!cancelled) setHistoryError(true);
      })
      .finally(() => {
        if (!cancelled) setHistoryLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [activeId]);

  const computedCount = suppliers.filter((supplier) => supplier.source === "computed" || supplier.source === "hybrid").length;
  const fallbackDecliningIds = useMemo(
    () =>
      new Set(
        suppliers
          .filter((supplier) => typeof supplier.exception_rate_trend === "number" && supplier.exception_rate_trend > 0)
          .map(supplierId),
      ),
    [suppliers],
  );
  const activeDecliningIds = decliningIds.size > 0 ? decliningIds : fallbackDecliningIds;

  return (
    <section data-screen-ready="true" className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Supplier memory</p>
        <h1 className="mt-1 text-3xl font-semibold text-slate-950">Suppliers</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">
          Review supplier profiles built from verified decisions, with fixture baselines preserved until live
          history is sufficient.
        </p>
      </div>

      <ClusteringPanel />
      <PaymentStrategyPanel />
      <RationalizationPanel />

      <div className="grid gap-4 xl:grid-cols-[380px_1fr]">
        <article className="copilot-card p-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Supplier list</p>
              <h2 className="mt-1 text-lg font-semibold text-slate-950">Profile source</h2>
            </div>
            {!loading && !error ? (
              <span className="rounded border border-slate-200 bg-white px-2 py-1 text-xs font-semibold text-slate-600">
                {suppliers.length} total
              </span>
            ) : null}
          </div>

          {loading ? (
            <div className="mt-4 space-y-2">
              <div className="h-20 animate-pulse rounded-md bg-slate-100" />
              <div className="h-20 animate-pulse rounded-md bg-slate-100" />
              <div className="h-20 animate-pulse rounded-md bg-slate-100" />
            </div>
          ) : error ? (
            <div className="mt-4 rounded-md border border-red-200 bg-red-50 p-3">
              <p className="text-sm font-semibold text-red-800">Unable to load supplier profiles</p>
              <button
                type="button"
                onClick={loadSuppliers}
                className="mt-3 rounded-md border border-red-200 bg-white px-3 py-1.5 text-sm font-semibold text-red-700"
              >
                Retry
              </button>
            </div>
          ) : suppliers.length === 0 ? (
            <p className="mt-4 text-sm text-slate-500">No supplier data yet. Score some invoices to build profiles.</p>
          ) : (
            <>
              <p className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-600">
                {computedCount} of {suppliers.length} suppliers have computed profiles. Others show baseline data.
              </p>
              <div className="mt-4 space-y-2">
                {suppliers.map((supplier) => {
                  const id = supplierId(supplier);
                  const selected = id === activeId;
                  const declining = activeDecliningIds.has(id);
                  return (
                    <SupplierCard
                      key={id}
                      supplier={supplier}
                      selected={selected}
                      declining={declining}
                      onSelect={() => setSelectedId(id)}
                    />
                  );
                })}
              </div>
            </>
          )}
        </article>

        <div className="space-y-4">
          <SupplierDetailPanel supplier={selectedSupplier} declining={activeDecliningIds.has(activeId)} />
          <SupplierSeasonalChart supplier={selectedSupplier} />
          <SupplierHistoryPanel events={history} loading={historyLoading} error={historyError} supplierId={activeId} />
          <SupplierHeatmap supplierId={activeId} />
        </div>
      </div>
    </section>
  );
}

function SupplierCard({
  supplier,
  selected,
  declining,
  onSelect,
}: {
  supplier: SupplierProfile;
  selected: boolean;
  declining: boolean;
  onSelect: () => void;
}) {
  const trend = trendMeta(supplier.exception_rate_trend);
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`w-full rounded-md border p-3 text-left transition ${
        selected ? "border-amber-400 bg-amber-50" : declining ? "border-amber-300 bg-white" : "border-slate-200 bg-white hover:border-amber-200"
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <span className="text-sm font-semibold text-slate-950">{supplierName(supplier)}</span>
        <span className={`rounded border px-2 py-0.5 text-[11px] font-semibold ${sourceClass(supplier.source)}`}>
          {sourceLabel(supplier.source)}
        </span>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-slate-600">
        <span>Exceptions {formatPercent(supplier.exception_rate)}</span>
        <span>OTIF {formatPercent(supplier.otif ?? supplier.otif_score ?? null)}</span>
        <span>{supplier.invoice_count ?? supplier.total_invoices ?? 0} invoices</span>
        <span className={trend.className}>
          {trend.mark} {trend.label}
        </span>
      </div>
      {declining ? (
        <span className="mt-2 inline-flex rounded border border-amber-300 bg-amber-100 px-2 py-0.5 text-[11px] font-semibold text-amber-800">
          ⚠ Declining
        </span>
      ) : null}
    </button>
  );
}

function SupplierDetailPanel({ supplier, declining }: { supplier: SupplierProfile | null; declining: boolean }) {
  if (!supplier) {
    return (
      <article className="copilot-card p-5">
        <p className="text-sm text-slate-500">Select a supplier to view profile details.</p>
      </article>
    );
  }

  const trend = trendMeta(supplier.exception_rate_trend);
  const otif = supplier.otif ?? supplier.otif_score ?? null;

  return (
    <article className={`copilot-card p-5 ${declining ? "border-amber-300" : ""}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Supplier profile</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-950">{supplierName(supplier)}</h2>
          <p className="mt-1 text-sm text-slate-500">
            {supplier.categories.length > 0 ? supplier.categories.join(", ").replace(/_/g, " ") : "No dominant category yet"}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className={`rounded border px-2 py-1 text-xs font-semibold ${sourceClass(supplier.source)}`}>
            {sourceLabel(supplier.source)}
          </span>
          {declining ? (
            <span className="rounded border border-amber-300 bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-800">
              ⚠ Declining
            </span>
          ) : null}
        </div>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-4">
        <Metric label="Exception rate" value={formatPercent(supplier.exception_rate)} />
        <Metric label="OTIF" value={formatPercent(otif)} note={supplier.source === "fixture" ? "baseline" : "fixture-backed"} />
        <Metric label="Invoices" value={supplier.invoice_count} />
        <Metric label="Avg lead time" value={supplier.avg_lead_time_days === null ? "n/a" : `${supplier.avg_lead_time_days} days`} />
      </div>

      <div className="mt-4 rounded-md border border-slate-200 bg-white p-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Exception trend</p>
        <p className={`mt-2 text-sm font-semibold ${trend.className}`}>
          {trend.mark} {trend.label}
        </p>
        <p className="mt-1 text-xs text-slate-500">
          {supplier.exception_rate_trend === null
            ? "Insufficient verified decisions for a computed trend."
            : `Slope ${supplier.exception_rate_trend.toFixed(4)} from verified invoice dates.`}
        </p>
      </div>
    </article>
  );
}

function SupplierSeasonalChart({ supplier }: { supplier: SupplierProfile | null }) {
  const leadTime = supplier?.lead_time_by_quarter ?? {};
  const otif = supplier?.otif_by_quarter ?? {};
  const mode = Object.keys(leadTime).length > 0 ? "lead" : Object.keys(otif).length > 0 ? "otif" : "empty";
  const data = QUARTERS.map((quarter): { quarter: string; value: number | null } => ({
    quarter,
    value: mode === "lead" ? leadTime[quarter] : mode === "otif" ? otif[quarter] : null,
  })).filter((row): row is { quarter: string; value: number } => typeof row.value === "number");

  return (
    <article className="copilot-card p-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Seasonality</p>
      <h2 className="mt-1 text-lg font-semibold text-slate-950">
        {mode === "lead" ? "Lead time by quarter" : mode === "otif" ? "OTIF by quarter" : "Quarterly pattern"}
      </h2>
      {!supplier ? (
        <p className="mt-4 text-sm text-slate-500">Select a supplier to view seasonal patterns.</p>
      ) : data.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">Insufficient seasonal data.</p>
      ) : (
        <>
          <div className="mt-4 h-44">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data}>
                <XAxis dataKey="quarter" tickLine={false} axisLine={false} />
                <YAxis tickLine={false} axisLine={false} width={36} />
                <Tooltip formatter={(value) => (mode === "otif" ? formatPercent(Number(value)) : `${value} days`)} />
                <Bar dataKey="value" fill="#d97706" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-2 text-sm text-slate-500">
            {mode === "lead" ? "Lead time by quarter from verified invoice metadata." : "OTIF by quarter from supplier profile data."}
          </p>
        </>
      )}
    </article>
  );
}

function SupplierHistoryPanel({
  events,
  loading,
  error,
  supplierId,
}: {
  events: SupplierHistoryEvent[];
  loading: boolean;
  error: boolean;
  supplierId: string;
}) {
  return (
    <article className="copilot-card p-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Verified decision history</p>
      <h2 className="mt-1 text-lg font-semibold text-slate-950">Accumulator events</h2>
      {!supplierId ? (
        <p className="mt-4 text-sm text-slate-500">Select a supplier to view history.</p>
      ) : loading ? (
        <p className="mt-4 text-sm text-slate-500">Loading supplier history...</p>
      ) : error ? (
        <p className="mt-4 text-sm text-slate-500">Supplier history is unavailable.</p>
      ) : events.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">No verified decisions yet for this supplier.</p>
      ) : (
        <div className="mt-4 overflow-hidden rounded-md border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-3 py-2">Invoice</th>
                <th className="px-3 py-2">Date</th>
                <th className="px-3 py-2">Category</th>
                <th className="px-3 py-2">Result</th>
                <th className="px-3 py-2">Reward</th>
                <th className="px-3 py-2">Amount</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {events.slice(0, 12).map((event, index) => (
                <tr key={`${event.invoice_id}-${index}`}>
                  <td className="px-3 py-2 font-mono text-xs text-slate-700">{event.invoice_id}</td>
                  <td className="px-3 py-2 text-slate-600">{event.invoice_date ?? "n/a"}</td>
                  <td className="px-3 py-2 text-slate-600">{event.category.replace(/_/g, " ")}</td>
                  <td className="px-3 py-2">
                    <span className={event.is_correct ? "font-semibold text-emerald-700" : "font-semibold text-amber-700"}>
                      {event.is_correct ? "Correct" : "Incorrect"}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-slate-600">{event.reward}</td>
                  <td className="px-3 py-2 text-slate-600">{formatCurrency(event.amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </article>
  );
}

function Metric({ label, value, note }: { label: string; value: string | number; note?: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-lg font-semibold text-slate-950">{value}</p>
      {note ? <p className="mt-1 text-xs text-slate-500">{note}</p> : null}
    </div>
  );
}
