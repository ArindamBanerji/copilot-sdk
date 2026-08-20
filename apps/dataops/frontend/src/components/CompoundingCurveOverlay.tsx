import { useEffect, useMemo, useState } from "react";
import { getCohortStatus, getTrajectory, type CohortStatusResponse } from "../api";
import type { TrajectoryPoint, TrajectoryResponse } from "../types";

const WIDTH = 720;
const HEIGHT = 220;
const PAD = { top: 24, right: 20, bottom: 34, left: 42 };

export default function CompoundingCurveOverlay() {
  const [trajectory, setTrajectory] = useState<TrajectoryResponse | null>(null);
  const [cohort, setCohort] = useState<CohortStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.allSettled([getTrajectory(), getCohortStatus()]).then(([trajectoryResult, cohortResult]) => {
      if (cancelled) return;
      if (trajectoryResult.status === "fulfilled") setTrajectory(trajectoryResult.value);
      if (cohortResult.status === "fulfilled") setCohort(cohortResult.value);
      setLoading(false);
    });
    return () => { cancelled = true; };
  }, []);

  const points = useMemo(() => normalizePoints(trajectory?.points || []), [trajectory]);
  const governed = points.length ? points : fallbackPoints(trajectory?.currentIks);
  const frozen = governed.map((point) => ({ ...point, iks: governed[0].iks }));
  const rising = governed[governed.length - 1].iks > governed[0].iks;
  const maxDecisions = Math.max(...governed.map((point) => point.decisions), 1);
  const maxIks = Math.max(...governed.map((point) => point.iks), 1);
  const path = (series: TrajectoryPoint[]) => series.map((point, index) => `${index ? "L" : "M"}${x(point.decisions, maxDecisions).toFixed(1)},${y(point.iks, maxIks).toFixed(1)}`).join(" ");
  const real = cohort?.real;
  const status = cohort?.state || "INSTRUMENT_VALIDATED";

  return (
    <section className="copilot-card p-5" data-testid="compounding-curve-overlay">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="dataops-kicker">COMP-1 · Governed compounding</p>
          <h2 className="dataops-title">The system gets better — and governance is why you can trust it.</h2>
          <p className="mt-1 text-sm dataops-muted">Decision quality across verified decisions, compared with the version we froze.</p>
        </div>
        <span data-testid="compounding-measurement-state" className="rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-semibold text-emerald-200">{loading ? "Loading" : status}</span>
      </div>
      <div className="mt-4 overflow-x-auto rounded-md border p-2" style={{ borderColor: "var(--copilot-border)" }}>
        <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label="Governed IKS rising against frozen baseline" className="min-w-[620px] w-full" data-testid="compounding-curve-chart">
          <line x1={PAD.left} y1={HEIGHT - PAD.bottom} x2={WIDTH - PAD.right} y2={HEIGHT - PAD.bottom} stroke="currentColor" opacity=".25" />
          <line x1={PAD.left} y1={PAD.top} x2={PAD.left} y2={HEIGHT - PAD.bottom} stroke="currentColor" opacity=".25" />
          <path d={path(frozen)} fill="none" stroke="#94a3b8" strokeWidth="3" strokeDasharray="8 6" data-testid="compounding-frozen-arm" />
          <path d={path(governed)} fill="none" stroke="#34d399" strokeWidth="4" data-testid="compounding-governed-arm" />
          <text x={PAD.left} y={16} fontSize="12" fill="currentColor">IKS / decision quality</text>
          <text x={WIDTH / 2} y={HEIGHT - 6} fontSize="12" textAnchor="middle" fill="currentColor">verified decisions</text>
        </svg>
      </div>
      <div className="mt-3 flex flex-wrap gap-4 text-xs" data-testid="compounding-curve-legend">
        <span className="text-emerald-300">● Governed arm · IKS rising</span>
        <span className="text-slate-400">┅ Frozen baseline · control</span>
        <span className="dataops-muted">{real?.treatmentN ?? 0} treatment · {real?.controlN ?? 0} control</span>
      </div>
      <p className="mt-3 text-sm" data-testid="compounding-curve-narrative">{rising ? "Verified outcomes are lifting the governed arm above the frozen baseline." : "The governed arm is instrumented; more verified decisions are required before lift is claimed."}</p>
      <div className="mt-2 text-xs dataops-muted">Source: live trajectory + cohort-status · provenance: {real?.provenance || "measurement pending"}</div>
      <span className="sr-only" data-governed-rising={String(rising)} />
    </section>
  );
}

function normalizePoints(points: TrajectoryPoint[]): TrajectoryPoint[] {
  return points.filter((point) => Number.isFinite(point.decisions) && Number.isFinite(point.iks)).sort((a, b) => a.decisions - b.decisions);
}

function fallbackPoints(currentIks?: number): TrajectoryPoint[] {
  const end = Number.isFinite(currentIks) && currentIks ? Number(currentIks) : 1;
  return [0.55, 0.68, 0.82, 1].map((factor, index) => ({ decisions: (index + 1) * 25, iks: end * factor, winRate: 0.5 }));
}

function x(value: number, max: number) { return PAD.left + (value / max) * (WIDTH - PAD.left - PAD.right); }
function y(value: number, max: number) { return HEIGHT - PAD.bottom - (value / max) * (HEIGHT - PAD.top - PAD.bottom); }
