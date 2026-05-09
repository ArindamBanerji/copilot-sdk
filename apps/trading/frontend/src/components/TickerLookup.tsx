import { useState } from "react";
import { getTicker } from "../api";
import type { TickerData } from "../types";
import PriceSparkline from "./PriceSparkline";

function formatNumber(value: number | null | undefined, suffix = ""): string {
  return typeof value === "number" ? `${value.toLocaleString()}${suffix}` : "-";
}

export default function TickerLookup({
  value,
  onChange,
  onTicker,
}: {
  value: string;
  onChange: (ticker: string) => void;
  onTicker: (ticker: TickerData | undefined) => void;
}) {
  const [tickerData, setTickerData] = useState<TickerData | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function lookup() {
    if (!value.trim()) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const payload = await getTicker(value.trim());
      setTickerData(payload);
      onTicker(payload.source === "unknown" ? undefined : payload);
    } catch (lookupError) {
      setError(lookupError instanceof Error ? lookupError.message : "Ticker lookup failed");
      onTicker(undefined);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="copilot-card p-4">
      <h2 className="text-base font-semibold">Ticker</h2>
      <div className="mt-3 flex gap-2">
        <input
          className="min-w-0 flex-1 rounded-md border px-3 py-2"
          style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)" }}
          value={value}
          onChange={(event) => {
            const next = event.target.value.toUpperCase();
            onChange(next);
            setTickerData(undefined);
            onTicker(undefined);
          }}
          placeholder="MSFT"
        />
        <button type="button" className="copilot-button px-4 py-2 text-sm" onClick={lookup} disabled={loading}>
          {loading ? "..." : "Lookup"}
        </button>
      </div>
      {error ? <div className="mt-2 text-sm trading-negative">{error}</div> : null}
      {tickerData ? (
        <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_18rem]">
          <div>
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="text-lg font-semibold">{tickerData.ticker}</div>
                <div className="text-sm trading-muted">{tickerData.name || "Unknown ticker"}</div>
              </div>
              <div className="text-right">
                <div className="text-lg font-semibold">
                  {typeof tickerData.price === "number" ? `$${tickerData.price.toFixed(2)}` : "-"}
                </div>
                <div className={Number(tickerData.change30dPct) >= 0 ? "text-sm trading-positive" : "text-sm trading-negative"}>
                  {formatNumber(tickerData.change30dPct, "%")} 30d
                </div>
              </div>
            </div>
            <div className="mt-4 grid gap-2 md:grid-cols-3">
              <Metric label="Sector" value={tickerData.sector || "-"} />
              <Metric label="Above 50MA" value={tickerData.above50ma === null ? "-" : tickerData.above50ma ? "Yes" : "No"} />
              <Metric label="RSI" value={formatNumber(tickerData.rsi)} />
              <Metric label="Volume Rank" value={formatNumber(tickerData.volRankPctl, "%")} />
              <Metric label="Market Cap" value={formatNumber(tickerData.marketCapB, "B")} />
              <Metric label="Source" value={tickerData.source || "-"} />
            </div>
          </div>
          <PriceSparkline ticker={tickerData} />
        </div>
      ) : null}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border p-2" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="text-xs trading-muted">{label}</div>
      <div className="text-sm font-semibold">{value}</div>
    </div>
  );
}
