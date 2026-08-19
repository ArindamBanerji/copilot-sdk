import { useEffect, useMemo, useState } from "react";
import { ConservationProjection } from "../../../../../copilot_sdk/frontend";
import TrajectoryChart, { type TrajectoryPoint } from "../../../../../copilot_sdk/frontend/TrajectoryChart";
import { getAnalytics, getConservationStatus, getTrajectory } from "../api";
import AlertDashboardCard from "../components/AlertDashboardCard";
import AuditExportPanel from "../components/AuditExportPanel";
import CategoryAccuracyChart from "../components/CategoryAccuracyChart";
import { CentroidTimelineChart } from "../components/CentroidTimelineChart";
import ChainTransferCard from "../components/ChainTransferCard";
import CohortStatusPanel from "../components/CohortStatusPanel";
import DisruptionRecoveryPanel from "../components/DisruptionRecoveryPanel";
import EconomicDashboardCard from "../components/EconomicDashboardCard";
import GroupDashboardCard from "../components/GroupDashboardCard";
import IKSTrackerPanel from "../components/IKSTrackerPanel";
import PaymentTimingPanel from "../components/PaymentTimingPanel";
import PurchasingProofPanel from "../components/PurchasingProofPanel";
import SupplierScorecardPanel from "../components/SupplierScorecardPanel";
import WasteAlertCard from "../components/WasteAlertCard";
import WasteCostCard from "../components/WasteCostCard";
import WeeklyReportPanel from "../components/WeeklyReportPanel";
import type { Analytics, ConservationState, TrajectoryResponse } from "../types";

function numberOr(value: unknown, fallback: number) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function toTrajectoryPoints(trajectory?: TrajectoryResponse): TrajectoryPoint[] {
  const raw = trajectory?.points ?? trajectory?.trajectory ?? [];
  return raw.map((point, index) => ({
    decisions: numberOr(point.decisions ?? point.decision ?? point.decisionsTotal, index + 1),
    iks: numberOr(point.iks ?? point.currentIks, 0),
    winRate: numberOr(point.winRate ?? point.win_rate, 0),
  }));
}

export default function PerformanceScreen() {
  const [trajectory, setTrajectory] = useState<TrajectoryResponse | undefined>();
  const [analytics, setAnalytics] = useState<Analytics | undefined>();
  const [conservation, setConservation] = useState<ConservationState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | undefined>();

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(undefined);
      try {
        const [nextTrajectory, nextAnalytics, nextConservation] = await Promise.all([
          getTrajectory(),
          getAnalytics(),
          getConservationStatus().catch(() => null),
        ]);
        if (mounted) {
          setTrajectory(nextTrajectory);
          setAnalytics(nextAnalytics);
          setConservation(nextConservation);
        }
      } catch (caught) {
        if (mounted) {
          setError(caught instanceof Error ? caught.message : "Unable to load performance");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, []);

  const points = useMemo(() => toTrajectoryPoints(trajectory), [trajectory]);
  const lastPoint = points.length > 0 ? points[points.length - 1] : undefined;
  const orders = numberOr(analytics?.portfolioSummary?.totalOrders, numberOr(trajectory?.decisionsTotal, points.length));
  const accuracy = numberOr(analytics?.portfolioSummary?.accuracy, lastPoint?.winRate ?? 0);
  const currentIks = numberOr(trajectory?.currentIks ?? trajectory?.iks, lastPoint?.iks ?? 0);
  const daysActive = numberOr(trajectory?.daysActive, 0);
  const managed = analytics?.aeImpact?.managedByRules;

  if (loading) {
    return <section data-screen-ready="false" className="purchase-card">Loading performance...</section>;
  }

  if (error) {
    return (
      <section data-screen-ready="true" className="purchase-card error-card">
        <p className="purchase-kicker">Performance unavailable</p>
        <p>{error}</p>
      </section>
    );
  }

  return (
    <div data-screen-ready="true" className="purchase-stack performance-screen">
      <PurchasingProofPanel />
      <section className="purchase-card">
        <p className="purchase-kicker">Performance</p>
        <h1 className="purchase-title">20 orders to learn what takes 11 years of gut instinct.</h1>
        <div className="stats-row">
          <div><span>IKS</span><strong>{currentIks.toFixed(1)}</strong></div>
          <div><span>Accuracy</span><strong>{(accuracy * 100).toFixed(0)}%</strong></div>
          <div><span>Orders</span><strong>{orders}</strong></div>
          <div><span>Days active</span><strong>{daysActive.toFixed(1)}</strong></div>
        </div>
      </section>

      <ChainTransferCard />
      <WeeklyReportPanel />
      <EconomicDashboardCard />
      <DisruptionRecoveryPanel />
      <PaymentTimingPanel />
      <AuditExportPanel />
      <GroupDashboardCard />
      <AlertDashboardCard />
      <IKSTrackerPanel />
      <CohortStatusPanel />
      <SupplierScorecardPanel />

      <TrajectoryChart
        points={points}
        currentIks={currentIks}
        currentWinRate={accuracy}
        switchingCostLine={55}
        narrative="20 orders to learn what takes 11 years of gut instinct."
        decisionsTotal={orders}
        daysActive={daysActive}
      />
      <ConservationProjection conservation={conservation} trajectory={trajectory || null} />
      <CentroidTimelineChart />

      <section className="purchase-card">
        <p className="purchase-kicker">Cost impact</p>
        <h2 className="purchase-title">Waste and stockouts are now measurable</h2>
        <div className="stats-row">
          <div>
            <span>Waste reduction</span>
            <strong>{numberOr(analytics?.portfolioSummary?.wasteReductionSinceStartPct, 0).toFixed(1)}%</strong>
          </div>
          <div>
            <span>Stockout events</span>
            <strong>{analytics?.wasteCostAnalysis?.stockoutOrders ?? 0}</strong>
          </div>
          <div>
            <span>Stockout cost</span>
            <strong>${numberOr(analytics?.wasteCostAnalysis?.totalStockoutCostDollars, 0).toFixed(0)}</strong>
          </div>
          <div>
            <span>AE auto-decisions</span>
            <strong>{managed?.count ?? 0}</strong>
          </div>
        </div>
      </section>

      <WasteCostCard analytics={analytics} />
      <WasteAlertCard />
      <CategoryAccuracyChart analytics={analytics} />
    </div>
  );
}
