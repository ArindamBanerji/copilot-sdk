import type { Analytics, MetricBreakdown } from "../types";

function pct(value: number | null | undefined): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "-";
}

function money(value: number | null | undefined): string {
  return typeof value === "number" ? `$${value.toLocaleString()}` : "-";
}

function asMetric(value: unknown): MetricBreakdown | undefined {
  return value && typeof value === "object" ? (value as MetricBreakdown) : undefined;
}

export default function RiskManagementCard({ analytics }: { analytics?: Analytics }) {
  const risk = analytics?.riskManagement || {};
  const withStops = asMetric(risk.withStops);
  const withoutStops = asMetric(risk.withoutStops);
  const riskValues = risk as Record<string, unknown>;
  const avgStop = typeof riskValues.avgStopDistancePct === "number" ? riskValues.avgStopDistancePct : undefined;
  const avgTarget = typeof riskValues.avgTargetDistancePct === "number" ? riskValues.avgTargetDistancePct : undefined;

  return (
    <section className="copilot-card p-4">
      <h2 className="text-base font-semibold">Risk Management</h2>
      <p className="mt-1 text-sm trading-muted">Stop discipline and target structure by closed trades.</p>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <Bucket title="With stops" metric={withStops} positive />
        <Bucket title="Without stops" metric={withoutStops} />
      </div>
      {(typeof avgStop === "number" || typeof avgTarget === "number") ? (
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <Stat label="Avg stop distance" value={typeof avgStop === "number" ? `${avgStop.toFixed(1)}%` : "-"} />
          <Stat label="Avg target distance" value={typeof avgTarget === "number" ? `${avgTarget.toFixed(1)}%` : "-"} />
        </div>
      ) : null}
    </section>
  );
}

function Bucket({ title, metric, positive = false }: { title: string; metric?: MetricBreakdown; positive?: boolean }) {
  return (
    <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
      <div className={positive ? "font-semibold trading-positive" : "font-semibold trading-negative"}>{title}</div>
      <div className="mt-3 grid grid-cols-3 gap-2">
        <Stat label="Win rate" value={pct(metric?.winRate)} />
        <Stat label="P&L" value={money(metric?.pnlDollars)} />
        <Stat label="Trades" value={String(metric?.count ?? 0)} />
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs trading-muted">{label}</div>
      <div className="text-sm font-semibold">{value}</div>
    </div>
  );
}
