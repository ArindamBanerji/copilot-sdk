import type { FactorItem } from "../../../../../copilot_sdk/frontend";

interface ProfileArchetypeProps {
  factors?: FactorItem[];
}

const profiles: Record<string, { name: string; description: string }> = {
  recurrence_frequency: {
    name: "The Pattern Matcher",
    description: "Recurring operational patterns are the strongest signal in your DataOps decisions.",
  },
  business_criticality: {
    name: "The Risk Assessor",
    description: "Business impact determines when the system should escalate rather than absorb noise.",
  },
  impact_scope: {
    name: "The Blast Analyst",
    description: "Your edge comes from sizing downstream impact before choosing an action.",
  },
  downstream_urgency: {
    name: "The SLA Guardian",
    description: "Urgent downstream systems are your clearest trigger for protective action.",
  },
  source_reliability: {
    name: "The Trust Trader",
    description: "You trade off noisy sources against proven stable pipelines.",
  },
  data_freshness: {
    name: "The Freshness Monitor",
    description: "Freshness pressure is the signal your operational response keeps watching.",
  },
};

export default function ProfileArchetype({ factors }: ProfileArchetypeProps) {
  const top = (factors || [])
    .filter((factor) => Number.isFinite(factor.weight))
    .sort((a, b) => b.weight - a.weight)[0];
  const profile = profiles[top?.name || ""] || {
    name: "The Graph Operator",
    description: "More confirmed DataOps decisions are needed before a stable profile emerges.",
  };

  return (
    <section className="copilot-card p-5">
      <div className="text-xs font-semibold uppercase" style={{ color: "var(--copilot-text-subtle)" }}>
        Your profile
      </div>
      <h2 className="mt-2 text-2xl font-semibold" style={{ color: "var(--copilot-text)" }}>
        {profile.name}
      </h2>
      <p className="mt-2 text-sm dataops-muted">{profile.description}</p>
      {top ? (
        <div className="mt-4 text-sm" style={{ color: "var(--copilot-primary)" }}>
          Top factor: {top.displayName || top.name} ({Math.round(top.weight * 100)}%)
        </div>
      ) : null}
    </section>
  );
}
