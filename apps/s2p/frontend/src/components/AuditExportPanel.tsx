import { useState } from "react";
import { getAuditPack } from "../api";
import type { AuditPackResponse } from "../types";

function formatDate(value?: string): string {
  if (!value) return "n/a";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function formatNumber(value?: number): string {
  return typeof value === "number" ? value.toLocaleString() : "n/a";
}

export function AuditExportPanel() {
  const [data, setData] = useState<AuditPackResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function generateAuditPack() {
    setLoading(true);
    setError("");
    getAuditPack()
      .then((response) => {
        if (!response) {
          setError("Audit pack is unavailable.");
          return;
        }
        setData(response);
      })
      .catch(() => {
        setError("Audit pack is unavailable.");
      })
      .finally(() => setLoading(false));
  }

  const overrideReasons = Object.entries(data?.override_distribution ?? {});

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">SOX export</p>
          <h2 className="mt-1 text-xl font-semibold text-slate-950">Audit Export</h2>
        </div>
        <button
          type="button"
          onClick={generateAuditPack}
          disabled={loading}
          className="rounded-md bg-amber-600 px-4 py-2 text-sm font-semibold text-white shadow-sm disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {loading ? "Generating..." : "Generate Audit Pack"}
        </button>
      </div>

      {error ? <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}

      {!data && !loading && !error ? (
        <p className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-500">
          Generate an audit pack to inspect receipt integrity, conservation state, and override distribution.
        </p>
      ) : null}

      {data ? (
        <>
          <div className="mt-4 grid gap-3 sm:grid-cols-4">
            <Metric label="Receipt count" value={formatNumber(data.receipt_count)} />
            <Metric label="Confirms" value={formatNumber(data.confirm_count)} />
            <Metric label="Overrides" value={formatNumber(data.override_count)} />
            <Metric label="Chain integrity" value={data.chain_integrity?.verified ? "Valid" : "Review"} />
          </div>

          <div className="mt-4 rounded-md border border-slate-200 bg-white p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Export timestamp</p>
            <p className="mt-1 text-sm font-semibold text-slate-900">{formatDate(data.export_timestamp)}</p>
          </div>

          {overrideReasons.length > 0 ? (
            <div className="mt-4 rounded-md border border-slate-200 bg-white p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Override distribution</p>
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                {overrideReasons.map(([reason, count]) => (
                  <div key={reason} className="flex items-center justify-between rounded-md bg-slate-50 px-3 py-2">
                    <span className="text-sm capitalize text-slate-700">{reason.replace(/_/g, " ")}</span>
                    <span className="text-sm font-semibold text-slate-950">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-500">
              No override reasons are present in the current audit pack.
            </p>
          )}
        </>
      ) : null}
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-lg font-semibold text-slate-950">{value}</p>
    </div>
  );
}
