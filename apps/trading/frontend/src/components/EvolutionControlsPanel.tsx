import { useCallback, useEffect, useMemo, useState } from "react";
import {
  applyEvolutionProposal,
  fetchEvolutionActive,
  fetchEvolutionProposalResponse,
  fetchParameterEvolutionLog,
  rollbackEvolution,
  type ParameterEvolutionActive,
  type ParameterEvolutionProposal,
  type ParameterEvolutionProposalResponse,
} from "../api";
import ProvenanceBadge from "./ProvenanceBadge";

function proposalId(proposal: ParameterEvolutionProposal): string {
  return proposal.proposalId ?? proposal.proposal_id ?? "";
}

function currentValue(proposal: ParameterEvolutionProposal): number {
  return Number(proposal.currentValue ?? proposal.current_value ?? 0);
}

function proposedValue(proposal: ParameterEvolutionProposal): number {
  return Number(proposal.proposedValue ?? proposal.proposed_value ?? 0);
}

function conservationState(proposal: ParameterEvolutionProposal): string {
  return proposal.conservationState ?? proposal.conservation_state ?? "UNKNOWN";
}

function formatValue(value: unknown): string {
  return typeof value === "number" ? value.toFixed(3) : "-";
}

function badgeClass(state: string): string {
  if (state === "GREEN") return "bg-emerald-100 text-emerald-800";
  if (state === "AMBER") return "bg-amber-100 text-amber-800";
  return "bg-red-100 text-red-800";
}

export default function EvolutionControlsPanel() {
  const [active, setActive] = useState<ParameterEvolutionActive>({
    parameterAdjustments: {},
    conservationState: "GREEN",
    bounds: {},
  });
  const [proposalPayload, setProposalPayload] = useState<ParameterEvolutionProposalResponse | ParameterEvolutionProposal[] | null>(null);
  const [history, setHistory] = useState<ParameterEvolutionProposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const proposalList = Array.isArray(proposalPayload) ? proposalPayload : proposalPayload?.proposals ?? [];
  const proposals = proposalList.filter((entry) => !entry.kind || entry.kind === "parameter");
  const proposalNote = Array.isArray(proposalPayload) ? "" : proposalPayload?.note ?? "";
  const proposalProvenance = Array.isArray(proposalPayload) ? "" : proposalPayload?.provenance ?? "";

  const state = active.conservationState ?? "GREEN";
  const adjustments = useMemo(() => Object.entries(active.parameterAdjustments ?? {}), [active]);
  const bounds = useMemo(() => Object.entries(active.bounds ?? {}), [active]);
  const canApply = state === "GREEN";

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    Promise.all([fetchEvolutionActive(), fetchEvolutionProposalResponse(), fetchParameterEvolutionLog()])
      .then(([nextActive, nextProposals, nextHistory]) => {
        setActive(nextActive);
        setProposalPayload(nextProposals);
        setHistory(nextHistory.filter((entry) => entry.kind === "parameter"));
      })
      .catch((loadError) => {
        console.debug("parameter evolution unavailable", loadError);
        setError("Parameter evolution unavailable.");
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function onApply(id: string) {
    if (!id) return;
    await applyEvolutionProposal(id);
    load();
  }

  async function onRollback(parameter: string) {
    await rollbackEvolution(parameter);
    load();
  }

  return (
    <section className="copilot-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold">Parameter Evolution</h2>
            <span className={`rounded px-2 py-1 text-xs font-semibold ${badgeClass(state)}`}>
              {state === "GREEN" ? "Evolution active" : state === "AMBER" ? "Evolution paused" : "Evolution paused -- rollback recommended"}
            </span>
          </div>
          <p className="mt-1 text-sm trading-muted">Scorer parameter changes are proposed from verified decisions and bounded by hard limits.</p>
        </div>
        <ProvenanceBadge source="real_measured" />
      </div>

      {loading ? (
        <p className="mt-4 text-sm trading-muted">Loading parameter evolution...</p>
      ) : error ? (
        <p className="mt-4 text-sm text-red-500">{error}</p>
      ) : (
        <div className="mt-5 grid gap-4 xl:grid-cols-2">
          <article className="rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
            <h3 className="text-sm font-semibold">Active Adjustments</h3>
            {adjustments.length === 0 ? (
              <p className="mt-3 text-sm trading-muted">No active parameter adjustments.</p>
            ) : (
              <div className="mt-3 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="text-left text-xs trading-muted">
                    <tr>
                      <th className="py-2 pr-3">Parameter</th>
                      <th className="py-2 pr-3">Original</th>
                      <th className="py-2 pr-3">Adjusted</th>
                      <th className="py-2 pr-3">Evidence</th>
                      <th className="py-2">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {adjustments.map(([parameter, adjustment]) => (
                      <tr key={parameter} className="border-t" style={{ borderColor: "var(--copilot-border)" }}>
                        <td className="py-2 pr-3">{parameter}</td>
                        <td className="py-2 pr-3">{formatValue(adjustment.original)}</td>
                        <td className="py-2 pr-3">{formatValue(adjustment.adjusted)}</td>
                        <td className="py-2 pr-3">{adjustment.evidence ?? "-"}</td>
                        <td className="py-2">
                          <button className="rounded border px-2 py-1 text-xs" onClick={() => void onRollback(parameter)}>
                            Rollback
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </article>

          <article className="rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
            <h3 className="text-sm font-semibold">Pending Proposals</h3>
            {proposalProvenance ? (
              <p className="mt-2 text-sm trading-muted">
                {proposalProvenance === "demo" ? "Demo -- based on synthetic evidence" : proposalProvenance}
                {proposalNote ? `. ${proposalNote}` : ""}
              </p>
            ) : null}
            {!canApply ? (
              <p className="mt-2 text-sm text-amber-700">Conservation must be GREEN to apply.</p>
            ) : null}
            {proposals.length === 0 ? (
              <p className="mt-3 text-sm trading-muted">No pending proposals.</p>
            ) : (
              <div className="mt-3 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="text-left text-xs trading-muted">
                    <tr>
                      <th className="py-2 pr-3">Parameter</th>
                      <th className="py-2 pr-3">Current</th>
                      <th className="py-2 pr-3">Proposed</th>
                      <th className="py-2 pr-3">Evidence</th>
                      <th className="py-2">Apply</th>
                    </tr>
                  </thead>
                  <tbody>
                    {proposals.map((proposal) => (
                      <tr key={proposalId(proposal)} className="border-t" style={{ borderColor: "var(--copilot-border)" }}>
                        <td className="py-2 pr-3">{proposal.parameter}</td>
                        <td className="py-2 pr-3">{currentValue(proposal).toFixed(3)}</td>
                        <td className="py-2 pr-3">{proposedValue(proposal).toFixed(3)}</td>
                        <td className="py-2 pr-3">{proposal.evidence}</td>
                        <td className="py-2">
                          <button
                            className="rounded border px-2 py-1 text-xs disabled:opacity-50"
                            disabled={!canApply}
                            onClick={() => void onApply(proposalId(proposal))}
                          >
                            Apply
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </article>

          <article className="rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
            <h3 className="text-sm font-semibold">Hard Bounds Reference</h3>
            <p className="mt-1 text-sm trading-muted">These bounds cannot be overridden.</p>
            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              {bounds.map(([parameter, range]) => (
                <div key={parameter} className="rounded border px-3 py-2 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
                  <div className="text-xs trading-muted">{parameter}</div>
                  <div className="font-semibold">{Array.isArray(range) ? `${range[0]} to ${range[1]}` : "-"}</div>
                </div>
              ))}
            </div>
          </article>

          <article className="rounded-md border p-4" style={{ borderColor: "var(--copilot-border)" }}>
            <h3 className="text-sm font-semibold">Evolution History</h3>
            {history.length === 0 ? (
              <p className="mt-3 text-sm trading-muted">No parameter history yet.</p>
            ) : (
              <div className="mt-3 max-h-64 overflow-auto">
                {history.map((entry) => (
                  <div key={proposalId(entry)} className="border-t py-2 text-sm" style={{ borderColor: "var(--copilot-border)" }}>
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="font-semibold">{entry.parameter}</span>
                      <span className={`rounded px-2 py-1 text-xs ${badgeClass(conservationState(entry))}`}>
                        {entry.applied ? "applied" : entry.rolledBack ?? entry.rolled_back ? "rolled back" : "proposed"}
                      </span>
                    </div>
                    <p className="mt-1 trading-muted">{entry.evidence}</p>
                  </div>
                ))}
              </div>
            )}
          </article>
        </div>
      )}
    </section>
  );
}
