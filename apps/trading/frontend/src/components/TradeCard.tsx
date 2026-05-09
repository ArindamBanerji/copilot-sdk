import type { JoinedTrade } from "../types";

function money(value: number | null | undefined): string {
  return typeof value === "number" ? `$${value.toLocaleString()}` : "-";
}

function pct(value: number | null | undefined): string {
  return typeof value === "number" ? `${value > 0 ? "+" : ""}${value.toFixed(2)}%` : "open";
}

function dots(value: number | null | undefined, count = 5) {
  const filled = Math.round(Math.max(0, Math.min(1, Number(value) || 0)) * count);
  return Array.from({ length: count }, (_, index) => (
    <span
      key={index}
      className="inline-block h-2 w-2 rounded-full"
      style={{ background: index < filled ? "var(--copilot-primary)" : "var(--copilot-surface-muted)" }}
    />
  ));
}

function livePnl(trade: JoinedTrade): number | null {
  if (typeof trade.exitPrice === "number" || typeof trade.tickerData?.price !== "number" || typeof trade.entryPrice !== "number") {
    return null;
  }
  return ((trade.tickerData.price - trade.entryPrice) / trade.entryPrice) * 100;
}

export default function TradeCard({ trade, onClick }: { trade: JoinedTrade; onClick: () => void }) {
  const openPnl = livePnl(trade);
  const displayPnl = openPnl ?? trade.pnlPct;
  const isPositive = typeof displayPnl === "number" && displayPnl >= 0;
  const checklist = trade.researchChecklist || [];
  const researchDepth = checklist.length ? checklist.filter(Boolean).length / checklist.length : trade.researchDepth;

  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full rounded-md border p-4 text-left transition hover:shadow-sm"
      style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface)" }}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-semibold">{trade.ticker || "Unknown"}</span>
            <span className="rounded px-2 py-1 text-xs font-semibold" style={{ background: "var(--copilot-surface-muted)" }}>
              {trade.direction || trade.scoreAction || trade.actionTaken || "trade"}
            </span>
          </div>
          <div className="mt-1 text-sm trading-muted">
            {trade.thesisType || trade.category || "unclassified"} · {trade.timeframe || "timeframe n/a"}
          </div>
        </div>
        <div className="text-right">
          <div className={isPositive ? "text-lg font-semibold trading-positive" : "text-lg font-semibold trading-negative"}>
            {pct(displayPnl)}
          </div>
          <div className="text-sm trading-muted">{money(trade.pnlDollars)}</div>
        </div>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-4">
        <div>
          <div className="text-xs trading-muted">Hold</div>
          <div className="text-sm font-semibold">{typeof trade.holdDays === "number" ? `${trade.holdDays}d` : "open"}</div>
        </div>
        <div>
          <div className="text-xs trading-muted">R:R</div>
          <div className="text-sm font-semibold">{typeof trade.rrRatio === "number" ? trade.rrRatio.toFixed(2) : "-"}</div>
        </div>
        <div>
          <div className="text-xs trading-muted">Research</div>
          <div className="mt-1 flex gap-1">{dots(researchDepth)}</div>
        </div>
        <div>
          <div className="text-xs trading-muted">Conviction</div>
          <div className="mt-1 flex gap-1">{dots(trade.conviction)}</div>
        </div>
      </div>
    </button>
  );
}
