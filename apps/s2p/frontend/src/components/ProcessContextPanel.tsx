import type { ProcessContext } from "../types";

function field<T>(snake: T | undefined, camel: T | undefined): T | undefined {
  return snake ?? camel;
}

export function ProcessContextPanel({ processContext }: { processContext?: ProcessContext | null }) {
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
