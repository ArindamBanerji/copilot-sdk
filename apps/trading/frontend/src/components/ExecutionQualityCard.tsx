import { useEffect, useState } from "react";
import { fetchExecutionAnalysis } from "../api";
import type { ExecutionSummaryResponse } from "../api";

function money(value: number | null | undefined): string {
  return typeof value === "number" ? `$${Math.round(value).toLocaleString()}` : "$0";
}

function pct(value: number | null | undefined): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "-";
}

function slippage(value: number | null | undefined): string {
  return typeof value === "number" ? value.toFixed(3) : "-";
}

export default function ExecutionQualityCard() {
  const [summary, setSummary] = useState<ExecutionSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchExecutionAnalysis()
      .then((payload) => {
        if (!cancelled) setSummary(payload);
      })
      .catch((loadError) => {
        console.debug("execution quality unavailable", loadError);
        if (!cancelled) setError("Execution quality unavailable.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const brokers = summary?.brokers ?? [];

  return (
    <section className="copilot-card p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">Execution Quality</h2>
          <p className="mt-1 text-sm trading-muted">Broker fill quality, slippage, and savings estimate.</p>
        </div>
        {summary?.bestBroker ? (
          <div className="rounded-md border px-3 py-2 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
            Best broker: <span className="font-semibold">{summary.bestBroker}</span>
          </div>
        ) : null}
      </div>

      {loading ? <p className="mt-4 text-sm trading-muted">Loading execution data...</p> : null}
      {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}
      {!loading && !error && brokers.length === 0 ? (
        <p className="mt-4 text-sm trading-muted">No execution data yet</p>
      ) : null}

      {brokers.length > 0 ? (
        <>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="trading-muted">
                <tr>
                  <th className="py-2 pr-4 font-medium">Broker</th>
                  <th className="py-2 pr-4 font-medium">Trades</th>
                  <th className="py-2 pr-4 font-medium">Avg slippage</th>
                  <th className="py-2 pr-4 font-medium">Fill rate</th>
                </tr>
              </thead>
              <tbody>
                {brokers.map((broker) => (
                  <tr key={broker.broker || "unknown"} className="border-t" style={{ borderColor: "var(--copilot-border)" }}>
                    <td className="py-2 pr-4 font-medium">{broker.broker || "unknown"}</td>
                    <td className="py-2 pr-4">{broker.tradeCount ?? 0}</td>
                    <td className="py-2 pr-4">{slippage(broker.avgSlippage)}</td>
                    <td className="py-2 pr-4">{pct(broker.fillRate)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-4 rounded-md border p-3 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
            <div className="font-semibold">Annual savings estimate: {money(summary?.annualSavingsEstimate)}</div>
            <div className="mt-1 trading-muted">{summary?.recommendation || "Track more broker fills to estimate savings."}</div>
          </div>
        </>
      ) : null}
    </section>
  );
}
