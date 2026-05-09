import type { SimilarTrade } from "../types";

function pnlClass(value: number | null | undefined): string {
  if (typeof value !== "number") {
    return "trading-muted";
  }
  return value >= 0 ? "trading-positive" : "trading-negative";
}

export default function SimilarTradesPanel({
  similar,
  count,
}: {
  similar: SimilarTrade[];
  count: number;
}) {
  const wins = similar.filter((trade) => trade.outcome === "win" || trade.isCorrect === true).length;
  return (
    <section className="copilot-card p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">Similar Trades</h2>
          <p className="text-sm trading-muted">
            {count} matches above threshold · {similar.length ? `${wins}/${similar.length} visible wins` : "no pattern yet"}
          </p>
        </div>
      </div>
      <div className="mt-4 grid gap-3">
        {similar.length === 0 ? <div className="text-sm trading-muted">No similar trades returned for this setup.</div> : null}
        {similar.map((trade) => (
          <div key={trade.tradeId || trade.ticker} className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="font-semibold">{trade.ticker || "Unknown"}</div>
                <div className="text-sm trading-muted">
                  {trade.thesisType || "thesis n/a"} · {trade.timeframe || "timeframe n/a"} · research{" "}
                  {typeof trade.researchDepth === "number" ? trade.researchDepth.toFixed(2) : "-"}
                </div>
              </div>
              <div className="text-right">
                <div className={pnlClass(trade.pnlPct)}>
                  {typeof trade.pnlPct === "number" ? `${trade.pnlPct > 0 ? "+" : ""}${trade.pnlPct.toFixed(2)}%` : "open"}
                </div>
                <div className="text-xs trading-muted">{trade.outcome || "pending"}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
