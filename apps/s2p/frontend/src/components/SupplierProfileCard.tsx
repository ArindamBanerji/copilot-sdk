import { useEffect, useState } from "react";
import { fetchSupplierProfile } from "../api";
import { ProvenanceBadge } from "./ProvenanceBadge";

type RecentInvoice = {
  invoice_id?: string;
  amount?: number;
  category?: string;
  ground_truth_action?: string;
};

type SupplierProfileResponse = {
  supplier_id?: string;
  name?: string;
  otif_score?: number;
  exception_rate?: number;
  otif_trend?: number[];
  exception_trend?: number[];
  behavioral_cluster?: string;
  risk_level?: string;
  recent_invoices?: RecentInvoice[];
};

function ensureArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

function formatCurrency(value?: number): string {
  if (typeof value !== "number") return "n/a";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPct(value?: number): string {
  if (typeof value !== "number") return "n/a";
  return `${Math.round(value * 100)}%`;
}

export function SupplierProfileCard({ supplierId }: { supplierId?: string }) {
  const [profile, setProfile] = useState<SupplierProfileResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    if (!supplierId) {
      setProfile(null);
      return () => {
        cancelled = true;
      };
    }
    setLoading(true);
    fetchSupplierProfile(supplierId)
      .then((response) => {
        if (!cancelled) setProfile((response as SupplierProfileResponse | null) ?? null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [supplierId]);

  const recentInvoices = ensureArray<RecentInvoice>(profile?.recent_invoices);
  const otifTrend = ensureArray<number>(profile?.otif_trend);
  const exceptionTrend = ensureArray<number>(profile?.exception_trend);

  return (
    <article className="copilot-card p-5">
      <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Supplier profile</p>
      {!supplierId ? (
        <p className="mt-4 text-sm text-slate-500">Select a supplier to view profile details.</p>
      ) : loading ? (
        <p className="mt-4 text-sm text-slate-500">Loading supplier profile...</p>
      ) : !profile ? (
        <p className="mt-4 text-sm text-slate-500">Supplier profile is unavailable.</p>
      ) : (
        <>
          <div className="mt-2 flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-slate-950">{profile.name ?? supplierId}</h2>
              <p className="mt-1 text-sm text-slate-500">{profile.behavioral_cluster ?? "Supplier cohort"} · risk {profile.risk_level ?? "n/a"}</p>
            </div>
            <span className="rounded bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-800">{profile.supplier_id ?? supplierId}</span>
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <Metric label="OTIF score" value={formatPct(profile.otif_score)} provenance="sample" />
            <Metric label="Exception rate" value={formatPct(profile.exception_rate)} />
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <Trend label="OTIF trend" values={otifTrend} />
            <Trend label="Exception trend" values={exceptionTrend} />
          </div>
          <div className="mt-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Recent invoices</p>
            {recentInvoices.length === 0 ? (
              <p className="mt-2 text-sm text-slate-500">No recent invoices for this supplier.</p>
            ) : (
              <div className="mt-2 divide-y divide-slate-100">
                {recentInvoices.map((invoice, index) => (
                  <div key={invoice.invoice_id ?? `invoice-${index}`} className="py-2 text-sm">
                    <div className="flex flex-wrap justify-between gap-3">
                      <span className="font-mono text-xs font-semibold text-slate-700">{invoice.invoice_id ?? "invoice"}</span>
                      <span className="font-semibold text-slate-950">{formatCurrency(invoice.amount)}</span>
                    </div>
                    <p className="mt-1 text-xs text-slate-500">{invoice.category ?? "uncategorized"}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </article>
  );
}

function Metric({ label, value, provenance }: { label: string; value: string; provenance?: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
        {provenance ? <ProvenanceBadge source={provenance} /> : null}
      </div>
      <p className="mt-2 text-lg font-semibold text-slate-950">{value}</p>
    </div>
  );
}

function Trend({ label, values }: { label: string; values: number[] }) {
  return (
    <div>
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
        <ProvenanceBadge source="real_measured" />
      </div>
      <div className="mt-2 flex h-10 items-end gap-1">
        {values.length === 0 ? (
          <span className="text-sm text-slate-500">n/a</span>
        ) : (
          values.map((value, index) => (
            <span
              key={`${label}-${index}`}
              className="block w-4 rounded-t bg-amber-500"
              style={{ height: `${Math.max(6, Math.round(value * 40))}px` }}
              title={`${Math.round(value * 100)}%`}
            />
          ))
        )}
      </div>
    </div>
  );
}
