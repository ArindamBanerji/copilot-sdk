import { useEffect, useMemo, useState } from "react";
import { fetchCorrelation } from "../api";
import type { CorrelationAlert, CorrelationPair, CorrelationResponse } from "../types";

function pct(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? `${Math.round(value * 100)}%` : "-";
}

function corrText(value: number | null | undefined): string {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(2) : "-";
}

function pairLabel(pair: CorrelationPair): string {
  return `${pair.tickerA || "-"} / ${pair.tickerB || "-"}`;
}

function badgeClass(value: number | null | undefined): string {
  const score = Math.abs(typeof value === "number" && Number.isFinite(value) ? value : 0);
  if (score > 0.8) return "border-red-300/50 bg-red-500/10 text-red-100";
  if (score >= 0.6) return "border-amber-300/50 bg-amber-500/10 text-amber-100";
  return "border-emerald-300/50 bg-emerald-500/10 text-emerald-100";
}

function alertClass(alert: CorrelationAlert): string {
  return alert.level === "critical"
    ? "border-red-300/50 bg-red-500/10 text-red-100"
    : "border-amber-300/50 bg-amber-500/10 text-amber-100";
}

function cellColor(value: number): string {
  const strength = Math.min(1, Math.abs(value));
  if (strength > 0.8) return "rgba(248, 113, 113, 0.32)";
  if (strength >= 0.6) return "rgba(251, 191, 36, 0.28)";
  return "rgba(52, 211, 153, 0.18)";
}

function Matrix({ tickers, matrix }: { tickers: string[]; matrix: number[][] }) {
  if (!tickers.length || !matrix.length || tickers.length > 8) return null;

  return (
    <div className="mt-4 overflow-x-auto">
      <div className="mb-2 text-xs uppercase tracking-wide trading-muted">Correlation matrix</div>
      <table className="min-w-full text-sm">
        <thead>
          <tr>
            <th className="p-2 text-left trading-muted">Ticker</th>
            {tickers.map((ticker) => (
              <th key={ticker} className="p-2 text-center trading-muted">
                {ticker}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {tickers.map((ticker, rowIndex) => (
            <tr key={ticker}>
              <th className="p-2 text-left font-semibold">{ticker}</th>
              {tickers.map((columnTicker, colIndex) => {
                const value = matrix[rowIndex]?.[colIndex] ?? 0;
                return (
                  <td key={`${ticker}-${columnTicker}`} className="p-1 text-center">
                    <span
                      className="inline-flex min-w-12 justify-center rounded-md px-2 py-1 text-xs font-semibold"
                      style={{ backgroundColor: cellColor(value) }}
                    >
                      {corrText(value)}
                    </span>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function CorrelationPanel() {
  const [payload, setPayload] = useState<CorrelationResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      const response = await fetchCorrelation();
      if (!cancelled) {
        setPayload(response);
        setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const tickers = useMemo(() => payload?.tickers || [], [payload]);
  const pairs = useMemo(() => payload?.pairs || [], [payload]);
  const alerts = useMemo(() => payload?.alerts || [], [payload]);
  const matrix = payload?.matrix || [];
  const insufficient = payload?.source === "insufficient_data";

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm uppercase tracking-wide trading-muted">Correlation monitoring</p>
          <h2 className="mt-1 text-xl font-semibold">Cross-Position Correlation</h2>
          <p className="mt-2 text-sm trading-muted">
            Concentration risk is estimated from recent daily return relationships across traded tickers.
          </p>
        </div>
        <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${badgeClass(payload?.avgCorrelation)}`}>
          Avg {pct(payload?.avgCorrelation)}
        </span>
      </div>

      {loading ? <div className="mt-4 text-sm trading-muted">Loading correlation monitor...</div> : null}

      {!loading && !payload ? (
        <div className="mt-4 rounded-md border border-dashed border-white/15 p-4 text-sm trading-muted">
          Correlation monitoring unavailable.
        </div>
      ) : null}

      {!loading && payload && insufficient ? (
        <div className="mt-4 rounded-md border border-dashed border-white/15 p-4 text-sm trading-muted">
          {payload.reason || "Need at least 2 tickers."}
        </div>
      ) : null}

      {!loading && payload && !insufficient ? (
        <div className="mt-4 grid gap-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
              <div className="text-xs uppercase tracking-wide trading-muted">Window</div>
              <div className="mt-1 font-semibold">{payload.windowDays ?? 20} days</div>
            </div>
            <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
              <div className="text-xs uppercase tracking-wide trading-muted">Tickers</div>
              <div className="mt-1 font-semibold">{tickers.length ? tickers.join(", ") : "-"}</div>
            </div>
            <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
              <div className="text-xs uppercase tracking-wide trading-muted">Max pair</div>
              <div className="mt-1 font-semibold">
                {payload.maxPair ? `${pairLabel(payload.maxPair)} (${corrText(payload.maxPair.correlation)})` : "-"}
              </div>
            </div>
          </div>

          <div className="rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-base font-semibold">Top correlated pairs</h3>
              <span className="text-xs trading-muted">{pairs.length} pairs</span>
            </div>
            {pairs.length ? (
              <div className="mt-3 grid gap-2">
                {pairs.slice(0, 10).map((pair) => (
                  <div key={pairLabel(pair)} className="flex flex-wrap items-center justify-between gap-2 rounded-md bg-white/5 px-3 py-2 text-sm">
                    <span className="font-semibold">{pairLabel(pair)}</span>
                    <span className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${badgeClass(pair.correlation)}`}>
                      {corrText(pair.correlation)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-2 text-sm trading-muted">No pair correlations available.</p>
            )}
          </div>

          <div className="rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
            <h3 className="text-base font-semibold">Alerts</h3>
            {alerts.length ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {alerts.map((alert, index) => (
                  <span key={`${alert.level || "alert"}-${index}`} className={`rounded-md border px-3 py-2 text-sm ${alertClass(alert)}`}>
                    {alert.message || `${alert.level || "alert"} concentration risk`}
                  </span>
                ))}
              </div>
            ) : (
              <p className="mt-2 text-sm trading-muted">No active correlation alerts.</p>
            )}
          </div>

          <Matrix tickers={tickers} matrix={matrix} />
        </div>
      ) : null}
    </section>
  );
}
