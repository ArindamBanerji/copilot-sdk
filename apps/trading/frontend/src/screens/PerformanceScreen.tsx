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
import PromotionDashboard from "../components/PromotionDashboard";
import RiskManagementCard from "../components/RiskManagementCard";
import RollingMetrics from "../components/RollingMetrics";
import StrategySafetyBreakdownPanel from "../components/StrategySafetyBreakdownPanel";
import TransferPanel from "../components/TransferPanel";
import VIXTimingPanel from "../components/VIXTimingPanel";
import type { Analytics, ConservationState, TrajectoryResponse } from "../types";

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

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [trajectoryPayload, analyticsPayload, conservationPayload] = await Promise.all([
          getTrajectory(),
          getAnalytics(),
          getConservationStatus().catch(() => null),
        ]);
        if (!cancelled) {
          setTrajectory(trajectoryPayload);
          setAnalytics(analyticsPayload);
          setConservation(conservationPayload);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Performance load failed");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

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

  if (loading) {
    return <div className="copilot-card p-8 text-sm trading-muted">Loading performance...</div>;
  }

  if (error) {
    return (
      <section className="copilot-card p-6">
        <h2 className="text-xl font-semibold">Performance unavailable</h2>
        <p className="mt-2 text-sm trading-muted">{error}</p>
      </section>
    );
  }

  return (
    <div className="flex flex-col gap-4">
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
      <AuditTrail />
      <ConservationProjection conservation={conservation} trajectory={projectionTrajectory} />
      <StrategySafetyBreakdownPanel />
      <PromotionDashboard />
      <TransferPanel />
      <EvolutionPanel />
      <EvolutionControlsPanel />
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
