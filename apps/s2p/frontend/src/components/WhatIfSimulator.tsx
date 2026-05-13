import { useEffect, useState } from "react";
import { fetchS2PWhatIf } from "../api";
import type { WhatIfResponse } from "../types";

function percent(value?: number) {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "n/a";
}

export function WhatIfSimulator() {
  const [additionalCorrect, setAdditionalCorrect] = useState(10);
  const [additionalIncorrect, setAdditionalIncorrect] = useState(0);
  const [data, setData] = useState<WhatIfResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchS2PWhatIf(additionalCorrect, additionalIncorrect).then((response) => {
      if (!cancelled) setData(response);
    });
    return () => {
      cancelled = true;
    };
  }, [additionalCorrect, additionalIncorrect]);

  return (
    <article className="copilot-card p-5">
      <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">What-if simulator</p>
      <h2 className="mt-1 text-xl font-semibold text-slate-950">Projected conservation state</h2>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <label className="text-sm font-medium text-slate-700">
          Additional correct
          <input
            type="number"
            min={0}
            max={100}
            value={additionalCorrect}
            onChange={(event) => setAdditionalCorrect(Number(event.target.value))}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </label>
        <label className="text-sm font-medium text-slate-700">
          Additional incorrect
          <input
            type="number"
            min={0}
            max={100}
            value={additionalIncorrect}
            onChange={(event) => setAdditionalIncorrect(Number(event.target.value))}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </label>
      </div>
      {data ? (
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <Metric label="Projected q" value={percent(data.projected.q)} />
          <Metric label="Theta min" value={percent(data.projected.theta_min ?? data.projected.thetaMin)} />
          <Metric label="Status" value={data.projected.status} />
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-500">Projection unavailable.</p>
      )}
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-lg font-semibold text-slate-950">{value}</p>
    </div>
  );
}
