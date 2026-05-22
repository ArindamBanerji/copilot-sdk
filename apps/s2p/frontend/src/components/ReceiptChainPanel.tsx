import { useEffect, useState } from "react";
import { getChainIntegrity, getReceipts } from "../api";
import type { ChainIntegrityResponse, ReceiptsResponse } from "../types";

function percent(value?: number): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "n/a";
}

function formatAction(value?: string): string {
  return value ? value.replace(/_/g, " ") : "n/a";
}

function formatNumber(value?: number): string {
  return typeof value === "number" ? value.toLocaleString() : "n/a";
}

export function ReceiptChainPanel() {
  const [data, setData] = useState<ReceiptsResponse | null>(null);
  const [chain, setChain] = useState<ChainIntegrityResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    Promise.all([getReceipts(20), getChainIntegrity()])
      .then(([receiptsResponse, chainResponse]) => {
        if (cancelled) return;
        if (!receiptsResponse || !chainResponse) {
          setError("Outcome receipt chain is unavailable.");
          setData(receiptsResponse);
          setChain(chainResponse);
          return;
        }
        setData(receiptsResponse);
        setChain(chainResponse);
      })
      .catch(() => {
        if (!cancelled) {
          setError("Outcome receipt chain is unavailable.");
          setData(null);
          setChain(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const receipts = data?.receipts ?? [];
  const stats = data?.stats;

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Outcome evidence</p>
          <h2 className="mt-1 text-xl font-semibold text-slate-950">Outcome Receipt Chain</h2>
        </div>
        {loading ? <span className="text-sm text-slate-500">Loading receipt chain...</span> : null}
      </div>

      {error ? <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}

      {!loading && !error && data ? (
        <>
          <div className="mt-4 grid gap-3 sm:grid-cols-4">
            <Metric label="Total receipts" value={formatNumber(stats?.total_receipts)} />
            <Metric label="Confirms" value={formatNumber(stats?.confirms)} />
            <Metric label="Overrides" value={`${formatNumber(stats?.overrides)} (${percent(stats?.override_rate)})`} />
            <Metric label="Chain validity" value={chain?.verified ?? stats?.chain_valid ? "Valid" : "Review"} />
          </div>

          {receipts.length === 0 ? (
            <p className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-500">
              No outcome receipts have been recorded yet.
            </p>
          ) : (
            <div className="mt-4 divide-y divide-slate-100 rounded-md border border-slate-200 bg-white">
              {receipts.map((receipt) => (
                <div key={receipt.receipt_id} className="p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="font-mono text-xs font-semibold text-slate-700">{receipt.invoice_id}</p>
                      <p className="mt-1 text-sm capitalize text-slate-700">
                        {formatAction(receipt.scored_action)} to {formatAction(receipt.human_action)}
                      </p>
                    </div>
                    <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
                      {formatNumber(receipt.reward)}
                    </span>
                  </div>
                  <div className="mt-3 grid gap-2 text-xs text-slate-500 sm:grid-cols-3">
                    <span>{receipt.category || "uncategorized"}</span>
                    <span>{percent(receipt.confidence)} confidence</span>
                    <span className="font-mono">{receipt.receipt_hash || "no hash"}</span>
                  </div>
                </div>
              ))}
            </div>
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
