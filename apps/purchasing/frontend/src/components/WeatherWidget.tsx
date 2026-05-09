import type { Weather } from "../types";

interface WeatherWidgetProps {
  weather?: Weather;
  dayOfWeek?: string;
}

export default function WeatherWidget({ weather, dayOfWeek }: WeatherWidgetProps) {
  const condition = weather?.condition ?? weather?.forecast ?? "No forecast";
  const temp = Number.isFinite(weather?.temperatureF) ? `${weather?.temperatureF} F` : "Temp unavailable";
  const precipValue = weather?.precipitationProb ?? weather?.precipChance;
  const precip = Number.isFinite(precipValue) ? `${precipValue}% precip` : "Precip unknown";

  return (
    <section className="purchase-card dashboard-header-card">
      <p className="purchase-kicker">Today</p>
      <h2 className="purchase-title">{dayOfWeek ?? "Current ordering day"}</h2>
      <div className="header-metric">{condition}</div>
      <p className="purchase-muted">
        {temp} | {precip}
      </p>
    </section>
  );
}
