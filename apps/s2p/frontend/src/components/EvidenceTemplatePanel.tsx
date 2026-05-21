import { useEffect, useMemo, useState } from "react";
import { getEvidenceTemplate } from "../api";
import type { EvidenceTemplateResponse } from "../types";

function label(name: string): string {
  return name.replace(/_/g, " ");
}

function valueText(value: unknown): string {
  if (value === null || value === undefined || value === "") return "N/A";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(2);
  return String(value);
}

export function EvidenceTemplatePanel({
  invoiceId,
  category
}: {
  invoiceId?: string;
  category?: string;
}) {
  const [data, setData] = useState<EvidenceTemplateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!invoiceId || !category) {
      setData(null);
      setError("");
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError("");
    getEvidenceTemplate(invoiceId, category)
      .then((response) => {
        if (cancelled) return;
        if (response) {
          setData(response);
        } else {
          setData(null);
          setError("Evidence template is unavailable.");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setData(null);
          setError("Evidence template is unavailable.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [invoiceId, category]);

  const highlights = useMemo(() => {
    const entries = Object.entries(data?.variables ?? {}).filter(([, value]) => valueText(value) !== "N/A");
    return entries.slice(0, 5);
  }, [data]);

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Evidence template</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-950">Category explanation</h2>
        </div>
        {data?.category ? (
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
            {label(data.category)}
          </span>
        ) : null}
      </div>

      {loading ? (
        <p className="mt-4 text-sm text-slate-500">Loading evidence...</p>
      ) : !invoiceId ? (
        <p className="mt-4 text-sm text-slate-500">Select an invoice to load its evidence template.</p>
      ) : error ? (
        <p className="mt-4 text-sm text-slate-500">{error}</p>
      ) : data ? (
        <>
          <p className="mt-4 rounded-md border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-slate-800">
            {data.rendered}
          </p>
          {highlights.length > 0 ? (
            <div className="mt-4 flex flex-wrap gap-2">
              {highlights.map(([name, value]) => (
                <span
                  key={name}
                  className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-700"
                >
                  {label(name)}: <span className="font-semibold text-slate-950">{valueText(value)}</span>
                </span>
              ))}
            </div>
          ) : null}
        </>
      ) : (
        <p className="mt-4 text-sm text-slate-500">No evidence template available.</p>
      )}
    </article>
  );
}
