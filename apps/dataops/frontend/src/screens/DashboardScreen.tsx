import { useEffect, useState } from "react";
import { ConservationSlider } from "../../../../../copilot_sdk/frontend";
import {
  getAeImpact,
  getAlerts,
  getConservationHistory,
  getConservationStatus,
  getPipelines,
  numberOr,
  postConservationWhatIf,
} from "../api";
import type {
  AEImpact,
  ConservationHistory,
  ConservationState,
  DataOpsAlert,
  PipelineSystem,
} from "../types";
import AEImpactPanel from "../components/AEImpactPanel";
import AlertQueue from "../components/AlertQueue";
import ConservationTimeline from "../components/ConservationTimeline";
import PipelineGrid from "../components/PipelineGrid";

interface DashboardScreenProps {
  onSelectAlert: (alertId: string) => void;
}

interface DashboardState {
  pipelines: PipelineSystem[];
  alerts: DataOpsAlert[];
  aeImpact: AEImpact | null;
  conservation: ConservationState | null;
  history: ConservationHistory | null;
}

export default function DashboardScreen({ onSelectAlert }: DashboardScreenProps) {
  const [state, setState] = useState<DashboardState>({
    pipelines: [],
    alerts: [],
    aeImpact: null,
    conservation: null,
    history: null,
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
      getConservationStatus(),
      getAeImpact(),
      getConservationHistory(),
    ])
      .then(([pipelines, alerts, conservation, aeImpact, history]) => {
        if (cancelled) {
          return;
        }
        setState({ pipelines, alerts, conservation, aeImpact, history });
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

  return (
    <div className="grid gap-5">
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

      <section className="grid gap-4 lg:grid-cols-[minmax(0,26rem)_1fr]">
        <AlertQueue alerts={state.alerts} onAlertClick={onSelectAlert} />
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
          <ConservationTimeline history={state.history} />
        </div>
      </section>
    </div>
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
