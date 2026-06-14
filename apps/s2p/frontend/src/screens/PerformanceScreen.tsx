import { ConservationMiniGauge } from "../components/ConservationMiniGauge";
import { CycleTimePanel } from "../components/CycleTimePanel";
import { FinancialImpactTrendPanel } from "../components/FinancialImpactTrendPanel";
import { OperationalSummary } from "../components/OperationalSummary";
import { TrajectoryChart } from "../components/TrajectoryChart";
import { WhatIfSimulator } from "../components/WhatIfSimulator";
import { fetchConservation } from "../api";
import type { ConservationStatus } from "../types";
import { useEffect, useState } from "react";

export function PerformanceScreen() {
  const [conservation, setConservation] = useState<ConservationStatus | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchConservation().then((response) => {
      if (!cancelled) setConservation(response);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Operating loop</p>
        <h1 className="mt-1 text-3xl font-semibold text-slate-950">Performance</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-600">
          Track learning trajectory, conservation health, what-if scenarios, and operational savings
          for the S2P invoice exception workflow.
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_360px]">
        <TrajectoryChart />
        <ConservationMiniGauge conservation={conservation} />
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <WhatIfSimulator />
        <OperationalSummary />
      </div>
      <FinancialImpactTrendPanel />
      <CycleTimePanel />
    </section>
  );
}
