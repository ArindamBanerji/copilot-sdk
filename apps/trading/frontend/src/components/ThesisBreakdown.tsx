import type { MetricBreakdown } from "../types";

function formatRate(value: number | null | undefined): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "-";
}

export default function ThesisBreakdown({ breakdown }: { breakdown?: Record<string, MetricBreakdown> }) {
  const entries = Object.entries(breakdown || {}).sort((a, b) => (b[1].count ?? 0) - (a[1].count ?? 0));
  const max = Math.max(1, ...entries.map(([, value]) => value.count ?? 0));

  return (
    <section className="copilot-card p-4">
      <h2 className="text-base font-semibold">Thesis Breakdown</h2>
      <div className="mt-4 flex flex-col gap-3">
        {entries.length === 0 ? <div className="text-sm trading-muted">No thesis data available.</div> : null}
        {entries.map(([name, value]) => (
          <div key={name}>
            <div className="mb-1 flex items-center justify-between text-sm">
              <span>{name.replace(/_/g, " ")}</span>
              <span className="trading-muted">{formatRate(value.winRate)} win rate</span>
            </div>
            <div className="trading-bar-track">
              <div className="trading-bar-fill" style={{ width: `${((value.count ?? 0) / max) * 100}%` }} />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
