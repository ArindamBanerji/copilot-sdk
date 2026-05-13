import type { ConservationStatus } from "../types";

function percent(value?: number) {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "n/a";
}

export function ConservationMiniGauge({ conservation }: { conservation?: ConservationStatus | null }) {
  const q = conservation?.q ?? conservation?.accuracy ?? 0;
  const verified = conservation?.verified_decisions ?? conservation?.verifiedDecisions ?? conservation?.verified_count ?? conservation?.verifiedCount ?? 0;
  const status = conservation?.status ?? "n/a";

  return (
    <article className="copilot-card p-5">
      <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Conservation mini-gauge</p>
      <div className="mt-4 flex items-center gap-4">
        <div className="grid h-24 w-24 place-items-center rounded-full border-8 border-amber-400 bg-amber-50">
          <span className="text-xl font-semibold text-slate-950">{percent(q)}</span>
        </div>
        <div>
          <h2 className="text-xl font-semibold text-slate-950">{status}</h2>
          <p className="mt-1 text-sm text-slate-500">{verified} verified decisions · penalty 5:1</p>
        </div>
      </div>
    </article>
  );
}
