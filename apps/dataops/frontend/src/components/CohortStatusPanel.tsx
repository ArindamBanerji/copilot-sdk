import { useEffect, useMemo, useState } from "react";
import { getCohortStatus, type CohortExperiment, type CohortStatusResponse } from "../api";

const FALLBACK_STATUS: CohortStatusResponse = {
  state: "INSTRUMENT_VALIDATED",
  instrument: { validated: false, provenance: "oracle", experiments: [] },
  real: {
    treatmentN: 0,
    controlN: 0,
    thresholdK: 30,
    lift: null,
    provenance: "real",
    status: "pending",
  },
  structure: { present: false, treatmentN: 0, controlN: 0, provenance: "sample" },
};

export default function CohortStatusPanel() {
  const [status, setStatus] = useState<CohortStatusResponse>(FALLBACK_STATUS);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getCohortStatus()
      .then((payload) => {
        if (!cancelled) {
          setStatus(payload);
        }
      })
      .catch((error) => {
        console.debug("cohort status fetch failed", error);
        if (!cancelled) {
          setStatus(FALLBACK_STATUS);
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

  const real = status.real ?? FALLBACK_STATUS.real;
  const treatmentN = numberOr(real?.treatmentN, 0);
  const controlN = numberOr(real?.controlN, 0);
  const thresholdK = numberOr(real?.thresholdK, 30);
  const total = treatmentN + controlN;
  const experiments = useMemo(
    () => ensureArray(status.instrument?.experiments),
    [status.instrument?.experiments],
  );
  const state = status.state || "INSTRUMENT_VALIDATED";
  const badge = badgeFor(state);
  const measured = state === "MEASURED" && typeof real?.lift === "number";

  return (
    <section className="copilot-card p-4" data-testid="cohort-status-panel">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wide dataops-muted">DataOps Measurement Status</p>
          <h2 className="dataops-section-title mt-1">Cohort measurement readiness</h2>
        </div>
        <span
          className="rounded-full px-3 py-1 text-xs font-semibold"
          data-testid="cohort-status-state"
          style={{ background: badge.background, color: badge.color }}
        >
          {badge.label}
        </span>
      </div>

      <p className="mt-3 text-sm dataops-muted">{loading ? "Loading measurement status..." : summaryFor(state, real?.lift, total, thresholdK)}</p>

      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        <section className="rounded-md border p-3" data-testid="cohort-status-instrument" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="text-xs font-semibold uppercase tracking-wide dataops-muted">T-O instrument</div>
          <p className="mt-2 text-sm">Validated - detects injected lift (+/-, recovered pass)</p>
          {experiments.length ? (
            <ul className="mt-3 grid gap-2 text-xs dataops-muted">
              {experiments.map((experiment, index) => (
                <li key={`${experiment.name || "experiment"}-${index}`}>
                  {experiment.name || `Experiment ${index + 1}`}: {experiment.pass ? "pass" : "pending"}
                </li>
              ))}
            </ul>
          ) : null}
        </section>

        <section className="rounded-md border p-3" data-testid="cohort-status-real" style={{ borderColor: "var(--copilot-border)" }}>
          <div className="text-xs font-semibold uppercase tracking-wide dataops-muted">T-R real measurement</div>
          <p className="mt-2 text-sm">
            {measured
              ? `Lift: ${formatLift(real?.lift)} from ${total} real decisions`
              : state === "ACCUMULATING"
                ? `Collecting decisions: ${total} of ${thresholdK * 2}`
                : "Measured on your team's real decisions. Appears here as they act."}
          </p>
          <p className="mt-2 text-xs dataops-muted" data-testid="cohort-status-progress">
            {treatmentN}/{thresholdK} shown, {controlN}/{thresholdK} control
          </p>
        </section>
      </div>
    </section>
  );
}

function badgeFor(state: string) {
  if (state === "MEASURED") {
    return { label: "Measured", background: "rgba(16, 185, 129, 0.16)", color: "#047857" };
  }
  if (state === "ACCUMULATING") {
    return { label: "Measuring", background: "rgba(245, 158, 11, 0.18)", color: "#92400e" };
  }
  return { label: "Measurement ready", background: "rgba(59, 130, 246, 0.16)", color: "#1d4ed8" };
}

function summaryFor(state: string, lift: number | null | undefined, total: number, thresholdK: number): string {
  if (state === "MEASURED" && typeof lift === "number") {
    return `Measured from ${total} real decisions.`;
  }
  if (state === "ACCUMULATING") {
    return `Measuring with ${total} of ${thresholdK * 2} decisions collected.`;
  }
  return "Measurement machinery is ready before real cohorts arrive.";
}

function ensureArray(value: CohortExperiment[] | undefined): CohortExperiment[] {
  return Array.isArray(value) ? value : [];
}

function numberOr(value: unknown, fallback: number): number {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function formatLift(value: number | null | undefined): string {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return "+0.0%";
  }
  const percent = Math.abs(value) <= 1 ? value * 100 : value;
  return `${percent >= 0 ? "+" : ""}${percent.toFixed(1)}%`;
}
