import { useEffect, useState } from "react";
import { fetchWeatherRisk, type WeatherRiskResponse } from "../api";
import ProvenanceBadge from "./ProvenanceBadge";

export default function WeatherImpactCard() {
  const [risk, setRisk] = useState<WeatherRiskResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const payload = await fetchWeatherRisk();
        if (mounted) setRisk(payload);
      } catch (caught) {
        if (mounted) setError(caught instanceof Error ? caught.message : "Weather data unavailable");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void load();
    return () => {
      mounted = false;
    };
  }, []);

  const categoryRisk = risk?.categoryRisk ?? {};

  return (
    <section className="purchase-card">
      <div className="purchase-card-header">
        <div>
          <p className="purchase-kicker">Weather Intelligence</p>
          <h2 className="purchase-title">Weather changes tomorrow's prep plan</h2>
        </div>
        <div className="flex flex-col items-end gap-1">
          <ProvenanceBadge source="scraped_external" />
          <span className="text-xs purchase-muted">OpenMeteo</span>
        </div>
      </div>
      {loading ? <p className="purchase-muted">Checking the forecast...</p> : null}
      {error ? <p className="purchase-muted">{error}</p> : null}
      {!loading && !error ? (
        <>
          <p className="mt-3 text-sm font-semibold">{risk?.alert ?? "Weather data unavailable"}</p>
          <p className="purchase-muted mt-2">Rainy weekend means less foot traffic and more comfort food orders.</p>
          <div className="mt-4 grid gap-2 md:grid-cols-7">
            {(risk?.forecast ?? []).map((day) => (
              <div key={`${day.label}-${day.condition}`} className="rounded-md border p-2 text-sm" style={{ borderColor: "var(--purchase-border)" }}>
                <div className="font-semibold">{day.label}</div>
                <div className="capitalize purchase-muted">{day.condition}</div>
                <div>{day.risk} risk</div>
              </div>
            ))}
          </div>
          <div className="mt-4 grid gap-2 md:grid-cols-4">
            {[
              ["Produce", categoryRisk.produce],
              ["Seafood", categoryRisk.seafood],
              ["Dairy", categoryRisk.dairy],
              ["Dry goods", categoryRisk.dryGoods],
            ].map(([label, value]) => (
              <div key={label} className="rounded-md border p-3 text-sm" style={{ borderColor: "var(--purchase-border)" }}>
                <div className="purchase-muted">{label}</div>
                <strong>{value ?? "LOW"}</strong>
              </div>
            ))}
          </div>
        </>
      ) : null}
    </section>
  );
}
