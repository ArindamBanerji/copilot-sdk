import type { MetricBreakdown } from "../types";

export default function PortfolioConcentration({
  concentration,
  categoryCounts,
}: {
  concentration?: Record<string, MetricBreakdown>;
  categoryCounts?: Record<string, number>;
}) {
  const entries = Object.entries(concentration || {}).length
    ? Object.entries(concentration || {}).map(([name, value]) => ({ name, count: value.count ?? 0, detail: value }))
    : Object.entries(categoryCounts || {}).map(([name, count]) => ({ name, count, detail: undefined }));
  const max = Math.max(1, ...entries.map((item) => item.count));

  return (
    <section className="copilot-card p-4">
      <h2 className="text-base font-semibold">Portfolio Concentration</h2>
      <div className="mt-4 flex flex-col gap-3">
        {entries.length === 0 ? <div className="text-sm trading-muted">No category data available.</div> : null}
        {entries.map((entry) => (
          <div key={entry.name}>
            <div className="mb-1 flex items-center justify-between text-sm">
              <span>{entry.name.replace(/_/g, " ")}</span>
              <span className="trading-muted">{entry.count} trades</span>
            </div>
            <div className="trading-bar-track">
              <div className="trading-bar-fill" style={{ width: `${(entry.count / max) * 100}%` }} />
            </div>
            {typeof entry.detail?.pnlDollars === "number" ? (
              <div className="mt-1 text-xs trading-muted">P&L ${entry.detail.pnlDollars.toLocaleString()}</div>
            ) : null}
          </div>
        ))}
      </div>
    </section>
  );
}
