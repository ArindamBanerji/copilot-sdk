import type { InvoiceException } from "../types";

function bottleneck(invoice?: InvoiceException) {
  return invoice?.process_context?.bottleneck_activity ?? invoice?.processContext?.bottleneckActivity ?? "Match Invoice to GR";
}

function duration(invoice?: InvoiceException) {
  return invoice?.process_context?.duration_median_min ?? invoice?.processContext?.durationMedianMin;
}

export function ProcessContextCard({ invoice }: { invoice?: InvoiceException }) {
  const minutes = duration(invoice);

  return (
    <article className="copilot-card border-amber-200 bg-amber-50 p-5">
      <p className="text-sm font-semibold uppercase tracking-wide text-amber-800">Process context</p>
      <h2 className="mt-1 text-xl font-semibold text-slate-950">Celonis bottleneck</h2>
      <p className="mt-3 text-sm leading-6 text-slate-700">
        {bottleneck(invoice)} is the active process signal across the current 50 invoice exception queue.
      </p>
      <div className="mt-4 rounded-md border border-amber-200 bg-white p-3">
        <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Duration median</p>
        <p className="mt-2 text-lg font-semibold text-slate-950">
          {typeof minutes === "number" ? `${Math.round(minutes)} min` : "42h signal"}
        </p>
      </div>
    </article>
  );
}
