import type { Analytics, MetricBreakdown } from "../types";

const labels: Record<string, string> = {
  low_vix: "Low VIX",
  mid_vix: "Mid VIX",
  high_vix: "High VIX",
};

function pct(value: number | null | undefined): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "-";
}

export default function RegimeChart({ analytics }: { analytics?: Analytics }) {
  const regimes = analytics?.regimeAnalysis || {};
  const rows = ["low_vix", "mid_vix", "high_vix"].map((key) => [key, regimes[key]] as const).filter(([, value]) => value);

  return (
    <section className="copilot-card p-4">
      <h2 className="text-base font-semibold">Regime Analysis</h2>
      <p className="mt-1 text-sm trading-muted">Win rate by volatility backdrop.</p>
      <div className="mt-4 grid gap-3">
        {rows.length ? rows.map(([key, value]) => <Bar key={key} label={labels[key]} value={value} />) : (
          <div className="rounded-md p-4 text-sm trading-muted" style={{ background: "var(--copilot-surface-muted)" }}>
            No regime data available.
          </div>
        )}
      </div>
    </section>
  );
}

function Bar({ label, value }: { label: string; value: MetricBreakdown }) {
  const width = Math.max(0, Math.min(100, (value.winRate ?? 0) * 100));
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm">
        <span>{label}</span>
        <span className="font-semibold">{pct(value.winRate)}</span>
      </div>
      <div className="trading-bar-track">
        <div
          className="h-full rounded-full"
          style={{ width: `${width}%`, background: label === "High VIX" ? "var(--trading-negative)" : "var(--trading-positive)" }}
        />
      </div>
      <div className="mt-1 text-xs trading-muted">{value.count ?? 0} trades · {value.pnlDollars ?? 0} P&L</div>
    </div>
  );
}
