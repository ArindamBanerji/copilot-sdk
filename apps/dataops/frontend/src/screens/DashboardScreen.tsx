import { useEffect, useState } from "react";
import { ConservationSlider, TransferBadge } from "../../../../../copilot_sdk/frontend";
import {
  BASE,
  getAeImpact,
  getAlertGroups,
  getAlerts,
  getConservationHistory,
  getConservationStatus,
  getPipelines,
  getTrajectory,
  numberOr,
  postConservationWhatIf,
} from "../api";
import type {
  AEImpact,
  AlertGroupAlert,
  AlertGroupsResponse,
  ConservationHistory,
  ConservationState,
  DataOpsAlert,
  PipelineSystem,
  TrajectoryResponse,
} from "../types";
import AEImpactPanel from "../components/AEImpactPanel";
import AccuracyAlertPanel from "../components/AccuracyAlertPanel";
import AlertGroupCard from "../components/AlertGroupCard";
import AlertQueue from "../components/AlertQueue";
import ConservationProjection from "../components/ConservationProjection";
import ConservationTimeline from "../components/ConservationTimeline";
import { EnterpriseHealthBar } from "../components/EnterpriseHealthBar";
import PipelineGrid from "../components/PipelineGrid";
import ProcessTimelinePanel from "../components/ProcessTimelinePanel";

interface DashboardScreenProps {
  onSelectAlert: (alertId: string) => void;
}

interface DashboardState {
  pipelines: PipelineSystem[];
  alerts: DataOpsAlert[];
  alertGroups: AlertGroupsResponse | null;
  aeImpact: AEImpact | null;
  conservation: ConservationState | null;
  history: ConservationHistory | null;
  trajectory: TrajectoryResponse | null;
}

export default function DashboardScreen({ onSelectAlert }: DashboardScreenProps) {
  const [state, setState] = useState<DashboardState>({
    pipelines: [],
    alerts: [],
    alertGroups: null,
    aeImpact: null,
    conservation: null,
    history: null,
    trajectory: null,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [whatIfPending, setWhatIfPending] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    Promise.all([
      getPipelines(),
      getAlerts(),
      getAlertGroups().catch(() => null),
      getConservationStatus(),
      getAeImpact(),
      getConservationHistory(),
      getTrajectory().catch(() => null),
    ])
      .then(([pipelines, alerts, alertGroups, conservation, aeImpact, history, trajectory]) => {
        if (cancelled) {
          return;
        }
        setState({ pipelines, alerts, alertGroups, conservation, aeImpact, history, trajectory });
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Could not load dashboard.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  async function handleConservationDrag(newThreshold: number) {
    setWhatIfPending(true);
    setState((current) => ({
      ...current,
      conservation: current.conservation
        ? { ...current.conservation, currentThreshold: newThreshold }
        : current.conservation,
    }));

    try {
      const next = await postConservationWhatIf({
        alpha: 0.7,
        q: Math.max(numberOr(state.conservation?.signal, 0.2), 0.01),
        V: Math.max(numberOr(state.conservation?.totalDecisions, 100), 1),
        thetaMin: newThreshold,
      });
      setState((current) => ({
        ...current,
        conservation: {
          ...current.conservation,
          ...next,
          penaltyRatio: current.conservation?.penaltyRatio ?? next.penaltyRatio,
          currentThreshold: newThreshold,
        },
      }));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Conservation what-if failed.");
    } finally {
      setWhatIfPending(false);
    }
  }

  if (loading) {
    return <DashboardFrame message="Loading DataOps dashboard..." />;
  }

  if (error) {
    return <DashboardFrame message={error} tone="error" />;
  }

  const conservation = state.conservation;
  const groups = state.alertGroups?.groups || [];
  const ungrouped = state.alertGroups?.ungrouped || [];
  const hasGroups = groups.length > 0;

  return (
    <div className="grid gap-5">
      <EnterpriseHealthBar />
      <TransferBadge apiBase={BASE} />

      <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <div>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="dataops-section-title">Pipeline Status</h2>
            <span className="text-sm dataops-muted">{state.pipelines.length} systems</span>
          </div>
          <PipelineGrid pipelines={state.pipelines} />
        </div>
        <AEImpactPanel impact={state.aeImpact} compact />
      </section>

      <ProcessTimelinePanel />

      <section className="grid gap-4 lg:grid-cols-[minmax(0,26rem)_1fr]">
        {hasGroups ? (
          <section className="grid gap-3">
            <div className="copilot-card p-4">
              <div className="flex items-center justify-between gap-3">
                <h2 className="dataops-section-title">Alert Root Causes</h2>
                <span className="text-sm dataops-muted">
                  {numberOr(state.alertGroups?.totalGroups ?? state.alertGroups?.total_groups, groups.length)} root causes ·{" "}
                  {numberOr(state.alertGroups?.totalAlerts ?? state.alertGroups?.total_alerts, state.alerts.length)} total alerts
                </span>
              </div>
            </div>
            {groups.map((group, index) => (
              <AlertGroupCard
                key={group.rootSystem || group.root_system || `group-${index}`}
                group={group}
                defaultExpanded={index === 0}
                onSelectAlert={onSelectAlert}
              />
            ))}
            {ungrouped.length > 0 ? (
              <UngroupedAlerts alerts={ungrouped} onSelectAlert={onSelectAlert} />
            ) : null}
          </section>
        ) : (
          <AlertQueue alerts={state.alerts} onAlertClick={onSelectAlert} />
        )}
        <div className="grid gap-4">
          {conservation ? (
            <div className="relative">
              <ConservationSlider
                currentThreshold={numberOr(conservation.currentThreshold, numberOr(conservation.thetaMin, 0.5))}
                conservationProduct={numberOr(conservation.signal, 0)}
                conservationThreshold={numberOr(conservation.thetaMin, 0)}
                penaltyRatio={numberOr(conservation.penaltyRatio, 1)}
                status={conservation.status || "AMBER"}
                onDrag={handleConservationDrag}
                narrative="Move the threshold to test whether automation still preserves enough conservation headroom."
              />
              {whatIfPending ? (
                <div className="mt-2 text-xs dataops-muted">Updating conservation what-if...</div>
              ) : null}
            </div>
          ) : (
            <DashboardFrame message="No conservation status available." />
          )}
          <ConservationProjection conservation={conservation} trajectory={state.trajectory} />
          <ConservationTimeline history={state.history} />
          <AccuracyAlertPanel />
        </div>
      </section>
    </div>
  );
}

function UngroupedAlerts({
  alerts,
  onSelectAlert,
}: {
  alerts: AlertGroupAlert[];
  onSelectAlert: (alertId: string) => void;
}) {
  return (
    <section className="copilot-card p-4">
      <h2 className="dataops-section-title">Ungrouped ({alerts.length})</h2>
      <div className="mt-3 grid gap-2">
        {alerts.map((alert, index) => {
          const id = alert.alertId || alert.alert_id || "";
          return (
            <div
              key={`${id || "ungrouped"}-${index}`}
              className="flex items-center justify-between gap-3 rounded-md border p-3 text-sm"
              style={{ borderColor: "var(--copilot-border)" }}
            >
              <div>
                <div className="font-semibold" style={{ color: "var(--copilot-text)" }}>{id || "unknown alert"}</div>
                <div className="mt-1 text-xs dataops-muted">
                  {alert.systemName || alert.system_name || "unknown system"} · {formatCategory(alert.category)} · {alert.severity || "unknown"}
                </div>
              </div>
              <button
                type="button"
                className="copilot-button-secondary px-3 py-2 text-xs"
                disabled={!id}
                onClick={() => {
                  if (id) {
                    onSelectAlert(id);
                  }
                }}
              >
                Triage
              </button>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function DashboardFrame({ message, tone = "muted" }: { message: string; tone?: "muted" | "error" }) {
  return (
    <div
      className="copilot-card p-6 text-sm"
      style={{ color: tone === "error" ? "var(--copilot-danger)" : "var(--copilot-text-muted)" }}
    >
      {message}
    </div>
  );
}

function formatCategory(value?: string): string {
  return value ? value.replace(/_/g, " ") : "uncategorized";
}
