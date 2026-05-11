import type { CentroidHistoryResponse, CentroidShift, CentroidSnapshot } from "../types";

interface CentroidTimelineProps {
  data: CentroidHistoryResponse | null;
  loading?: boolean;
}

export default function CentroidTimeline({ data, loading = false }: CentroidTimelineProps) {
  if (loading) {
    return <section className="copilot-card p-4 text-sm dataops-muted">Loading centroid evolution...</section>;
  }

  const snapshots = data?.snapshots || [];
  if (!data || snapshots.length === 0) {
    return <section className="copilot-card p-4 text-sm dataops-muted">Centroid evolution unavailable.</section>;
  }

  const initial = snapshots[0];
  const current = snapshots[snapshots.length - 1];
  const topShifts = current.topShifts && current.topShifts.length > 0
    ? current.topShifts
    : computeShifts(initial, current);

  return (
    <section className="copilot-card p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="dataops-section-title">Centroid Evolution</h2>
          <p className="mt-1 text-xs dataops-muted">
            {initial.label || "Initial"} {"->"} {current.label || `Current (${data.totalDecisions ?? 0} decisions)`}
          </p>
        </div>
        <span className="rounded-full px-2 py-1 text-xs font-semibold" style={{ background: "#f3e8ff", color: "#7e22ce" }}>
          {data.totalDecisions ?? current.decisionIndex ?? 0} decisions
        </span>
      </div>

      <div className="mt-4 grid gap-2">
        {topShifts.length > 0 ? (
          topShifts.map((shift) => <ShiftRow key={shift.factor || "factor"} shift={shift} />)
        ) : (
          <div className="rounded-md border p-3 text-sm dataops-muted" style={{ borderColor: "var(--copilot-border)" }}>
            No centroid shifts are available yet.
          </div>
        )}
      </div>

      <blockquote className="mt-4 border-l-4 pl-3 text-sm dataops-muted" style={{ borderColor: "#8b5cf6" }}>
        These values didn't appear from nowhere - they evolved through verified decisions.
      </blockquote>
    </section>
  );
}

function ShiftRow({ shift }: { shift: CentroidShift }) {
  const from = numeric(shift.from, 0.5);
  const to = numeric(shift.to, from);
  const delta = numeric(shift.delta, to - from);
  const positive = delta >= 0;
  return (
    <div className="grid gap-2 rounded-md border p-3" style={{ borderColor: "var(--copilot-border)" }}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-sm font-semibold" style={{ color: "var(--copilot-text)" }}>{humanize(shift.factor || "factor")}</div>
        <div className="text-xs font-semibold" style={{ color: positive ? "#15803d" : "#b91c1c" }}>
          {formatNumber(from)} {"->"} {formatNumber(to)} ({positive ? "+" : ""}{formatNumber(delta)})
        </div>
      </div>
      <div className="h-2 overflow-hidden rounded-full" style={{ background: "rgba(148, 163, 184, 0.22)" }}>
        <div className="h-full rounded-full bg-violet-500" style={{ width: `${Math.min(Math.abs(delta) * 200, 100)}%` }} />
      </div>
    </div>
  );
}

function computeShifts(initial: CentroidSnapshot, current: CentroidSnapshot): CentroidShift[] {
  const initialCentroid = initial.centroidsSample || {};
  const currentCentroid = current.centroidsSample || {};
  return Object.entries(currentCentroid)
    .map(([factor, to]) => {
      const from = numeric(initialCentroid[factor], 0.5);
      return {
        factor,
        from,
        to,
        delta: Number((to - from).toFixed(3)),
      };
    })
    .sort((left, right) => Math.abs(right.delta || 0) - Math.abs(left.delta || 0))
    .slice(0, 3);
}

function numeric(value: unknown, fallback: number): number {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
}

function formatNumber(value: number): string {
  return value.toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
}

function humanize(value: string): string {
  return value.replace(/_/g, " ");
}
