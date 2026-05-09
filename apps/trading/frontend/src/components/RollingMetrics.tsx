import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Analytics } from "../types";

function num(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

export default function RollingMetrics({ analytics }: { analytics?: Analytics }) {
  const rows = (analytics?.rolling10 || []).map((row, index) => ({
    label: typeof row.tradeId === "string" ? row.tradeId : String(index + 1),
    winRate: (num(row.rollingWinRate) ?? 0) * 100,
    pnl: num(row.rollingPnlDollars) ?? 0,
  }));

  return (
    <section className="copilot-card p-4">
      <h2 className="text-base font-semibold">Rolling 10</h2>
      <p className="mt-1 text-sm trading-muted">Recent win rate and rolling P&L.</p>
      {rows.length ? (
        <div className="mt-4 h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={rows} margin={{ left: 0, right: 12, top: 8, bottom: 0 }}>
              <XAxis dataKey="label" stroke="var(--copilot-text-subtle)" tickLine={false} />
              <YAxis yAxisId="left" stroke="var(--copilot-text-subtle)" tickLine={false} width={36} domain={[0, 100]} />
              <YAxis yAxisId="right" orientation="right" stroke="var(--copilot-text-subtle)" tickLine={false} width={52} />
              <Tooltip
                formatter={(value: number, name: string) => [
                  name === "winRate" ? `${Number(value).toFixed(0)}%` : `$${Number(value).toLocaleString()}`,
                  name === "winRate" ? "Win rate" : "Rolling P&L",
                ]}
              />
              <Line yAxisId="left" type="monotone" dataKey="winRate" stroke="var(--copilot-chart-win-rate)" strokeWidth={2} dot={false} />
              <Line yAxisId="right" type="monotone" dataKey="pnl" stroke="var(--copilot-chart-iks)" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="mt-4 rounded-md p-4 text-sm trading-muted" style={{ background: "var(--copilot-surface-muted)" }}>
          No rolling metrics available.
        </div>
      )}
    </section>
  );
}
