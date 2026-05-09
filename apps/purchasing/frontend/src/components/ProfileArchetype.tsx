import type { FingerprintFactor, FingerprintResponse } from "../types";

interface ProfileArchetypeProps {
  fingerprint?: FingerprintResponse;
}

const archetypes: Record<string, { name: string; description: string }> = {
  historical_waste: {
    name: "THE HISTORIAN",
    description: "Your edge is remembering which items repeatedly waste out.",
  },
  expected_demand: {
    name: "THE PLANNER",
    description: "Your demand estimate is the strongest ordering input.",
  },
  day_of_week: {
    name: "THE SCHEDULER",
    description: "The calendar explains more than the daily noise.",
  },
  event_flag: {
    name: "THE EVENT MANAGER",
    description: "You react most clearly when events change demand.",
  },
  weather_forecast: {
    name: "THE WEATHER WATCHER",
    description: "Forecast shifts still pull the ordering pattern.",
  },
  supplier_lead_time: {
    name: "THE LOGISTICS PRO",
    description: "Lead time is the constraint that shapes your best orders.",
  },
};

function topFactor(fingerprint?: FingerprintResponse) {
  const factors = fingerprint?.factors;
  if (!factors) {
    return undefined;
  }
  const entries = Array.isArray(factors)
    ? factors.map((factor: FingerprintFactor) => [factor.name, Number(factor.weight ?? 0)] as const)
    : Object.entries(factors).map(([name, weight]) => [name, Number(weight ?? 0)] as const);
  return entries.sort((left, right) => right[1] - left[1])[0]?.[0];
}

export default function ProfileArchetype({ fingerprint }: ProfileArchetypeProps) {
  const factor = topFactor(fingerprint);
  const archetype = archetypes[factor ?? ""] ?? {
    name: "THE HISTORIAN",
    description: "There is not enough fingerprint data yet, so the profile defaults to waste history.",
  };

  return (
    <section className="purchase-card profile-archetype">
      <p className="purchase-kicker">Your Profile</p>
      <h2>{archetype.name}</h2>
      <p className="purchase-muted">{archetype.description}</p>
    </section>
  );
}
