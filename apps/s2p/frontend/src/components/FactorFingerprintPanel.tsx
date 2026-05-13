import { useEffect, useState } from "react";
import { fetchS2PFingerprint } from "../api";
import { S2P_FACTORS, type FactorMap, type FingerprintResponse } from "../types";

function label(name: string) {
  return name.replace(/_/g, " ");
}

function percent(value?: number) {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "n/a";
}

export function FactorFingerprintPanel({ invoiceId }: { invoiceId?: string }) {
  const [data, setData] = useState<FingerprintResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!invoiceId) {
      setData(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    fetchS2PFingerprint(invoiceId)
      .then((response) => {
        if (!cancelled) setData(response);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [invoiceId]);

  const factors: FactorMap = data?.factors ?? {};
  const dominant = data?.dominant_factor ?? data?.dominantFactor;

  return (
    <article className="copilot-card p-5">
      <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Factor fingerprint</p>
      <h2 className="mt-1 text-xl font-semibold text-slate-950">Why this invoice was flagged</h2>
      {loading ? (
        <p className="mt-4 text-sm text-slate-500">Loading fingerprint...</p>
      ) : !invoiceId ? (
        <p className="mt-4 text-sm text-slate-500">Select an invoice to inspect its factor fingerprint.</p>
      ) : data?.error ? (
        <p className="mt-4 text-sm text-slate-500">{data.error}</p>
      ) : (
        <div className="mt-5 space-y-3">
          {S2P_FACTORS.map((factor) => {
            const value = Number(factors[factor] ?? 0);
            return (
              <div key={factor}>
                <div className="flex items-center justify-between gap-3 text-sm">
                  <span className="font-medium capitalize text-slate-700">{label(factor)}</span>
                  <span className={factor === dominant ? "font-semibold text-amber-700" : "text-slate-500"}>
                    {percent(value)}
                  </span>
                </div>
                <div className="mt-1 h-2 rounded-md bg-slate-100">
                  <div
                    className={factor === dominant ? "h-2 rounded-md bg-amber-500" : "h-2 rounded-md bg-slate-400"}
                    style={{ width: `${Math.max(3, Math.min(100, value * 100))}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </article>
  );
}
