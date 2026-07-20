import { useEffect, useMemo, useState } from "react";

export type MeasurementStateName = "instrument_validated" | "accumulating" | "measured" | string;

export interface MeasurementStatus {
  state?: MeasurementStateName;
  decisionsVerified?: number;
  decisions_verified?: number;
  decisionsNeeded?: number;
  decisions_needed?: number;
  armsMeasured?: number;
  arms_measured?: number;
  armsTotal?: number;
  arms_total?: number;
  accuracy?: number | null;
  iks?: number | null;
  message?: string;
  provenance?: string;
}

export interface DayZeroCardProps {
  apiBase?: string;
  copilot?: string;
  demoMode?: boolean;
  renderProvenance?: (source: string) => React.ReactNode;
}

const DAY_ZERO_STATUS: MeasurementStatus = {
  state: "instrument_validated",
  decisionsVerified: 0,
  decisionsNeeded: 30,
  armsMeasured: 0,
  armsTotal: 0,
  accuracy: null,
  iks: null,
  message: "Instrument calibrated. Awaiting first verified decision.",
  provenance: "instrument",
};

const FALLBACK_STATUS: MeasurementStatus = {
  state: "error",
  accuracy: null,
  iks: null,
  message: "Unable to load measurement state",
  provenance: "unavailable",
};

export default function DayZeroCard({
  apiBase = "",
  copilot = "trading",
  demoMode = false,
  renderProvenance,
}: DayZeroCardProps) {
  const [status, setStatus] = useState<MeasurementStatus>(FALLBACK_STATUS);
  const [loading, setLoading] = useState(true);
  const [showDayZero, setShowDayZero] = useState(false);
  const [retryToken, setRetryToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    fetch(`${apiBase}/api/${copilot}/measurement-state`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`measurement-state returned ${response.status}`);
        }
        return response.json();
      })
      .then((payload) => {
        if (!cancelled) {
          setStatus(toCamelStatus(payload));
        }
      })
      .catch((error) => {
        console.debug("measurement state fetch failed", error);
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
  }, [apiBase, copilot, retryToken]);

  const displayedStatus = showDayZero ? DAY_ZERO_STATUS : status;
  const state = displayedStatus.state || "error";
  const decisionsVerified = numberOr(displayedStatus.decisionsVerified ?? displayedStatus.decisions_verified, 0);
  const decisionsNeeded = numberOr(displayedStatus.decisionsNeeded ?? displayedStatus.decisions_needed, 30);
  const armsMeasured = numberOr(displayedStatus.armsMeasured ?? displayedStatus.arms_measured, 0);
  const armsTotal = numberOr(displayedStatus.armsTotal ?? displayedStatus.arms_total, 0);
  const kMin = decisionsVerified + decisionsNeeded;
  const provenance = displayedStatus.provenance || provenanceFor(state);
  const progress = useMemo(() => {
    if (kMin <= 0) return 0;
    return Math.max(0, Math.min(100, (decisionsVerified / kMin) * 100));
  }, [decisionsVerified, kMin]);

  return (
    <section className="copilot-card p-4" data-testid="day-zero-card">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wide trading-muted">Day-Zero Honesty</p>
          <h2 className="mt-1 text-base font-semibold">{headingFor(state, loading)}</h2>
        </div>
        <div className="flex items-center gap-2">
          {demoMode && status.state === "measured" ? (
            <button
              type="button"
              data-testid="day-zero-toggle"
              onClick={() => setShowDayZero((current) => !current)}
              className="rounded border border-slate-300 bg-white px-2 py-1 text-xs font-semibold text-slate-700"
            >
              {showDayZero ? "Show measured view" : "Show day-zero view"}
            </button>
          ) : null}
          {state !== "error" ? (renderProvenance ? renderProvenance(provenance) : <DefaultBadge source={provenance} />) : null}
        </div>
      </div>

      {state === "error" ? (
        <ErrorBody onRetry={() => setRetryToken((current) => current + 1)} />
      ) : state === "measured" ? (
        <MeasuredBody status={displayedStatus} decisionsVerified={decisionsVerified} />
      ) : state === "accumulating" ? (
        <AccumulatingBody
          armsMeasured={armsMeasured}
          armsTotal={armsTotal}
          decisionsVerified={decisionsVerified}
          kMin={kMin}
          progress={progress}
        />
      ) : (
        <InstrumentBody />
      )}

      {state !== "error" ? (
        <p className="mt-3 text-xs trading-muted">{loading && !showDayZero ? "Checking measurement state..." : displayedStatus.message}</p>
      ) : null}
    </section>
  );
}

function InstrumentBody() {
  return (
    <div className="mt-3 grid gap-2 text-sm">
      <p>The scoring engine is deployed and responding. Factors configured.</p>
      <p className="font-semibold">Awaiting first verified decision.</p>
      <p className="font-semibold">No magnitude claims yet.</p>
      <p className="trading-muted">This is what honest looks like on day one. No fake numbers.</p>
    </div>
  );
}

function ErrorBody({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="mt-3 grid gap-3 text-sm">
      <p className="font-semibold">Unable to load measurement state.</p>
      <button
        type="button"
        onClick={onRetry}
        className="w-fit rounded border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700"
      >
        Retry
      </button>
    </div>
  );
}

function AccumulatingBody({
  armsMeasured,
  armsTotal,
  decisionsVerified,
  kMin,
  progress,
}: {
  armsMeasured: number;
  armsTotal: number;
  decisionsVerified: number;
  kMin: number;
  progress: number;
}) {
  return (
    <div className="mt-4">
      <div className="h-2 overflow-hidden rounded-full bg-slate-200">
        <div className="h-full bg-amber-500" style={{ width: `${progress}%` }} />
      </div>
      <div className="mt-2 text-sm font-semibold">
        {decisionsVerified} / {kMin} decisions
      </div>
      <p className="mt-2 text-sm trading-muted">
        {armsMeasured} of {armsTotal} arms measured. Accuracy will be available at {kMin}.
      </p>
    </div>
  );
}

function MeasuredBody({
  status,
  decisionsVerified,
}: {
  status: MeasurementStatus;
  decisionsVerified: number;
}) {
  return (
    <div className="mt-3 grid gap-3 text-sm sm:grid-cols-3">
      <Metric label="Accuracy" value={formatPercent(status.accuracy)} />
      <Metric label="IKS" value={formatNumber(status.iks)} />
      <Metric label="Verified decisions" value={String(decisionsVerified)} />
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs trading-muted">{label}</div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  );
}

function DefaultBadge({ source }: { source: string }) {
  return <span className="rounded-full bg-slate-200 px-2 py-1 text-xs">{source}</span>;
}

function headingFor(state: string, loading: boolean): string {
  if (loading) return "Measurement State";
  if (state === "error") return "Measurement State Unavailable";
  if (state === "measured") return "Measured";
  if (state === "accumulating") return "Accumulating Evidence";
  return "Instrument Calibrated";
}

function provenanceFor(state: string): string {
  if (state === "error") return "unavailable";
  if (state === "measured") return "real_measured";
  if (state === "accumulating") return "accumulating";
  return "instrument";
}

function numberOr(value: unknown, fallback: number): number {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function formatPercent(value: number | null | undefined): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "Pending";
  return `${(value * 100).toFixed(1)}%`;
}

function formatNumber(value: number | null | undefined): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "Pending";
  return value.toFixed(1);
}

function toCamelStatus(value: MeasurementStatus): MeasurementStatus {
  return {
    ...value,
    decisionsVerified: value.decisionsVerified ?? value.decisions_verified,
    decisionsNeeded: value.decisionsNeeded ?? value.decisions_needed,
    armsMeasured: value.armsMeasured ?? value.arms_measured,
    armsTotal: value.armsTotal ?? value.arms_total,
  };
}
