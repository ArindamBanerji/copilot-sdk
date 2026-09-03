import { useEffect, useState } from "react";
import { CopilotShell, SelfComputationPanels, type CopilotShellTab } from "../../../../copilot_sdk/frontend";
import { getTrajectory } from "./api";
import PaperBadge from "./components/PaperBadge";
import AnalysisScreen from "./screens/AnalysisScreen";
import DashboardScreen from "./screens/DashboardScreen";
import LogTradeScreen from "./screens/LogTradeScreen";
import JournalScreen from "./screens/JournalScreen";
import PerformanceScreen from "./screens/PerformanceScreen";
import TradeDetailScreen from "./screens/TradeDetailScreen";

type TabId = "dashboard" | "log" | "analysis" | "performance" | "journal" | "detail";

const tabs: CopilotShellTab[] = [
  { id: "dashboard", label: "Dashboard" },
  { id: "log", label: "Log Trade" },
  { id: "analysis", label: "Analysis" },
  { id: "performance", label: "Performance" },
  { id: "journal", label: "Journal" },
  { id: "detail", label: "Trade Detail" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>("dashboard");
  const [activeTradeId, setActiveTradeId] = useState<string | null>(null);
  const [currentIks, setCurrentIks] = useState(50);

  useEffect(() => {
    let cancelled = false;
    getTrajectory()
      .then((trajectory) => {
        if (cancelled) {
          return;
        }
        const iks = trajectory.currentIks ?? trajectory.iks;
        if (typeof iks === "number" && Number.isFinite(iks)) {
          setCurrentIks(iks);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setCurrentIks(50);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  function selectTrade(tradeId: string) {
    setActiveTradeId(tradeId);
    setActiveTab("detail");
  }

  return (
    <CopilotShell
      name="Trading Copilot"
      icon="$"
      tabs={tabs}
      activeTab={activeTab}
      onTabChange={(tabId) => setActiveTab(tabId as TabId)}
      iks={currentIks}
    >
      <div className="mb-4 flex justify-end">
        <PaperBadge />
      </div>
      {activeTab === "dashboard" ? (
        <DashboardScreen
          onSelectTrade={selectTrade}
          onLogTrade={() => setActiveTab("log")}
        />
      ) : null}
      {activeTab === "log" ? <LogTradeScreen /> : null}
      {activeTab === "analysis" ? <AnalysisScreen /> : null}
      {activeTab === "performance" ? <PerformanceScreen /> : null}
      {activeTab === "journal" ? <JournalScreen /> : null}
      {activeTab === "detail" ? (
        <TradeDetailScreen
          tradeId={activeTradeId}
          onBack={() => setActiveTab("dashboard")}
        />
      ) : null}
      <SelfComputationPanels />
    </CopilotShell>
  );
}
