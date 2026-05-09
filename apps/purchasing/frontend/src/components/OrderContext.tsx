import WasteSparkline from "./WasteSparkline";
import type { Analytics, FactorMap, TodaySummary, WasteHistory, Weather } from "../types";

interface OrderContextProps {
  today?: TodaySummary;
  weather?: Weather;
  events?: Array<Record<string, unknown>>;
  wasteHistory?: WasteHistory;
  analytics?: Analytics;
  factors: FactorMap;
}

function pct(value?: number) {
  return Number.isFinite(value) ? `${(Number(value) * 100).toFixed(0)}%` : "n/a";
}

function dayMetric(analytics?: Analytics, day?: string) {
  if (!analytics?.dayOfWeek || !day) {
    return undefined;
  }
  return analytics.dayOfWeek[day.toLowerCase()] ?? analytics.dayOfWeek[day];
}

export default function OrderContext({ today, weather, events, wasteHistory, analytics, factors }: OrderContextProps) {
  const metric = dayMetric(analytics, today?.dayOfWeek);
  const eventCount = events?.length ?? 0;

  return (
    <section className="purchase-card order-context">
      <div className="purchase-card-header">
        <div>
          <p className="purchase-kicker">Order context</p>
          <h2 className="purchase-title">Tomorrow's order is mostly inventory history</h2>
        </div>
        <span className="purchase-pill">Expected covers: ~180</span>
      </div>
      <div className="context-grid">
        <div>
          <span>Day</span>
          <strong>{today?.dayOfWeek ?? "Unknown"}</strong>
          <small>{metric?.count ?? 0} historical orders in this day bucket</small>
        </div>
        <div>
          <span>Weather</span>
          <strong>{weather?.condition ?? weather?.forecast ?? "Cached forecast"}</strong>
          <small>Scorer value {factors.weather_forecast.toFixed(2)}</small>
        </div>
        <div>
          <span>Events</span>
          <strong>{eventCount}</strong>
          <small>Scorer value {factors.event_flag.toFixed(2)}</small>
        </div>
        <div>
          <span>Historical waste</span>
          <strong>{pct(factors.historical_waste)}</strong>
          <WasteSparkline history={wasteHistory} />
        </div>
      </div>
    </section>
  );
}
