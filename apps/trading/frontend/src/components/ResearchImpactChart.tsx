import type { Analytics, MetricBreakdown } from "../types";

function pct(value: number | null | undefined): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "-";
}

export default function ResearchImpactChart({ analytics }: { analytics?: Analytics }) {
  const buckets = analytics?.researchImpact?.buckets || {};
  const rows = [1, 2, 3, 4, 5].map((count) => ({
    label: `${count}/5`,
    value: buckets[`checklist_${count}`],
  }));

  return (
    <section className="copilot-card p-4">
      <h2 className="text-base font-semibold">Research Impact</h2>
      <p className="mt-1 text-sm trading-muted">Checklist completion versus closed-trade win rate.</p>
      <div className="mt-4 grid gap-3">
        {rows.some((row) => row.value) ? rows.map((row) => <Bar key={row.label} label={row.label} value={row.value} />) : (
          <div className="rounded-md p-4 text-sm trading-muted" style={{ background: "var(--copilot-surface-muted)" }}>
            No research bucket data available.
          </div>
        )}
      </div>
    </section>
  );
}

function Bar({ label, value }: { label: string; value?: MetricBreakdown }) {
  const width = Math.max(0, Math.min(100, (value?.winRate ?? 0) * 100));
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm">
        <span>{label}</span>
        <span className="font-semibold">{pct(value?.winRate)}</span>
      </div>
      <div className="trading-bar-track">
        <div className="trading-bar-fill" style={{ width: `${width}%` }} />
      </div>
      <div className="mt-1 text-xs trading-muted">{value?.count ?? 0} trades</div>
    </div>
  );
}
