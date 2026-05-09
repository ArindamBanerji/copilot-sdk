import type { PortfolioSummaryData } from "../types";

function money(value: number | null | undefined): string {
  if (typeof value !== "number") {
    return "-";
  }
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

function pct(value: number | null | undefined): string {
  if (typeof value !== "number") {
    return "-";
  }
  return `${(value * 100).toFixed(value > 1 ? 1 : 0)}%`;
}

export default function PortfolioSummary({ summary }: { summary?: PortfolioSummaryData }) {
  const stats = [
    { label: "Open Positions", value: String(summary?.openPositions ?? 0) },
    { label: "Open Exposure", value: money(summary?.openExposureDollars), sub: pct(summary?.openExposurePct) },
    { label: "Closed Trades", value: String(summary?.closedTrades ?? 0) },
    { label: "Win Rate", value: pct(summary?.winRate) },
    { label: "YTD Return", value: pct(summary?.ytdReturnPct) },
  ];

  return (
    <section className="copilot-card p-4">
      <div className="mb-4">
        <h2 className="text-base font-semibold">Portfolio Summary</h2>
        <p className="text-sm trading-muted">Open risk and closed-trade quality</p>
      </div>
      <div className="trading-grid trading-grid-4">
        {stats.map((stat) => (
          <div key={stat.label} className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
            <div className="text-xs trading-muted">{stat.label}</div>
            <div className="trading-stat-value">{stat.value}</div>
            {stat.sub ? <div className="text-xs trading-muted">{stat.sub}</div> : null}
          </div>
        ))}
      </div>
    </section>
  );
}
