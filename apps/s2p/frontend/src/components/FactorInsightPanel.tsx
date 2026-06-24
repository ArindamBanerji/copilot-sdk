import { useEffect, useState } from "react";
import {
  getFactorAnalysis,
  proposeFactorReplacement,
  type FactorProposalResponse,
  type FactorRecommendation
} from "../api";

function label(value?: string): string {
  return String(value || "unknown").replace(/_/g, " ");
}

function num(value?: number): number {
  return typeof value === "number" ? value : 0;
}

function field(row: FactorRecommendation, snake: keyof FactorRecommendation, camel: keyof FactorRecommendation): number {
  const value = row[snake] ?? row[camel];
  return typeof value === "number" ? value : 0;
}

export default function FactorInsightPanel() {
  const [rows, setRows] = useState<FactorRecommendation[]>([]);
  const [proposal, setProposal] = useState<FactorProposalResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getFactorAnalysis()
      .then((payload) => {
        if (!cancelled) setRows(payload?.factors || []);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function propose(row: FactorRecommendation) {
    const factor = row.factor_name || row.factorName || "";
    if (!factor) return;
    setProposal(await proposeFactorReplacement(factor));
  }

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-amber-700">Factor intelligence</p>
          <h2 className="mt-1 text-xl font-semibold text-slate-950">Factor Intelligence</h2>
          <p className="mt-2 text-sm text-slate-600">Advisory factor contribution and replacement dry-runs.</p>
        </div>
        {loading ? <span className="text-sm text-slate-500">Loading factor analysis...</span> : null}
      </div>

      {!loading && rows.length === 0 ? (
        <p className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-500">No factor analysis available.</p>
      ) : null}

      <div className="mt-5 grid gap-3">
        {rows.map((row) => {
          const factor = row.factor_name || row.factorName || "";
          const contribution = field(row, "signal_contribution_pct", "signalContributionPct");
          const verdict = row.verdict || "review";
          return (
            <div key={factor}>
              <div className="flex items-center justify-between gap-3 text-sm">
                <span className="font-medium capitalize text-slate-700">{label(factor)}</span>
                <span className={verdict === "replace_candidate" ? "font-semibold text-amber-700" : "text-slate-500"}>
                  {contribution.toFixed(1)}%
                </span>
              </div>
              <div className="mt-1 h-2 rounded-md bg-slate-100">
                <div
                  className={verdict === "replace_candidate" ? "h-2 rounded-md bg-amber-500" : "h-2 rounded-md bg-slate-500"}
                  style={{ width: `${Math.max(3, Math.min(100, contribution))}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {rows.length ? (
        <div className="mt-5 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-slate-500">
              <tr>
                <th className="py-2 pr-3">Factor</th>
                <th className="py-2 pr-3">Weight</th>
                <th className="py-2 pr-3">Contribution</th>
                <th className="py-2 pr-3">Correlation</th>
                <th className="py-2 pr-3">Verdict</th>
                <th className="py-2 pr-3">Action</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const factor = row.factor_name || row.factorName || "";
                const verdict = row.verdict || "review";
                return (
                  <tr key={factor} className="border-t border-slate-200">
                    <td className="py-2 pr-3 capitalize">{label(factor)}</td>
                    <td className="py-2 pr-3">{field(row, "current_dk_weight", "currentDkWeight").toFixed(3)}</td>
                    <td className="py-2 pr-3">{field(row, "signal_contribution_pct", "signalContributionPct").toFixed(1)}%</td>
                    <td className="py-2 pr-3">{field(row, "outcome_correlation", "outcomeCorrelation").toFixed(2)}</td>
                    <td className={verdict === "replace_candidate" ? "py-2 pr-3 font-semibold text-amber-700" : "py-2 pr-3"}>
                      {label(verdict)}
                    </td>
                    <td className="py-2 pr-3">
                      {verdict === "replace_candidate" ? (
                        <button
                          type="button"
                          className="rounded-md bg-amber-600 px-3 py-1 text-xs font-semibold text-white"
                          onClick={() => propose(row)}
                        >
                          Propose Replacement
                        </button>
                      ) : (
                        <span className="text-slate-400">-</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}

      {proposal ? (
        <div className="mt-5 rounded-md border border-amber-300 bg-amber-50 p-4 text-sm text-amber-950">
          <p className="font-semibold">
            Replace {label(proposal.factor)} with {label(proposal.replacement)} for ~{num(proposal.estimated_pp ?? proposal.estimatedPp)}pp.
          </p>
          <p className="mt-2">{proposal.rationale}</p>
        </div>
      ) : null}
    </article>
  );
}
