import { useEffect, useState } from "react";
import { CopilotShell, SelfComputationPanels } from "../../../../copilot_sdk/frontend";
import { getTrajectory } from "./api";
import DashboardScreen from "./screens/DashboardScreen";
import OrderScreen from "./screens/OrderScreen";
import AnalysisScreen from "./screens/AnalysisScreen";
import InventoryScreen from "./screens/InventoryScreen";
import PerformanceScreen from "./screens/PerformanceScreen";
import type { Item } from "./types";

type TabId = "dashboard" | "order" | "analysis" | "inventory" | "performance";

const tabs = [
  { id: "dashboard", label: "Dashboard" },
  { id: "order", label: "Order" },
  { id: "analysis", label: "Analysis" },
  { id: "inventory", label: "Inventory" },
  { id: "performance", label: "Performance" },
];

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>("dashboard");
  const [selectedItem, setSelectedItem] = useState<Item | undefined>();
  const [iks, setIks] = useState(50);

  useEffect(() => {
    let mounted = true;
    getTrajectory()
      .then((trajectory) => {
        const nextIks = trajectory.currentIks ?? trajectory.iks;
        if (mounted && Number.isFinite(nextIks)) {
          setIks(Number(nextIks));
        }
      })
      .catch(() => {
        if (mounted) {
          setIks(50);
        }
      });
    return () => {
      mounted = false;
    };
  }, []);

  const selectItem = (item?: Item) => {
    setSelectedItem(item);
    setActiveTab("order");
  };

  return (
    <CopilotShell
      name="Purchasing Copilot"
      icon="PO"
      tabs={tabs}
      activeTab={activeTab}
      onTabChange={(tab) => setActiveTab(tab as TabId)}
      iks={iks}
    >
      {activeTab === "dashboard" && <DashboardScreen onSelectItem={selectItem} />}
      {activeTab === "order" && <OrderScreen selectedItem={selectedItem} />}
      {activeTab === "analysis" && <AnalysisScreen />}
      {activeTab === "inventory" && <InventoryScreen />}
      {activeTab === "performance" && <PerformanceScreen />}
      <SelfComputationPanels />
    </CopilotShell>
  );
}
