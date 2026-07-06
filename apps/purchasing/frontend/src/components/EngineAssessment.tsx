import type { Analytics, FactorMap, FingerprintFactor, FingerprintResponse } from "../types";
import { factorDisplayName } from "../factorDisplay";

interface EngineAssessmentProps {
  factors: FactorMap;
  fingerprint?: FingerprintResponse;
  analytics?: Analytics;
  similarCount: number;
}

function fingerprintWeight(fingerprint: FingerprintResponse | undefined, name: string) {
  const factors = fingerprint?.factors;
  if (Array.isArray(factors)) {
    const match = factors.find((factor: FingerprintFactor) => factor.name === name);
    return Number(match?.weight ?? 0);
  }
  return Number(factors?.[name] ?? 0);
}

export default function EngineAssessment({ factors, fingerprint, analytics, similarCount }: EngineAssessmentProps) {
  const ranked = (Object.keys(factors) as Array<keyof FactorMap>)
    .map((name) => ({
      name,
      label: factorDisplayName(name),
      value: factors[name],
      weight: fingerprintWeight(fingerprint, name),
    }))
    .sort((left, right) => right.weight - left.weight || right.value - left.value);
  const top = ranked.slice(0, 3);
  const weakest = ranked[ranked.length - 1];
  const historicalWeight = fingerprintWeight(fingerprint, "historical_waste");
  const weatherWeight = fingerprintWeight(fingerprint, "weather_forecast");
  const eventWeight = fingerprintWeight(fingerprint, "event_flag");

  return (
    <section className="purchase-card engine-assessment">
      <div className="purchase-card-header">
        <div>
          <p className="purchase-kicker">Engine assessment</p>
          <h2 className="purchase-title">What the model is using</h2>
        </div>
        <span className="purchase-pill">{similarCount} similar orders</span>
      </div>
      <div className="engine-grid">
        {top.map((factor) => (
          <div key={factor.name}>
            <span>{factor.label}</span>
            <strong>{factor.value.toFixed(2)}</strong>
            <small>Fingerprint weight {factor.weight.toFixed(2)}</small>
          </div>
        ))}
        {weakest ? (
          <div>
            <span>Noisiest / weakest</span>
            <strong>{weakest.label}</strong>
            <small>Fingerprint weight {weakest.weight.toFixed(2)}</small>
          </div>
        ) : null}
      </div>
      <p className="purchase-muted">
        {historicalWeight >= weatherWeight && historicalWeight >= eventWeight
          ? "Historical waste is carrying the signal for this ordering profile."
          : "Weather and events are present, but the engine keeps them subordinate when the fingerprint is weak."}
      </p>
      {analytics?.portfolioSummary?.accuracy !== undefined ? (
        <p className="purchase-muted">
          Portfolio accuracy baseline: {(Number(analytics.portfolioSummary.accuracy) * 100).toFixed(0)}%.
        </p>
      ) : null}
    </section>
  );
}
