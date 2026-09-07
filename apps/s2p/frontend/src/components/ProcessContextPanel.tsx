import type { ProcessContext, ProcessContextDetail } from "../types";

function field<T>(snake: T | undefined, camel: T | undefined): T | undefined {
  return snake ?? camel;
}

export function ProcessContextPanel({
  processContext,
  contextDetail,
}: {
  processContext?: ProcessContext | null;
  contextDetail?: ProcessContextDetail | null;
}) {
  const timeline = contextDetail?.activity_timeline ?? contextDetail?.activityTimeline ?? contextDetail?.activities ?? [];
  const bottleneck = contextDetail?.bottleneck;
  if (contextDetail) {
    return (
      <article className="copilot-card border-amber-200 bg-amber-50 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Process context</p>
            <h2 className="mt-1 text-lg font-semibold text-amber-950">{contextDetail.invoice_id ?? contextDetail.invoiceId ?? "Invoice"} activity chain</h2>
          </div>
          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-amber-800">
            {(contextDetail.source ?? "fixture").replace(/_/g, " ")}
          </span>
        </div>
        <dl className="mt-4 grid gap-3 sm:grid-cols-4">
          <Metric label="P2P variant" value={contextDetail.category?.replace(/_/g, " ") ?? "standard"} />
          <Metric label="Cycle time" value={formatHours(contextDetail.total_cycle_time_hours ?? contextDetail.totalCycleTimeHours)} />
          <Metric label="Bottleneck" value={bottleneck?.activity ?? "n/a"} />
          <Metric label="Reason" value={bottleneck?.reason ?? "n/a"} />
        </dl>
        {timeline.length ? (
          <div className="mt-4 overflow-hidden rounded-md border border-amber-200 bg-white">
            {timeline.map((activity, index) => {
              const name = activity.activity ?? activity.name ?? activity.id ?? `Activity ${index + 1}`;
              const duration = activity.duration_hours ?? activity.durationHours ?? activity.duration_median_hours ?? activity.durationMedianHours;
              return (
                <div key={`${name}-${index}`} className="grid gap-2 border-b border-amber-100 px-3 py-2 text-sm last:border-b-0 md:grid-cols-[1fr_auto_auto]">
                  <span className="font-semibold text-slate-900">{name}</span>
                  <span className="text-slate-600">{activity.system ?? "system n/a"}</span>
                  <span className="text-slate-600">{formatHours(duration)}</span>
                </div>
              );
            })}
          </div>
        ) : null}
      </article>
    );
  }

  const activity = field(processContext?.bottleneck_activity, processContext?.bottleneckActivity);
  const duration = field(processContext?.duration_median_min, processContext?.durationMedianMin);
  const cause = processContext?.cause ?? processContext?.root_cause ?? processContext?.rootCause;
  const source = processContext?.source;

  if (!processContext || (!activity && duration === undefined && !cause)) {
    return (
      <article className="copilot-card border-amber-200 bg-amber-50 p-5">
        <h2 className="text-lg font-semibold text-amber-950">Process Context (Celonis)</h2>
        <p className="mt-3 text-sm text-amber-800">No process context available.</p>
      </article>
    );
  }

  return (
    <article className="copilot-card border-amber-200 bg-amber-50 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-amber-950">Process Context (Celonis)</h2>
        {source ? (
          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-amber-800">
            {source.replace(/_/g, " ")}
          </span>
        ) : null}
      </div>
      <dl className="mt-4 grid gap-3 sm:grid-cols-3">
        <Metric label="Bottleneck activity" value={activity ?? "n/a"} />
        <Metric label="Duration median" value={typeof duration === "number" ? `${duration} min` : "n/a"} />
        <Metric label="Root cause" value={cause ?? "n/a"} />
      </dl>
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-amber-200 bg-white/80 p-3">
      <dt className="text-xs font-semibold uppercase tracking-wide text-amber-700">{label}</dt>
      <dd className="mt-2 text-sm font-semibold text-slate-950">{value}</dd>
    </div>
  );
}

function formatHours(value?: number): string {
  if (typeof value !== "number") return "n/a";
  if (value < 1) return `${Math.round(value * 60)} min`;
  return `${value.toFixed(1)} h`;
}
