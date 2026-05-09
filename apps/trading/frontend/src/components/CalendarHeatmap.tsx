import type { JoinedTrade, MetricBreakdown } from "../types";

const dayNames = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

function dayColor(trade: JoinedTrade | undefined): string {
  if (!trade) {
    return "var(--copilot-surface-muted)";
  }
  if (trade.isCorrect === true || trade.outcome === "win") {
    return "rgba(21, 128, 61, 0.75)";
  }
  if (trade.isCorrect === false || trade.outcome === "loss") {
    return "rgba(185, 28, 28, 0.72)";
  }
  return "rgba(100, 116, 139, 0.55)";
}

export default function CalendarHeatmap({
  trades,
  calendar,
}: {
  trades: JoinedTrade[];
  calendar?: Record<string, MetricBreakdown>;
}) {
  const datedTrades = trades
    .filter((trade) => trade.date)
    .sort((left, right) => String(left.date).localeCompare(String(right.date)))
    .slice(-42);
  const cells = Array.from({ length: 42 }, (_, index) => datedTrades[index]);

  return (
    <section className="copilot-card p-4">
      <h2 className="text-base font-semibold">Calendar Heatmap</h2>
      <div className="mt-4 grid grid-cols-7 gap-1">
        {cells.map((trade, index) => (
          <div
            key={`${trade?.decisionId || "empty"}-${index}`}
            title={trade ? `${trade.date} ${trade.ticker || ""}` : "No trade"}
            className="h-8 rounded"
            style={{ background: dayColor(trade) }}
          />
        ))}
      </div>
      <div className="mt-4 grid gap-2 md:grid-cols-5">
        {dayNames.map((day) => {
          const stats = calendar?.[day];
          return (
            <div key={day} className="rounded-md border p-2" style={{ borderColor: "var(--copilot-border)" }}>
              <div className="text-xs trading-muted">{day}</div>
              <div className="text-sm font-semibold">{stats?.count ?? 0} trades</div>
              <div className="text-xs trading-muted">
                {typeof stats?.winRate === "number" ? `${Math.round(stats.winRate * 100)}% win` : "-"}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
