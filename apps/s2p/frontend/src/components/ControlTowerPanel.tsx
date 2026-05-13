import { useEffect, useState } from "react";
import { fetchCTQueue, fetchIntents } from "../api";

type IntentRow = {
  intent_id?: string;
  name?: string;
  description?: string;
  route?: string;
  categories?: string[];
};

type QueueRow = {
  invoice_id?: string;
  intent?: string;
  intent_id?: string;
  amount?: number;
  priority?: number;
  supplier?: string;
  route?: string;
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

function label(value?: string): string {
  return value ? value.replace(/_/g, " ") : "unclassified";
}

export function ControlTowerPanel() {
  const [intents, setIntents] = useState<IntentRow[]>([]);
  const [queue, setQueue] = useState<QueueRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchIntents(), fetchCTQueue(5)])
      .then(([intentData, queueData]) => {
        if (cancelled) return;
        setIntents(ensureArray<IntentRow>((intentData as { intents?: unknown })?.intents));
        setQueue(ensureArray<QueueRow>((queueData as { queue?: unknown; items?: unknown })?.queue ?? (queueData as { items?: unknown })?.items));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Control Tower</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-950">Intent queue</h2>
        </div>
        <span className="rounded bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-800">
          {intents.length || 5} intents
        </span>
      </div>

      {loading ? (
        <p className="mt-4 text-sm text-slate-500">Loading intent queue...</p>
      ) : (
        <div className="mt-4 grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Intent types</p>
            {intents.length === 0 ? (
              <p className="mt-3 text-sm text-slate-500">Control Tower intents are unavailable.</p>
            ) : (
              <div className="mt-3 space-y-2">
                {intents.slice(0, 5).map((intent, index) => (
                  <div key={intent.intent_id ?? intent.name ?? `intent-${index}`} className="rounded-md border border-slate-200 bg-white p-3">
                    <p className="text-sm font-semibold capitalize text-slate-900">{label(intent.name ?? intent.intent_id)}</p>
                    <p className="mt-1 text-xs text-slate-500">{intent.description ?? "S2P classification intent"}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Top priority invoices</p>
            {queue.length === 0 ? (
              <p className="mt-3 text-sm text-slate-500">No prioritized invoices available.</p>
            ) : (
              <div className="mt-3 divide-y divide-slate-100">
                {queue.slice(0, 5).map((item, index) => (
                  <div key={item.invoice_id ?? `queue-${index}`} className="py-3">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <span className="font-mono text-xs font-semibold text-slate-700">{item.invoice_id ?? "invoice"}</span>
                      <span className="text-sm font-semibold text-slate-950">{formatCurrency(item.amount)}</span>
                    </div>
                    <p className="mt-1 text-xs text-slate-600">
                      {label(item.intent ?? item.intent_id)} · priority {typeof item.priority === "number" ? item.priority.toFixed(2) : "n/a"}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </article>
  );
}
