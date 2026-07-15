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
  renderProvenance?: (source: string) => React.ReactNode;
}

const FALLBACK_STATUS: MeasurementStatus = {
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

export default function DayZeroCard({
  apiBase = "",
  copilot = "trading",
  renderProvenance,
}: DayZeroCardProps) {
  const [status, setStatus] = useState<MeasurementStatus>(FALLBACK_STATUS);
  const [loading, setLoading] = useState(true);

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
  }, [apiBase, copilot]);

  const state = status.state || "instrument_validated";
  const decisionsVerified = numberOr(status.decisionsVerified ?? status.decisions_verified, 0);
  const decisionsNeeded = numberOr(status.decisionsNeeded ?? status.decisions_needed, 30);
  const armsMeasured = numberOr(status.armsMeasured ?? status.arms_measured, 0);
  const armsTotal = numberOr(status.armsTotal ?? status.arms_total, 0);
  const kMin = decisionsVerified + decisionsNeeded;
  const provenance = status.provenance || provenanceFor(state);
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
        {renderProvenance ? renderProvenance(provenance) : <DefaultBadge source={provenance} />}
      </div>

      {state === "measured" ? (
        <MeasuredBody status={status} decisionsVerified={decisionsVerified} />
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

      <p className="mt-3 text-xs trading-muted">{loading ? "Checking measurement state..." : status.message}</p>
    </section>
  );
}

function InstrumentBody() {
  return (
    <div className="mt-3 grid gap-2 text-sm">
      <p>The scoring engine is deployed and responding. Factors configured.</p>
      <p className="font-semibold">Awaiting first verified decision.</p>
      <p className="trading-muted">This is what honest looks like on day one. No fake numbers.</p>
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
  if (state === "measured") return "Measured";
  if (state === "accumulating") return "Accumulating Evidence";
  return "Instrument Calibrated";
}

function provenanceFor(state: string): string {
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
