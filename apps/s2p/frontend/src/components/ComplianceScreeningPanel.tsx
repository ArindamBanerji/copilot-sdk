import { useEffect, useState } from "react";
import { getComplianceScreening } from "../api";
import type { ComplianceScreeningResponse } from "../types";

function percent(value?: number): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "n/a";
}

function status(value?: boolean): string {
  return value ? "Ready" : "Review";
}

function statusClass(value?: boolean): string {
  return value ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-amber-200 bg-amber-50 text-amber-700";
}

export function ComplianceScreeningPanel() {
  const [data, setData] = useState<ComplianceScreeningResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    getComplianceScreening()
      .then((response) => {
        if (cancelled) return;
        if (!response) {
          setError("Compliance screening is unavailable.");
          setData(null);
          return;
        }
        setData(response);
      })
      .catch(() => {
        if (!cancelled) {
          setError("Compliance screening is unavailable.");
          setData(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Governance controls</p>
          <h2 className="mt-1 text-xl font-semibold text-slate-950">Compliance Screening</h2>
        </div>
        {loading ? <span className="text-sm text-slate-500">Loading compliance screening...</span> : null}
      </div>

      {error ? <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}

      {!loading && !error && data ? (
        <>
          <div className="mt-4 grid gap-3 sm:grid-cols-4">
            <Metric label="Compliance rate" value={percent(data.compliance_rate)} />
            <Metric label="SOX score" value={percent(data.sox_readiness?.score)} />
            <Metric label="Gaps" value={data.with_gaps} />
            <Metric label="Hash chain" value={data.chain_integrity?.verified ? "Valid" : "Review"} />
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <ChecklistItem label="Article 14 traceable" value={data.eu_ai_act.article_14_traceable} />
            <ChecklistItem label="Human oversight documented" value={data.eu_ai_act.human_oversight_documented} />
            <ChecklistItem label="Automated decision logged" value={data.eu_ai_act.automated_decision_logged} />
          </div>

          <div className="mt-4 rounded-md border border-slate-200 bg-white p-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Decisions screened</p>
            <p className="mt-2 text-sm text-slate-600">
              {data.total_decisions_screened} decisions screened, {data.compliant} compliant, {data.with_gaps} with gaps.
            </p>
          </div>
        </>
      ) : null}
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-lg font-semibold text-slate-950">{value}</p>
    </div>
  );
}

function ChecklistItem({ label, value }: { label: string; value?: boolean }) {
  return (
    <div className={`rounded-md border p-3 ${statusClass(value)}`}>
      <p className="text-xs font-semibold uppercase tracking-wide">{label}</p>
      <p className="mt-2 text-sm font-semibold">{status(value)}</p>
    </div>
  );
}
