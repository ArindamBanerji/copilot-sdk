import { useState, type CSSProperties } from "react";
import { CopilotShell } from "../../../../copilot_sdk/frontend";
import { DashboardScreen } from "./screens/DashboardScreen";
import { EvidenceScreen } from "./screens/EvidenceScreen";
import { InsightScreen } from "./screens/InsightScreen";
import { PerformanceScreen } from "./screens/PerformanceScreen";
import { SuppliersScreen } from "./screens/SuppliersScreen";
import { TriageScreen } from "./screens/TriageScreen";

type TabId = "dashboard" | "triage" | "insight" | "evidence" | "suppliers" | "performance";

const tabs: { id: TabId; label: string }[] = [
  { id: "dashboard", label: "Dashboard" },
  { id: "triage", label: "Exception Triage" },
  { id: "insight", label: "Insight" },
  { id: "evidence", label: "Evidence" },
  { id: "suppliers", label: "Suppliers" },
  { id: "performance", label: "Performance" }
];

const themeVars = {
  "--copilot-primary": "#D97706",
  "--copilot-primary-contrast": "#ffffff",
  "--copilot-accent": "#F59E0B",
  "--copilot-chart-iks": "#D97706",
  "--copilot-chart-win-rate": "#0F766E"
} as CSSProperties;

function renderScreen(activeTab: TabId) {
  switch (activeTab) {
    case "dashboard":
      return <DashboardScreen />;
    case "triage":
      return <TriageScreen />;
    case "insight":
      return <InsightScreen />;
    case "evidence":
      return <EvidenceScreen />;
    case "suppliers":
      return <SuppliersScreen />;
    case "performance":
      return <PerformanceScreen />;
    default:
      return <DashboardScreen />;
  }
}

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>("dashboard");

  return (
    <div style={themeVars}>
      <CopilotShell
        name="S2P Copilot"
        icon="S2P"
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={(tab) => setActiveTab(tab as TabId)}
        iks={0}
      >
        {renderScreen(activeTab)}
      </CopilotShell>
    </div>
  );
}
