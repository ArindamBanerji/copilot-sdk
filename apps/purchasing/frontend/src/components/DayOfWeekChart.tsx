import type { Analytics } from "../types";

interface DayOfWeekChartProps {
  analytics?: Analytics;
}

const days = [
  ["monday", "Mon"],
  ["tuesday", "Tue"],
  ["wednesday", "Wed"],
  ["thursday", "Thu"],
  ["friday", "Fri"],
  ["saturday", "Sat"],
  ["sunday", "Sun"],
];

export default function DayOfWeekChart({ analytics }: DayOfWeekChartProps) {
  const data = analytics?.dayOfWeek ?? {};
  const friday = Number(data.friday?.accuracy ?? 1);
  const average = days.reduce((total, [key]) => total + Number(data[key]?.accuracy ?? 0), 0) / days.length;
  return (
    <section className="purchase-card">
      <p className="purchase-kicker">Day of week</p>
      <h2 className="purchase-title">Friday is the stress test</h2>
      <div className="bar-list compact">
        {days.map(([key, label]) => {
          const metric = data[key];
          const accuracy = Number(metric?.accuracy ?? 0);
          return (
            <div className="bar-row" key={key}>
              <span>{label}</span>
              <div className="factor-track"><span style={{ width: `${Math.max(accuracy * 100, 2)}%` }} /></div>
              <strong>{(accuracy * 100).toFixed(0)}%</strong>
              <small>{metric?.count ?? 0}</small>
            </div>
          );
        })}
      </div>
      <p className="purchase-muted">
        {friday < average ? "Friday weakness is supported by the current analytics." : "Day-of-week weakness is not yet concentrated on Friday."}
      </p>
    </section>
  );
}
