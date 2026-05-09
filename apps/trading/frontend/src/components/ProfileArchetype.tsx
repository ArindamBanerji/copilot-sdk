import type { FingerprintResponse } from "../types";

const archetypes: Record<string, { name: string; description: string }> = {
  research_depth: {
    name: "The Researcher",
    description: "Your edge improves when the checklist is complete before the trade.",
  },
  position_size: {
    name: "The Sizer",
    description: "Position sizing explains more of the outcome than the setup label.",
  },
  technical_signal: {
    name: "The Technician",
    description: "Clean technical context separates your best entries from noise.",
  },
  time_horizon: {
    name: "The Timer",
    description: "Holding period discipline is a major part of the edge.",
  },
  conviction: {
    name: "The Gut Trader",
    description: "Conviction is powerful, but it needs evidence around it.",
  },
  market_regime: {
    name: "The Weather Vane",
    description: "Market backdrop changes whether the same setup works or fails.",
  },
};

export default function ProfileArchetype({ fingerprint }: { fingerprint?: FingerprintResponse }) {
  const top = [...(fingerprint?.factors || [])]
    .filter((factor) => typeof factor.weight === "number")
    .sort((a, b) => (b.weight || 0) - (a.weight || 0))[0];
  const profile = archetypes[top?.name || ""] || {
    name: "Profile pending",
    description: "More decisions are needed before the trading archetype is reliable.",
  };

  return (
    <section className="copilot-card p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">{profile.name}</h2>
          <p className="mt-1 text-sm trading-muted">{profile.description}</p>
        </div>
        {top ? (
          <div className="rounded-md border px-3 py-2 text-right" style={{ borderColor: "var(--copilot-border)" }}>
            <div className="text-xs trading-muted">Top factor</div>
            <div className="font-semibold">{(top.displayName || top.name).replace(/_/g, " ")}</div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
