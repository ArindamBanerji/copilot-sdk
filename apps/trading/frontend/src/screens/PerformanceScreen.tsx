import { useEffect, useMemo, useState } from "react";
import {
  ConservationProjection,
  TrajectoryChart,
  type GenericTrajectoryResponse,
  type TrajectoryPoint,
} from "../../../../../copilot_sdk/frontend";
import { getAnalytics, getConservationStatus, getTrajectory } from "../api";
import AuditTrail from "../components/AuditTrail";
import CategoryPerformance from "../components/CategoryPerformance";
import CentroidTimeline from "../components/CentroidTimeline";
import CohortStatusPanel from "../components/CohortStatusPanel";
import EvolutionControlsPanel from "../components/EvolutionControlsPanel";
import EvolutionPanel from "../components/EvolutionPanel";
import ExecutionQualityCard from "../components/ExecutionQualityCard";
import PromotionDashboard from "../components/PromotionDashboard";
import RegimeAnalyticsPanel from "../components/RegimeAnalyticsPanel";
import RegimePanel from "../components/RegimePanel";
import VolatilityScenarioPanel from "../components/VolatilityScenarioPanel";
import RegimeStatusPanel from "../components/RegimeStatusPanel";
import RejectionMomentPanel from "../components/RejectionMomentPanel";
import ReConvergencePanel from "../components/ReConvergencePanel";
import RiskManagementCard from "../components/RiskManagementCard";
import RollingMetrics from "../components/RollingMetrics";
import StrategySafetyBreakdownPanel from "../components/StrategySafetyBreakdownPanel";
import TransferPanel from "../components/TransferPanel";
import VIXTimingPanel from "../components/VIXTimingPanel";
import WebhookStatusCard from "../components/WebhookStatusCard";
import type { Analytics, ConservationState, TrajectoryResponse } from "../types";
import {
  AutonomyThrottlePanel,
  CertificatePanel,
  DispersionPanel,
  GateDividendPanel,
  RegimeRejectionPanel,
  RejectionMomentTable,
  RichCheapPanel,
  TailBetsPanel,
  VolShortPanel,
  VRPPanel,
} from "../components/DemoBeatPanels";

function pct(value: number | null | undefined): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "-";
}

function normalizePoints(trajectory?: TrajectoryResponse): TrajectoryPoint[] {
  return (trajectory?.points || [])
    .map((point) => ({
      decisions: Number(point.decisions) || 0,
      iks: Number(point.iks) || 0,
      winRate: Number(point.winRate) || 0,
    }))
    .filter((point) => point.decisions > 0);
}

export default function PerformanceScreen() {
  const [analytics, setAnalytics] = useState<Analytics | undefined>();
  const [trajectory, setTrajectory] = useState<TrajectoryResponse | undefined>();
  const [conservation, setConservation] = useState<ConservationState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const points = useMemo(() => normalizePoints(trajectory), [trajectory]);
  const lastPoint = points.length ? points[points.length - 1] : undefined;
  const currentIks = trajectory?.currentIks ?? trajectory?.iks ?? lastPoint?.iks ?? 0;
  const currentWinRate = trajectory?.currentWinRate ?? lastPoint?.winRate ?? analytics?.portfolioSummary?.winRate ?? 0;
  const decisionsTotal = trajectory?.decisionsTotal ?? analytics?.totalTrades ?? lastPoint?.decisions ?? 0;
  const daysActive = trajectory?.daysActive ?? analytics?.closedTrades ?? 0;
  const narrative = `A competitor needs ${decisionsTotal} of YOUR trades - including the losses.`;
  const projectionTrajectory: GenericTrajectoryResponse | null = trajectory
    ? {
        ...trajectory,
        points: trajectory.points?.map((point) => ({ ...point, timestamp: undefined })),
      }
    : null;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([getAnalytics(), getTrajectory(), getConservationStatus()])
      .then(([nextAnalytics, nextTrajectory, nextConservation]) => {
        if (cancelled) return;
        setAnalytics(nextAnalytics);
        setTrajectory(nextTrajectory);
        setConservation(nextConservation);
        setError(null);
      })
      .catch((loadError) => {
        console.debug("performance data unavailable", loadError);
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Performance unavailable");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return <div data-screen-ready="false" className="copilot-card p-8 text-sm trading-muted">Loading performance...</div>;
  }

  if (error) {
    return (
      <section data-screen-ready="true" className="copilot-card p-6">
        <h2 className="text-xl font-semibold">Performance unavailable</h2>
        <p className="mt-2 text-sm trading-muted">{error}</p>
      </section>
    );
  }

  return (
    <div data-screen-ready="true" className="flex flex-col gap-4">
      <section className="copilot-card p-4">
        <h2 className="text-base font-semibold">Performance Summary</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-4">
          <Stat label="IKS" value={currentIks.toFixed(1)} />
          <Stat label="Win rate" value={pct(currentWinRate)} />
          <Stat label="Trades" value={String(decisionsTotal)} />
          <Stat label="Days active" value={String(daysActive)} />
        </div>
      </section>
      <TrajectoryChart
        points={points}
        currentIks={currentIks}
        currentWinRate={currentWinRate}
        switchingCostLine={67}
        narrative={narrative}
        decisionsTotal={decisionsTotal}
        daysActive={daysActive}
      />
      <CentroidTimeline />
      <ReConvergencePanel />
      <AuditTrail />
      <ConservationProjection conservation={conservation} trajectory={projectionTrajectory} />
      <RegimeStatusPanel />
      <AutonomyThrottlePanel />
      <RegimeRejectionPanel />
      <RegimeAnalyticsPanel />
      <RegimePanel />
      <VolatilityScenarioPanel />
      <div className="grid gap-4 xl:grid-cols-2" data-testid="trading-volatility-beats">
        <VolShortPanel />
        <VRPPanel />
        <RichCheapPanel />
        <DispersionPanel />
        <TailBetsPanel />
      </div>
      <CertificatePanel />
      <GateDividendPanel />
      <StrategySafetyBreakdownPanel />
      <PromotionDashboard />
      <RejectionMomentPanel />
      <RejectionMomentTable />
      <TransferPanel />
      <EvolutionPanel />
      <EvolutionControlsPanel />
      <ExecutionQualityCard />
      <WebhookStatusCard />
      <CohortStatusPanel />
      <VIXTimingPanel />
      <RollingMetrics analytics={analytics} />
      <CategoryPerformance analytics={analytics} />
      <RiskManagementCard analytics={analytics} />
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border px-3 py-2" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="text-xs trading-muted">{label}</div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  );
}
