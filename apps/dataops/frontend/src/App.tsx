import { useEffect, useMemo, useState } from "react";
import { CopilotShell, SelfComputationPanels } from "../../../../copilot_sdk/frontend";
import { getHealth, getTrajectory } from "./api";
import type { Health } from "./types";
import DashboardScreen from "./screens/DashboardScreen";
import TriageScreen from "./screens/TriageScreen";
import InsightScreen from "./screens/InsightScreen";
import EvidenceScreen from "./screens/EvidenceScreen";
import CurveScreen from "./screens/CurveScreen";

type TabId = "dashboard" | "triage" | "insight" | "evidence" | "curve";

const tabs = [
  { id: "dashboard", label: "Dashboard" },
  { id: "triage", label: "Triage" },
  { id: "insight", label: "Insight" },
  { id: "evidence", label: "Evidence" },
  { id: "curve", label: "Curve" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>("dashboard");
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [iks, setIks] = useState(0);

  useEffect(() => {
    let cancelled = false;
    Promise.allSettled([getHealth(), getTrajectory()]).then(([healthResult, trajectoryResult]) => {
      if (cancelled) {
        return;
      }
      if (healthResult.status === "fulfilled") {
        setHealth(healthResult.value);
      }
      if (trajectoryResult.status === "fulfilled") {
        setIks(trajectoryResult.value.currentIks ?? 0);
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const content = useMemo(() => {
    if (activeTab === "dashboard") {
      return (
        <DashboardScreen
          onSelectAlert={(alertId) => {
            setSelectedAlertId(alertId);
            setActiveTab("triage");
          }}
        />
      );
    }
    if (activeTab === "triage") {
      return (
        <TriageScreen
          selectedAlertId={selectedAlertId}
          onBack={() => setActiveTab("dashboard")}
        />
      );
    }
    if (activeTab === "insight") {
      return <InsightScreen />;
    }
    if (activeTab === "evidence") {
      return <EvidenceScreen />;
    }
    return <CurveScreen />;
  }, [activeTab, selectedAlertId]);

  return (
    <CopilotShell
      name="DataOps Copilot"
      icon="DO"
      tabs={tabs}
      activeTab={activeTab}
      onTabChange={(tabId) => setActiveTab(tabId as TabId)}
      iks={iks}
    >
      {health?.graphSource === "fixture" ? (
        <div
          className="mb-4 rounded-md border px-4 py-3 text-sm"
          style={{
            borderColor: "var(--copilot-border)",
            background: "var(--copilot-primary-light)",
            color: "var(--copilot-primary)",
          }}
        >
          Fixture graph mode. Live graph data is not connected.
        </div>
      ) : null}
      {content}
      <SelfComputationPanels />
    </CopilotShell>
  );
}
