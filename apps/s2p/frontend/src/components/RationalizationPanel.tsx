import { useEffect, useState } from "react";
import { getRationalizationRecs } from "../api";
import type { RationalizationResponse, SupplierRecommendation } from "../types";

function formatCurrency(value?: number, currency = "USD"): string {
  if (typeof value !== "number") return "n/a";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}

function percent(value?: number): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "n/a";
}

function label(value: string): string {
  return value.replace(/_/g, " ");
}

function recommendationClass(value: string): string {
  if (value === "grow") return "border-emerald-200 bg-emerald-50 text-emerald-700";
  if (value === "phase_out") return "border-red-200 bg-red-50 text-red-700";
  return "border-sky-200 bg-sky-50 text-sky-700";
}

export function RationalizationPanel() {
  const [data, setData] = useState<RationalizationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    getRationalizationRecs()
      .then((response) => {
        if (cancelled) return;
        if (!response) {
          setError("Supplier rationalization is unavailable.");
          setData(null);
          return;
        }
        setData(response);
      })
      .catch(() => {
        if (!cancelled) {
          setError("Supplier rationalization is unavailable.");
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

  const recommendations = data?.recommendations ?? [];
  const currency = data?.estimated_savings?.currency ?? "USD";

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Supplier portfolio</p>
          <h2 className="mt-1 text-xl font-semibold text-slate-950">Supplier Rationalization</h2>
        </div>
        {loading ? <span className="text-sm text-slate-500">Loading recommendations...</span> : null}
      </div>

      {error ? <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}

      {!loading && !error && recommendations.length === 0 ? (
        <p className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-500">
          No supplier rationalization recommendations are available.
        </p>
      ) : null}

      {!loading && !error && data && recommendations.length > 0 ? (
        <>
          <div className="mt-4 grid gap-3 sm:grid-cols-5">
            <Metric label="Grow" value={data.grow} className="text-emerald-700" />
            <Metric label="Maintain" value={data.maintain} className="text-sky-700" />
            <Metric label="Phase out" value={data.phase_out} className="text-red-700" />
            <Metric label="Quarterly savings" value={formatCurrency(data.estimated_savings.estimated_quarterly_savings, currency)} />
            <Metric label="Annual savings" value={formatCurrency(data.estimated_savings.estimated_annual_savings, currency)} />
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {recommendations.map((recommendation) => (
              <RecommendationCard key={recommendation.supplier_id} recommendation={recommendation} />
            ))}
          </div>
        </>
      ) : null}
    </article>
  );
}

function RecommendationCard({ recommendation }: { recommendation: SupplierRecommendation }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-mono text-xs font-semibold text-slate-500">{recommendation.supplier_id}</p>
          <h3 className="mt-1 text-sm font-semibold text-slate-950">{recommendation.name}</h3>
          <p className="mt-1 text-xs text-slate-500">{recommendation.region || "unknown"}</p>
        </div>
        <span className={`rounded border px-2 py-1 text-xs font-semibold ${recommendationClass(recommendation.recommendation)}`}>
          {label(recommendation.recommendation)}
        </span>
      </div>

      <div className="mt-3 grid grid-cols-3 gap-2 text-sm">
        <span className="rounded bg-slate-50 p-2 text-slate-600">
          OTIF <strong className="block text-slate-950">{percent(recommendation.otif)}</strong>
        </span>
        <span className="rounded bg-slate-50 p-2 text-slate-600">
          Exceptions <strong className="block text-slate-950">{percent(recommendation.exception_rate)}</strong>
        </span>
        <span className="rounded bg-slate-50 p-2 text-slate-600">
          Invoices <strong className="block text-slate-950">{recommendation.total_invoices ?? "n/a"}</strong>
        </span>
      </div>

      <p className="mt-3 text-sm text-slate-600">{recommendation.reason}</p>
      <p className="mt-2 rounded-md bg-slate-50 p-2 text-sm font-medium text-slate-700">{recommendation.action}</p>
    </div>
  );
}

function Metric({
  label,
  value,
  className = "text-slate-950",
}: {
  label: string;
  value: string | number;
  className?: string;
}) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-2 text-lg font-semibold ${className}`}>{value}</p>
    </div>
  );
}
