import { useEffect, useMemo, useState } from "react";
import { fetchAutoApproveStats, fetchExpansionProof } from "../api";
import type { AutoApproveCategoryStats, AutoApproveStats, ExpansionProof } from "../types";

function formatLabel(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatPercent(value?: number | null): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "n/a";
  return `${Math.round(value * 100)}%`;
}

function formatCount(value?: number): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "0";
  return new Intl.NumberFormat("en-US").format(value);
}

function categoryStats(stats: AutoApproveStats | null): Record<string, AutoApproveCategoryStats> {
  return stats?.per_category ?? stats?.perCategory ?? {};
}

function currentRate(stats: AutoApproveStats | null): number | undefined {
  return stats?.current_auto_approve_rate ?? stats?.currentAutoApproveRate;
}

function spotChecks(stats: AutoApproveStats | null): number {
  return stats?.total_spot_checked ?? stats?.totalSpotChecked ?? 0;
}

function spotCheckAccuracy(stats: AutoApproveStats | null): number | undefined {
  return stats?.spot_check_accuracy ?? stats?.spotCheckAccuracy;
}

function proofCurrentThreshold(proof: ExpansionProof): number {
  return proof.current_threshold ?? proof.currentThreshold ?? 0;
}

function proofProposedThreshold(proof: ExpansionProof): number {
  return proof.proposed_threshold ?? proof.proposedThreshold ?? 0;
}

function proofVerified(proof: ExpansionProof): number {
  return proof.verified_decisions ?? proof.verifiedDecisions ?? 0;
}

function proofConservation(proof: ExpansionProof): string {
  return proof.conservation_status ?? proof.conservationStatus ?? "n/a";
}

function proofSafe(proof: ExpansionProof): boolean {
  return proof.safe_to_expand ?? proof.safeToExpand ?? false;
}

function proofRollback(proof: ExpansionProof): boolean {
  return proof.rollback_available ?? proof.rollbackAvailable ?? false;
}

export function AutoApprovePanel() {
  const [stats, setStats] = useState<AutoApproveStats | null>(null);
  const [proof, setProof] = useState<ExpansionProof | null>(null);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [loadingStats, setLoadingStats] = useState(true);
  const [loadingProof, setLoadingProof] = useState(false);
  const [error, setError] = useState("");
  const [proofError, setProofError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoadingStats(true);
    setError("");
    fetchAutoApproveStats()
      .then((response) => {
        if (cancelled) return;
        if (!response) {
          setError("Auto-approve stats are unavailable.");
          return;
        }
        const categories = Object.keys(categoryStats(response));
        setStats(response);
        setSelectedCategory((current) => current || categories[0] || "");
      })
      .catch((caught) => {
        if (!cancelled) setError(caught instanceof Error ? caught.message : "Unable to load auto-approve stats.");
      })
      .finally(() => {
        if (!cancelled) setLoadingStats(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const rows = useMemo(() => Object.entries(categoryStats(stats)), [stats]);

  function loadProof() {
    const category = selectedCategory || rows[0]?.[0];
    if (!category) return;
    setLoadingProof(true);
    setProofError("");
    fetchExpansionProof(category)
      .then((response) => {
        if (!response) {
          setProofError("Expansion proof is unavailable for this category.");
          return;
        }
        setProof(response);
      })
      .catch((caught) => {
        setProofError(caught instanceof Error ? caught.message : "Unable to load expansion proof.");
      })
      .finally(() => setLoadingProof(false));
  }

  return (
    <article className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Control gate</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-950">Auto-Approve Status</h2>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
          {loadingStats ? "Loading" : formatPercent(currentRate(stats))}
        </span>
      </div>

      {loadingStats ? (
        <p className="mt-4 text-sm text-slate-500">Loading auto-approve telemetry...</p>
      ) : error ? (
        <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-700">{error}</p>
      ) : rows.length === 0 ? (
        <p className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-500">No auto-approve category data is available.</p>
      ) : (
        <>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <Metric label="Auto-approve rate" value={formatPercent(currentRate(stats))} />
            <Metric label="Spot checks" value={formatCount(spotChecks(stats))} />
            <Metric label="Spot-check accuracy" value={formatPercent(spotCheckAccuracy(stats))} />
          </div>

          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full border-separate border-spacing-0 text-left text-sm">
              <thead>
                <tr className="text-xs uppercase tracking-wide text-slate-500">
                  <th className="border-b border-slate-200 px-3 py-2 font-semibold">Category</th>
                  <th className="border-b border-slate-200 px-3 py-2 font-semibold">Approved</th>
                  <th className="border-b border-slate-200 px-3 py-2 font-semibold">Held</th>
                  <th className="border-b border-slate-200 px-3 py-2 font-semibold">Threshold</th>
                </tr>
              </thead>
              <tbody>
                {rows.map(([category, item]) => (
                  <tr key={category} className="text-slate-700">
                    <td className="border-b border-slate-100 px-3 py-3 font-medium text-slate-950">{formatLabel(category)}</td>
                    <td className="border-b border-slate-100 px-3 py-3">{formatCount(item.approved)}</td>
                    <td className="border-b border-slate-100 px-3 py-3">{formatCount(item.held)}</td>
                    <td className="border-b border-slate-100 px-3 py-3">{formatPercent(item.threshold)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4 flex flex-wrap items-end gap-3">
            <label className="flex min-w-56 flex-col gap-1 text-sm font-medium text-slate-700">
              Expansion category
              <select
                value={selectedCategory}
                onChange={(event) => setSelectedCategory(event.target.value)}
                className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900"
              >
                {rows.map(([category]) => (
                  <option key={category} value={category}>
                    {formatLabel(category)}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              onClick={loadProof}
              disabled={loadingProof || rows.length === 0}
              className="rounded-md bg-slate-950 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {loadingProof ? "Loading Proof..." : "View Expansion Proof"}
            </button>
          </div>

          {proofError ? (
            <p className="mt-4 rounded-md bg-rose-50 p-3 text-sm text-rose-700">{proofError}</p>
          ) : null}

          {proof ? <ExpansionProofCard proof={proof} /> : null}
        </>
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

function ExpansionProofCard({ proof }: { proof: ExpansionProof }) {
  const safe = proofSafe(proof);
  return (
    <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-slate-950">{formatLabel(proof.category)} expansion proof</h3>
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${safe ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>
          {safe ? "Safe to expand" : "Hold threshold"}
        </span>
      </div>
      <div className="mt-3 grid gap-3 sm:grid-cols-3">
        <Metric label="Current threshold" value={formatPercent(proofCurrentThreshold(proof))} />
        <Metric label="Proposed threshold" value={formatPercent(proofProposedThreshold(proof))} />
        <Metric label="Accuracy" value={formatPercent(proof.accuracy)} />
        <Metric label="Verified decisions" value={formatCount(proofVerified(proof))} />
        <Metric label="Conservation" value={proofConservation(proof)} />
        <Metric label="Rollback" value={proofRollback(proof) ? "Available" : "Unavailable"} />
      </div>
      <p className="mt-3 text-sm text-slate-600">{proof.evidence}</p>
    </div>
  );
}
