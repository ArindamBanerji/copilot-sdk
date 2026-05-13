import { useEffect, useState } from "react";
import { fetchS2PCrossGraph } from "../api";
import type { CrossGraphResponse } from "../types";

function percent(value?: number) {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "n/a";
}

export function CrossGraphInsightCard() {
  const [data, setData] = useState<CrossGraphResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchS2PCrossGraph().then((response) => {
      if (!cancelled) setData(response);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const top = data?.insights?.[0];
  const duration = data?.bottleneck_duration ?? data?.bottleneckDuration ?? 0;
  const bottleneck = data?.bottleneck_activity ?? data?.bottleneckActivity ?? "Match Invoice to GR";

  return (
    <article className="copilot-card border-amber-200 bg-amber-50 p-5">
      <p className="text-sm font-semibold uppercase tracking-wide text-amber-800">Cross-graph signal</p>
      <h2 className="mt-1 text-xl font-semibold text-slate-950">Supplier exceptions align with process delay</h2>
      {!top ? (
        <p className="mt-4 text-sm text-slate-600">No cross-graph correlations available.</p>
      ) : (
        <div className="mt-4 space-y-3">
          <p className="text-sm leading-6 text-slate-700">
            {top.supplier} has {percent(top.exception_rate ?? top.exceptionRate)} exception history while{" "}
            <span className="font-semibold">{bottleneck}</span> carries a {duration.toFixed(1)}h bottleneck.
          </p>
          <div className="grid gap-3 sm:grid-cols-3">
            <Metric label="Supplier" value={top.supplier ?? "n/a"} />
            <Metric label="Commodity" value={top.commodity ?? top.category ?? "n/a"} />
            <Metric label="Impact score" value={(top.impact_score ?? top.impactScore ?? 0).toFixed(3)} />
          </div>
        </div>
      )}
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-amber-200 bg-white p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">{label}</p>
      <p className="mt-2 break-words text-sm font-semibold text-slate-950">{value}</p>
    </div>
  );
}
