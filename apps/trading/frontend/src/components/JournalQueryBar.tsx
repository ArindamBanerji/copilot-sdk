import { useState } from "react";

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8010";

type JournalQueryResult = {
  query?: string;
  parsed?: Record<string, unknown>;
  results?: Array<Record<string, unknown>>;
  count?: number;
  summary?: string;
  warnings?: string[];
};

function label(value: unknown): string {
  return typeof value === "string" && value ? value.replace(/_/g, " ") : "-";
}

function money(value: unknown): string {
  const number = Number(value);
  if (!Number.isFinite(number)) return "-";
  return `${number < 0 ? "-" : ""}$${Math.abs(number).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function interpretation(parsed?: Record<string, unknown>): string {
  if (!parsed || Object.keys(parsed).length === 0) return "No filters applied";
  const parts: string[] = [];
  if (parsed.category) parts.push(`Category: ${label(parsed.category)}`);
  if (parsed.regime) parts.push(`Regime: ${label(parsed.regime)}`);
  if (Array.isArray(parsed.date_range)) parts.push(`Period: ${parsed.date_range.join(" to ")}`);
  if (parsed.factor && typeof parsed.factor === "object") {
    const factor = parsed.factor as Record<string, unknown>;
    parts.push(`Factor: ${label(factor.name)} ${factor.operator ?? ""} ${factor.value ?? ""}`.trim());
  }
  if (parsed.confidence_min) parts.push(`Confidence >= ${Number(parsed.confidence_min) * 100}%`);
  if (parsed.performance) parts.push(`Sort: ${label(parsed.performance)}`);
  return parts.join(", ");
}

export default function JournalQueryBar() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<JournalQueryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${BASE}/api/trading/journal/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!response.ok) throw new Error(`Journal query failed with ${response.status}`);
      setResult(await response.json());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Journal query unavailable");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="copilot-card p-4" data-testid="journal-query-bar">
      <div className="flex flex-wrap items-end gap-3">
        <label className="min-w-[260px] flex-1 text-sm">
          <span className="trading-muted">Ask your journal</span>
          <input
            className="mt-1 w-full rounded-md border bg-transparent px-3 py-2"
            style={{ borderColor: "var(--copilot-border)" }}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") void submit();
            }}
            placeholder="Ask your journal..."
          />
        </label>
        <button
          className="rounded-md px-4 py-2 text-sm font-semibold text-white"
          style={{ background: "var(--copilot-accent)" }}
          type="button"
          onClick={() => void submit()}
          disabled={loading}
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {error ? <p className="mt-3 text-sm trading-negative">{error}</p> : null}
      {result ? (
        <div className="mt-4">
          <p className="text-sm font-semibold">{result.summary ?? "Journal query complete."}</p>
          <p className="mt-1 text-sm trading-muted">{interpretation(result.parsed)}</p>
          {result.warnings?.length ? <p className="mt-1 text-sm trading-muted">{result.warnings[0]}</p> : null}
          {Number(result.count ?? 0) === 0 ? (
            <p className="mt-3 rounded-md p-3 text-sm trading-muted" style={{ background: "var(--copilot-surface-muted)" }}>
              No trades match your query
            </p>
          ) : (
            <div className="mt-3 overflow-x-auto">
              <table className="w-full min-w-[640px] text-left text-sm">
                <thead className="trading-muted">
                  <tr>
                    <th className="py-2 pr-3 font-medium">Date</th>
                    <th className="py-2 pr-3 font-medium">Ticker</th>
                    <th className="py-2 pr-3 font-medium">Category</th>
                    <th className="py-2 pr-3 font-medium">Regime</th>
                    <th className="py-2 pr-3 font-medium">P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {(result.results ?? []).slice(0, 8).map((trade, index) => (
                    <tr key={String(trade.trade_id ?? trade.tradeId ?? index)} className="border-t" style={{ borderColor: "var(--copilot-border)" }}>
                      <td className="py-2 pr-3">{String(trade.entry_time ?? trade.entryTime ?? "-").slice(0, 10)}</td>
                      <td className="py-2 pr-3 font-semibold">{String(trade.ticker ?? "-")}</td>
                      <td className="py-2 pr-3 capitalize">{label(trade.category)}</td>
                      <td className="py-2 pr-3 capitalize">{label(trade.regime)}</td>
                      <td className="py-2 pr-3">{money(trade.pnl)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {Number(result.count ?? 0) > 8 ? (
                <p className="mt-2 text-sm trading-muted">Showing 8 of {result.count} results</p>
              ) : null}
            </div>
          )}
        </div>
      ) : null}
    </section>
  );
}
