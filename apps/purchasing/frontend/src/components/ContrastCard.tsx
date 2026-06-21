import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Analytics, MetricBreakdown } from "../types";

interface ContrastCardProps {
  analytics?: Analytics;
}

function pct(value?: number) {
  return Number.isFinite(value) ? `${(Number(value) * 100).toFixed(0)}%` : "n/a";
}

function money(value?: number) {
  return Number.isFinite(value) ? `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : "n/a";
}

function metricValue(metric?: MetricBreakdown, key?: string) {
  const value = key ? metric?.[key] : undefined;
  return Number.isFinite(value) ? Number(value) : undefined;
}

function derivedCurve(aligned?: MetricBreakdown, misaligned?: MetricBreakdown) {
  const alignedCost = Number(aligned?.totalCostDollars ?? 0);
  const misalignedCost = Number(misaligned?.totalCostDollars ?? 0);
  const alignedCount = Math.max(Number(aligned?.count ?? 4), 1);
  const misalignedCount = Math.max(Number(misaligned?.count ?? 4), 1);
  return Array.from({ length: 6 }, (_, index) => ({
    step: index + 1,
    aligned: Math.max(0, alignedCost * 0.18 - (index * alignedCost) / alignedCount / 6),
    misaligned: (index * misalignedCost) / misalignedCount,
  }));
}

export default function ContrastCard({ analytics }: ContrastCardProps) {
  const contrast = analytics?.contrastCard;
  const aligned = contrast?.aligned;
  const misaligned = contrast?.misaligned;
  const exactCurves = contrast?.curves as Array<Record<string, number>> | undefined;
  const chartData = Array.isArray(exactCurves) && exactCurves.length > 0 ? exactCurves : derivedCurve(aligned, misaligned);

  return (
    <section className="purchase-card contrast-card" data-testid="contrast-card">
      <div className="purchase-card-header">
        <div>
          <p className="purchase-kicker">Contrast card</p>
          <h1>YOUR TWO SELVES</h1>
          <p className="purchase-muted">Same owner. Different outcome when the fingerprint is followed.</p>
        </div>
      </div>
      <div className="contrast-grid">
        <div className="contrast-pane aligned">
          <span>Aligned</span>
          <strong>{pct(aligned?.accuracy)}</strong>
          <small>{aligned?.count ?? 0} orders | {money(aligned?.totalCostDollars)}</small>
        </div>
        <div className="contrast-pane misaligned">
          <span>Misaligned</span>
          <strong>{pct(misaligned?.accuracy)}</strong>
          <small>{misaligned?.count ?? 0} orders | {money(misaligned?.totalCostDollars)}</small>
        </div>
        <div className="contrast-pane">
          <span>Waste signal</span>
          <strong>{pct(metricValue(aligned, "wastePct") ?? analytics?.wasteCostAnalysis?.averageWastePct)}</strong>
          <small>Current aggregate waste rate</small>
        </div>
      </div>
      <div className="contrast-chart">
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={chartData}>
            <XAxis dataKey="step" tickLine={false} />
            <YAxis tickLine={false} />
            <Tooltip />
            <Area type="monotone" dataKey="aligned" stroke="#059669" fill="rgba(5, 150, 105, 0.16)" strokeWidth={2} />
            <Area type="monotone" dataKey="misaligned" stroke="#dc2626" fill="rgba(220, 38, 38, 0.12)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
