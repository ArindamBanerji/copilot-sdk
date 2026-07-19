import { useEffect, useState } from "react";
import { fetchWebhookStatus } from "../api";
import type { WebhookStatusResponse } from "../api";

function pct(value: number | null | undefined): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "-";
}

function signalLabel(status: WebhookStatusResponse | null): string {
  const last = status?.lastAlert;
  if (!last) return "No signals received yet";
  const ticker = last.ticker || "Unknown";
  const signal = last.signalType || last.action || "signal";
  const when = status?.lastReceived || "recently";
  return `${ticker} ${signal} at ${when}`;
}

function speedNarrative(status: WebhookStatusResponse | null): string {
  if (typeof status?.fastAccuracy !== "number" && typeof status?.slowAccuracy !== "number") {
    return "Awaiting signal-trade correlation data.";
  }
  return `Fast entry (<5min): ${pct(status.fastAccuracy)} accuracy. Slow (>30min): ${pct(status.slowAccuracy)}.`;
}

export default function WebhookStatusCard() {
  const [status, setStatus] = useState<WebhookStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchWebhookStatus()
      .then((payload) => {
        if (!cancelled) setStatus(payload);
      })
      .catch((loadError) => {
        console.debug("webhook status unavailable", loadError);
        if (!cancelled) setError("Webhook status unavailable.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="copilot-card p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">Signal Integration</h2>
          <p className="mt-1 text-sm trading-muted">TradingView signal health and signal-to-trade correlation.</p>
        </div>
        <span className="rounded-md border px-3 py-1 text-xs uppercase" style={{ borderColor: "var(--copilot-border)" }}>
          {status?.health || "waiting"}
        </span>
      </div>

      {loading ? <p className="mt-4 text-sm trading-muted">Loading signal status...</p> : null}
      {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}
      {!loading && !error ? (
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
            <div className="text-xs trading-muted">Last alert</div>
            <div className="mt-1 text-sm font-medium">{signalLabel(status)}</div>
          </div>
          <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
            <div className="text-xs trading-muted">Signal-to-trade stats</div>
            <div className="mt-1 text-sm">
              {status?.totalAlerts ?? 0} alerts received. {status?.correlatedTrades ?? 0} correlated to trades.
            </div>
          </div>
          <div className="rounded-md border p-3 md:col-span-2" style={{ borderColor: "var(--copilot-border)" }}>
            <div className="text-xs trading-muted">Accuracy by speed</div>
            <div className="mt-1 text-sm">{speedNarrative(status)}</div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
