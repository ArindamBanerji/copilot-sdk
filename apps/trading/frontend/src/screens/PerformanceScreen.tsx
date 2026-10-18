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

function isAbortError(error: unknown): boolean {
  const message = error instanceof Error ? error.message : String(error);
  return /abort/i.test(message);
}

async function retryAbort<T>(load: () => Promise<T>, attempts = 3): Promise<T> {
  let lastError: unknown;
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      return await load();
    } catch (error) {
      if (!isAbortError(error)) {
        throw error;
      }
      lastError = error;
      await new Promise((resolve) => window.setTimeout(resolve, 150 * (attempt + 1)));
    }
  }
  throw lastError;
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
    setError(null);
    const loads = [
      retryAbort(getAnalytics).then((nextAnalytics) => {
        if (!cancelled) setAnalytics(nextAnalytics);
      }),
      retryAbort(getTrajectory).then((nextTrajectory) => {
        if (!cancelled) setTrajectory(nextTrajectory);
      }),
      retryAbort(getConservationStatus).then((nextConservation) => {
        if (!cancelled) setConservation(nextConservation);
      }),
    ];
    Promise.allSettled(loads)
      .then((results) => {
        if (cancelled) return;
        const failures = results.filter((result) => result.status === "rejected");
        if (failures.length > 0) {
          console.debug("performance data partially unavailable", failures);
          setError(`${failures.length} performance data source${failures.length === 1 ? " is" : "s are"} unavailable`);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div data-screen-ready="true" className="flex flex-col gap-4">
      {loading ? (
        <div className="copilot-card p-3 text-sm trading-muted">Loading performance data…</div>
      ) : null}
      {error ? (
        <div className="copilot-card p-3 text-sm trading-muted">{error}; showing available performance data.</div>
      ) : null}
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
