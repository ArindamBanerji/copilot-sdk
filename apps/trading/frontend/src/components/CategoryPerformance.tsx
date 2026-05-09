import type { Analytics, MetricBreakdown } from "../types";

function pct(value: number | null | undefined): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "-";
}

function money(value: number | null | undefined): string {
  return typeof value === "number" ? `$${value.toLocaleString()}` : "-";
}

export default function CategoryPerformance({ analytics }: { analytics?: Analytics }) {
  const concentration = analytics?.portfolioConcentration || {};
  const counts = analytics?.categoryCounts || {};
  const keys = Array.from(new Set([...Object.keys(counts), ...Object.keys(concentration)]));

  return (
    <section className="copilot-card p-4">
      <h2 className="text-base font-semibold">Category Performance</h2>
      <div className="mt-4 grid gap-3">
        {keys.length ? keys.map((key) => <Row key={key} name={key} metric={concentration[key]} count={counts[key]} />) : (
          <div className="rounded-md p-4 text-sm trading-muted" style={{ background: "var(--copilot-surface-muted)" }}>
            No category performance available.
          </div>
        )}
      </div>
    </section>
  );
}

function Row({ name, metric, count }: { name: string; metric?: MetricBreakdown; count?: number }) {
  const width = Math.max(0, Math.min(100, (metric?.winRate ?? 0) * 100));
  return (
    <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="font-semibold">{name.replace(/_/g, " ")}</div>
        <div className="text-sm trading-muted">{count ?? metric?.count ?? 0} trades</div>
      </div>
      <div className="mt-3 trading-bar-track">
        <div className="trading-bar-fill" style={{ width: `${width}%` }} />
      </div>
      <div className="mt-2 flex justify-between text-sm">
        <span>{pct(metric?.winRate)} win rate</span>
        <span>{money(metric?.pnlDollars)}</span>
      </div>
    </div>
  );
}
