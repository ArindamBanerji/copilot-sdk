import { useEffect, useMemo, useState } from "react";
import { fetchProcessData } from "../api";
import type { CrossGraphInsight, ProcessData } from "../types";

interface CrossGraphInsightCardProps {
  insight?: CrossGraphInsight | null;
  data?: ProcessData | null;
}

function currency(value?: number) {
  if (typeof value !== "number") {
    return null;
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export function CrossGraphInsightCard({ insight, data }: CrossGraphInsightCardProps) {
  const [remoteData, setRemoteData] = useState<ProcessData | null>(null);

  useEffect(() => {
    if (insight || data) {
      return;
    }

    let cancelled = false;
    fetchProcessData().then((response) => {
      if (!cancelled) {
        setRemoteData(response);
      }
    });

    return () => {
      cancelled = true;
    };
  }, [data, insight]);

  const activeInsight = useMemo(() => {
    if (insight) {
      return insight;
    }
    const source = data ?? remoteData;
    return source?.crossGraphInsights?.[0] ?? null;
  }, [data, insight, remoteData]);

  const impact =
    currency(activeInsight?.monthlyImpactUsd) ??
    currency(activeInsight?.annualImpactUsd) ??
    currency(activeInsight?.annualizedSavingsUsd) ??
    currency(activeInsight?.preventableImpactUsd);

  return (
    <section className="rounded-md border border-purple-300/20 bg-purple-500/10 p-5">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-purple-200/80">
        Cross-Graph Insight
      </p>
      <h2 className="mt-2 text-xl font-semibold text-white">
        {activeInsight?.title ?? activeInsight?.finding ?? "SAP, Celonis, and Graph signals aligned"}
      </h2>
      <p className="mt-2 text-sm leading-6 text-slate-300">
        {activeInsight?.detail ??
          activeInsight?.finding ??
          "Process intelligence is correlating enterprise events with graph evidence."}
      </p>
      <div className="mt-4 flex flex-wrap gap-2 text-sm">
        {typeof activeInsight?.confidence === "number" ? (
          <span className="rounded-md border border-white/10 bg-white/10 px-3 py-1 text-slate-100">
            {Math.round(activeInsight.confidence * 100)}% confidence
          </span>
        ) : null}
        {impact ? (
          <span className="rounded-md border border-emerald-300/30 bg-emerald-500/10 px-3 py-1 text-emerald-100">
            {impact} impact
          </span>
        ) : null}
      </div>
      <p className="mt-4 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
        SAP × Celonis × Graph
      </p>
    </section>
  );
}
