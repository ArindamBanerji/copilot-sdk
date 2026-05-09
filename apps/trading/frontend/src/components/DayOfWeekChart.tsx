import type { Analytics, MetricBreakdown } from "../types";

const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

function pct(value: number | null | undefined): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "-";
}

export default function DayOfWeekChart({ analytics }: { analytics?: Analytics }) {
  const calendar = analytics?.calendarHeatmap || {};
  const rows = days
    .map((day) => [day, calendar[day]] as const)
    .filter(([, value]) => value);
  const monday = calendar.Monday?.winRate;
  const thursday = calendar.Thursday?.winRate;
  const supportedInsight = typeof monday === "number" && typeof thursday === "number" && monday < 0.35 && thursday > 0.65;

  return (
    <section className="copilot-card p-4">
      <h2 className="text-base font-semibold">Day of Week</h2>
      <p className="mt-1 text-sm trading-muted">
        {supportedInsight
          ? "Monday trades are impulsive. By Thursday, you've processed the week."
          : "Win rate varies by day; use the stronger sessions as the baseline."}
      </p>
      <div className="mt-4 grid gap-3">
        {rows.length ? rows.map(([day, value]) => <Bar key={day} label={day} value={value} />) : (
          <div className="rounded-md p-4 text-sm trading-muted" style={{ background: "var(--copilot-surface-muted)" }}>
            No day-of-week analytics available.
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
        <div className="trading-bar-fill" style={{ width: `${width}%` }} />
      </div>
      <div className="mt-1 text-xs trading-muted">{value.count ?? 0} trades · {value.wins ?? 0} wins</div>
    </div>
  );
}
