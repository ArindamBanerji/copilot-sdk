import { useEffect, useState } from "react";
import { TrajectoryChart } from "../../../../../copilot_sdk/frontend";
import { getCentroidHistory, getTrajectory } from "../api";
import CentroidTimeline from "../components/CentroidTimeline";
import DisruptionAnnotation from "../components/DisruptionAnnotation";
import type { CentroidHistoryResponse, TrajectoryResponse } from "../types";

export default function CurveScreen() {
  const [trajectory, setTrajectory] = useState<TrajectoryResponse | null>(null);
  const [centroidHistory, setCentroidHistory] = useState<CentroidHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([
      getTrajectory(),
      getCentroidHistory().catch(() => null),
    ])
      .then(([result, centroidResult]) => {
        if (!cancelled) {
          setTrajectory(result);
          setCentroidHistory(centroidResult);
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Could not load trajectory.");
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

  if (loading) {
    return <Frame message="Loading DataOps learning curve..." />;
  }

  const points = trajectory?.points || [];

  return (
    <div className="grid gap-4">
      {error ? <Frame message={error} tone="error" /> : null}
      <TrajectoryChart
        points={points}
        currentIks={trajectory?.currentIks ?? 0}
        currentWinRate={trajectory?.currentWinRate ?? 0.5}
        annotations={[
          {
            decision: 301,
            type: "disruption",
            label: "SAP restructure",
            description: "6 pipeline configurations changed simultaneously.",
            recovery: "The graph recovers as confirmations re-anchor the new dependency shape.",
          },
        ]}
        narrative="Enterprise systems do not learn in a straight line. DataOps compounds through recurring graph patterns, then re-stabilizes after structural disruption."
        decisionsTotal={trajectory?.decisionsTotal ?? points[points.length - 1]?.decisions ?? 0}
        daysActive={trajectory?.daysActive ?? 0}
      />
      <DisruptionAnnotation />
      <CentroidTimeline data={centroidHistory} />
    </div>
  );
}

function Frame({ message, tone = "muted" }: { message: string; tone?: "muted" | "error" }) {
  return (
    <section className="copilot-card p-6 text-sm" style={{ color: tone === "error" ? "var(--copilot-danger)" : "var(--copilot-text-muted)" }}>
      {message}
    </section>
  );
}
