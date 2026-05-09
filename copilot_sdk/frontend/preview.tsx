import { useState } from "react";
import { createRoot } from "react-dom/client";

import "./copilot-theme.css";
import {
  ConservationSlider,
  CopilotShell,
  DecisionHistory,
  EvolutionPanel,
  FingerprintPanel,
  IKSBadge,
  ScoreResultCard,
  TrajectoryChart,
} from "./index";

const tabs = [
  { id: "overview", label: "Overview" },
  { id: "score", label: "Score" },
  { id: "learn", label: "Learn" },
  { id: "evolve", label: "Evolve" },
];

const factors = [
  { name: "research_depth", displayName: "Research Depth", weight: 0.82, sigma: 0.08, interpretation: "clean" },
  { name: "historical_waste", displayName: "Historical Waste", weight: 0.72, sigma: 0.12, interpretation: "clean" },
  { name: "recurrence_frequency", displayName: "Recurrence Frequency", weight: 0.67, sigma: 0.16, interpretation: "moderate" },
  { name: "weather_forecast", displayName: "Weather Forecast", weight: 0.44, sigma: 0.24, interpretation: "moderate" },
  { name: "conviction", displayName: "Conviction", weight: 0.18, sigma: 0.42, interpretation: "noisy" },
  { name: "source_reliability", displayName: "Source Reliability", weight: 0.12, sigma: 0.46, interpretation: "noisy" },
];

const trajectory = [
  { decisions: 0, iks: 0, winRate: 0.5 },
  { decisions: 10, iks: 11, winRate: 0.58 },
  { decisions: 20, iks: 19, winRate: 0.61 },
  { decisions: 30, iks: 24, winRate: 0.64 },
  { decisions: 40, iks: 31, winRate: 0.67 },
  { decisions: 50, iks: 34, winRate: 0.69 },
];

const decisions = [
  { id: "D-1001", action: "approve", confidence: 0.81 },
  { id: "D-1002", action: "review", confidence: 0.67 },
  { id: "D-1003", action: "defer", confidence: 0.59 },
  { id: "D-1004", action: "approve", confidence: 0.74 },
  { id: "D-1005", action: "escalate", confidence: 0.62 },
];

const variants = [
  {
    id: "V-1",
    name: "Threshold prior update",
    status: "promoted" as const,
    description: "Raised confidence for a repeated low-risk pattern.",
    shadowCount: 120,
    shadowWinRate: 0.74,
    conservationAtPromotion: 0.92,
    sourceRule: "rule-17",
  },
  {
    id: "V-2",
    name: "Fallback action probe",
    status: "shadow" as const,
    description: "Testing a narrower override path before promotion.",
    shadowCount: 45,
    shadowWinRate: 0.57,
  },
  {
    id: "V-3",
    name: "Aggressive shortcut",
    status: "rejected" as const,
    description: "Rejected after shadow evaluation failed conservation checks.",
    shadowCount: 30,
    shadowWinRate: 0.39,
    rejectReason: "Conservation margin was below threshold.",
  },
];

function PreviewApp() {
  const [activeTab, setActiveTab] = useState("overview");
  const [threshold, setThreshold] = useState(0.4);

  return (
    <CopilotShell
      name="Domain Copilot Preview"
      icon="C"
      tabs={tabs}
      activeTab={activeTab}
      onTabChange={setActiveTab}
      iks={34}
      iksDelta={0.4}
    >
      <div className="grid gap-6">
        <div className="grid gap-6 lg:grid-cols-[auto_1fr]">
          <div className="copilot-card flex items-center justify-center p-6">
            <IKSBadge value={34} delta={0.4} size="lg" />
          </div>
          <ScoreResultCard
            result={{
              decisionId: "demo-001",
              action: "approve",
              actionIndex: 0,
              confidence: 0.78,
              probabilities: [0.78, 0.14, 0.08],
              category: "repeatable_case",
              actionNames: ["approve", "review", "defer"],
              factors: { precision: 0.7, urgency: 0.4 },
            }}
            onConfirm={() => undefined}
            onOverride={() => undefined}
            iksDelta={0.4}
            rewardLine={{ reward: 0.42, previousReward: 0.35, rewardMultiplier: 1.2 }}
            centroidDelta={{ value: 0.0187, beforeLabel: "Previous centroid", afterLabel: "updated centroid" }}
          />
        </div>

        <div className="grid gap-6 xl:grid-cols-2">
          <FingerprintPanel
            factors={factors}
            decisionsAnalyzed={86}
            perCategoryPrecision={{ repeatable_case: 0.74, exception_case: 0.58 }}
          />
          <TrajectoryChart
            points={trajectory}
            currentIks={34}
            currentWinRate={0.69}
            switchingCostLine={28}
            annotations={[
              {
                decision: 24,
                type: "disruption",
                label: "Policy change",
                description: "Temporary precision drop after criteria changed.",
                recovery: "Recovered within 16 decisions.",
              },
            ]}
            narrative="Institutional knowledge is compounding as verified decisions accumulate."
            decisionsTotal={50}
            daysActive={18.4}
          />
        </div>

        <div className="grid gap-6 xl:grid-cols-2">
          <DecisionHistory
            decisions={decisions}
            renderCard={(decision) => (
              <div className="rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
                <div className="flex items-center justify-between">
                  <span className="font-semibold" style={{ color: "var(--copilot-text)" }}>
                    {decision.id}
                  </span>
                  <span style={{ color: "var(--copilot-text-muted)" }}>
                    {(decision.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="text-sm" style={{ color: "var(--copilot-text-muted)" }}>
                  {decision.action}
                </div>
              </div>
            )}
          />
          <ConservationSlider
            currentThreshold={threshold}
            conservationProduct={0.74}
            conservationThreshold={0.4}
            penaltyRatio={3}
            status="GREEN"
            onDrag={setThreshold}
            narrative="Current operating point clears the conservation threshold."
          />
        </div>

        <EvolutionPanel variants={variants} />
      </div>
    </CopilotShell>
  );
}

createRoot(document.getElementById("root") as HTMLElement).render(<PreviewApp />);
