import { useEffect, useState } from "react";
import { fetchProcessFusion } from "../api";
import type { ProcessFusionResponse } from "../types";
import ProvenanceBadge from "./ProvenanceBadge";

const SAMPLE_EVENTS: Array<Record<string, unknown>> = [
  {
    case_id: "INV-1001",
    activity: "3-way match",
    timestamp: "2026-07-01T08:00:00Z",
    resource: "Chicago AP team",
    duration_ms: 15120000,
    variant: "non-standard format",
    supplier: "Supplier X",
  },
  {
    case_id: "INV-1002",
    activity: "3-way match",
    timestamp: "2026-07-01T09:00:00Z",
    resource: "Chicago AP team",
    duration_ms: 15120000,
    variant: "non-standard format",
    supplier: "Supplier Y",
  },
  {
    case_id: "INV-1003",
    activity: "3-way match",
    timestamp: "2026-07-01T10:00:00Z",
    resource: "Chicago AP team",
    duration_ms: 15120000,
    variant: "non-standard format",
    supplier: "Supplier Z",
  },
  {
    case_id: "INV-1004",
    activity: "invoice receipt",
    timestamp: "2026-07-01T11:00:00Z",
    resource: "Houston AP team",
    duration_ms: 3960000,
    variant: "standard",
    supplier: "Supplier A",
  },
];

function pct(value: number | undefined): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "-";
}

export default function ProcessFusionPanel() {
  const [data, setData] = useState<ProcessFusionResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchProcessFusion(SAMPLE_EVENTS)
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch((error) => {
        console.debug("Process fusion fetch failed", error);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!data) {
    return (
      <article data-testid="process-fusion-panel" className="copilot-card p-5">
        <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Process intelligence fusion</p>
        <p className="mt-3 text-sm text-slate-500">Fusion signal unavailable.</p>
      </article>
    );
  }

  return (
    <article data-testid="process-fusion-panel" className="copilot-card p-5">
      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Process intelligence fusion</p>
          <h2 className="mt-1 text-xl font-semibold text-slate-950">Where to What to Why to Decision</h2>
        </div>
        <ProvenanceBadge source="sample" provenance="sample" />
      </div>

      <div className="mt-5 grid gap-4">
        <FusionRow
          label="WHERE"
          title={`${data.where.bottleneck} - ${data.where.activity}`}
          detail={`${data.where.avg_duration_hours.toFixed(1)} hours (benchmark: ${data.where.vs_benchmark_hours.toFixed(1)})`}
          testId="process-fusion-where"
        />
        <FusionRow
          label="WHAT"
          title={`Exception rate ${pct(data.what.exception_rate)} (org avg: ${pct(data.what.vs_org_rate)})`}
          detail={data.what.pattern}
          testId="process-fusion-what"
        />
        <FusionRow
          label="WHY"
          title={data.why.situation_analysis}
          detail={data.why.root_cause}
          testId="process-fusion-why"
        />
        <div data-testid="process-fusion-which" className="rounded-md border border-emerald-200 bg-emerald-50 p-4">
          <div className="grid gap-2 md:grid-cols-[120px_1fr]">
            <div className="text-sm font-bold uppercase tracking-wide text-emerald-700">WHICH DECISION</div>
            <div>
              <p className="font-semibold text-slate-950">{data.which_decision.recommendation}</p>
              <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-slate-600">
                <span>Impact: {data.which_decision.estimated_impact}</span>
                <ProvenanceBadge source={data.which_decision.provenance} provenance={data.which_decision.provenance} />
              </div>
              <p className="mt-1 text-sm text-slate-600">Confidence: {pct(data.which_decision.confidence)}</p>
            </div>
          </div>
        </div>
      </div>

      <p className="mt-5 text-sm font-semibold text-slate-700">
        Celonis shows WHERE. We show WHY and WHICH DECISION.
      </p>
    </article>
  );
}

function FusionRow({
  label,
  title,
  detail,
  testId,
}: {
  label: string;
  title: string;
  detail: string;
  testId: string;
}) {
  return (
    <div data-testid={testId} className="grid gap-2 rounded-md border border-slate-200 p-4 md:grid-cols-[120px_1fr]">
      <div className="text-sm font-bold uppercase tracking-wide text-slate-500">{label}</div>
      <div>
        <p className="font-semibold text-slate-950">{title}</p>
        <p className="mt-1 text-sm text-slate-600">{detail}</p>
      </div>
    </div>
  );
}
