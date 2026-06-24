import type { AnalyticsGroup } from "../types";

function pct(value: number | null | undefined): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "-";
  return `${(value * 100).toFixed(1)}%`;
}

function count(group?: AnalyticsGroup): number {
  return Number(group?.count ?? group?.totalTrades ?? 0) || 0;
}

function label(value: string): string {
  return value.replace(/_/g, " ");
}

function styleFor(group?: AnalyticsGroup) {
  return {
    count: count(group),
    accuracy: group?.winRate,
  };
}

export default function EarningsInsightCard({ groups }: { groups: AnalyticsGroup[] }) {
  const directional = groups.find((group) => group.key === "directional");
  const volatility = groups.find((group) => group.key === "volatility");
  const directionalStats = styleFor(directional);
  const volatilityStats = styleFor(volatility);
  const total = directionalStats.count + volatilityStats.count;

  if (total === 0) {
    return (
      <section className="copilot-card p-4">
        <h3 className="text-base font-semibold">Earnings Style Analysis</h3>
        <p className="mt-3 text-sm trading-muted">No event-driven trades yet.</p>
      </section>
    );
  }

  const dominant =
    volatilityStats.count > directionalStats.count
      ? { name: "volatility", stats: volatilityStats }
      : { name: "directional", stats: directionalStats };
  const secondary = dominant.name === "volatility" ? directionalStats : volatilityStats;

  return (
    <section className="copilot-card p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold">Earnings Style Analysis</h3>
          <p className="mt-1 text-sm trading-muted">Event-driven trades split into directional and volatility playbooks.</p>
        </div>
        <span className="rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide" style={{ background: "var(--copilot-surface-muted)" }}>
          {total} trades
        </span>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <StyleBlock
          title="Directional"
          subtitle="Single-leg calls/puts"
          count={directionalStats.count}
          accuracy={directionalStats.accuracy}
        />
        <StyleBlock
          title="Volatility"
          subtitle="Straddles/strangles"
          count={volatilityStats.count}
          accuracy={volatilityStats.accuracy}
        />
      </div>

      <div className="mt-4 rounded-md border p-3 text-sm" style={{ borderColor: "var(--copilot-border)", background: "var(--copilot-surface-muted)" }}>
        <span className="font-semibold">
          You are an earnings {dominant.name.toUpperCase()} trader.
        </span>{" "}
        {label(dominant.name)}: {pct(dominant.stats.accuracy)}.{" "}
        {dominant.name === "volatility" ? "Directional" : "Volatility"}: {pct(secondary.accuracy)}.
      </div>
    </section>
  );
}

function StyleBlock({
  title,
  subtitle,
  count,
  accuracy,
}: {
  title: string;
  subtitle: string;
  count: number;
  accuracy?: number | null;
}) {
  return (
    <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="text-sm font-semibold">{title}</div>
      <div className="mt-1 text-xs trading-muted">{subtitle}</div>
      <div className="mt-3 flex items-end justify-between gap-3">
        <div>
          <div className="text-2xl font-semibold">{pct(accuracy)}</div>
          <div className="text-xs trading-muted">accuracy</div>
        </div>
        <div className="text-right">
          <div className="text-lg font-semibold">{count}</div>
          <div className="text-xs trading-muted">trades</div>
        </div>
      </div>
    </div>
  );
}
