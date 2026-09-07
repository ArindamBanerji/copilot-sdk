import { useEffect, useState } from "react";
import type { CSSProperties } from "react";
import {
  fetchDataOpsAbstention,
  fetchDataOpsGovernance,
  fetchDataOpsHoldout,
  fetchDataOpsProvenance,
  registerDataOpsHoldout,
  verifyDataOpsHoldout,
  type DataOpsAbstentionStatus,
  type DataOpsGovernanceStatus,
  type DataOpsHoldoutStatus,
  type DataOpsProvenanceResponse,
} from "../api";

export default function DataOpsGovernancePanel() {
  const [claims, setClaims] = useState<DataOpsGovernanceStatus | null>(null);
  const [holdout, setHoldout] = useState<DataOpsHoldoutStatus | null>(null);
  const [abstention, setAbstention] = useState<DataOpsAbstentionStatus | null>(null);
  const [selectedProvenance, setSelectedProvenance] = useState<DataOpsProvenanceResponse | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const refresh = () => {
    Promise.all([fetchDataOpsGovernance(), fetchDataOpsHoldout(), fetchDataOpsAbstention()]).then(([claimResult, holdoutResult, abstentionResult]) => {
      setClaims(claimResult);
      setHoldout(holdoutResult);
      setAbstention(abstentionResult);
    });
  };
  useEffect(() => {
    refresh();
  }, []);

  const failingClaims = claims?.claims.filter((claim) => claim.passed === false).length ?? 0;
  const pendingEntries = holdout?.entries.filter((entry) => !entry.verifiedAt) ?? [];
  const evidenceStyle = evidenceStateStyle(claims?.state);
  const registerHoldout = async () => {
    setBusy("register");
    setNotice(null);
    try {
      await registerDataOpsHoldout({
        decisionId: `manual-${Date.now()}`,
        sourceId: "operator",
        decisionClass: "quality",
        scorePayload: { source: "governance_panel" },
      });
      setNotice("Holdout registered");
      refresh();
    } finally {
      setBusy(null);
    }
  };
  const verifyFirstHoldout = async () => {
    const entry = pendingEntries[0];
    if (!entry?.decisionId) return;
    setBusy(entry.decisionId);
    setNotice(null);
    try {
      await verifyDataOpsHoldout({ decisionId: entry.decisionId });
      setNotice("Holdout verified");
      refresh();
    } finally {
      setBusy(null);
    }
  };
  const showProvenance = async (decisionId?: string) => {
    if (!decisionId) return;
    setBusy(`provenance-${decisionId}`);
    setSelectedProvenance(await fetchDataOpsProvenance(decisionId));
    setBusy(null);
  };
  return (
    <section className="copilot-card p-5" data-testid="dataops-governance-panel">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide dataops-muted">Evidence governance</p>
          <h2 className="mt-1 text-lg font-semibold">Measured proof, clearly separated from modelled value</h2>
        </div>
        <span data-testid="dataops-evidence-label" className="rounded-full px-3 py-1 text-xs font-semibold" style={evidenceStyle}>
          {claims?.label ?? "Evidence gate: not evaluated"}
        </span>
      </div>
      {abstention?.shouldAbstain ? <div data-testid="dataops-abstention-card" className="mt-4 rounded-md border p-3 text-sm" style={{ borderColor: "#f59e0b" }}><strong>I don&apos;t know yet.</strong> {abstention.reason.split("_").join(" ")} ({abstention.currentEvidence}/{abstention.evidenceFloor} verified).</div> : null}
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div data-testid="dataops-holdout-panel" className="rounded-md border p-3 text-sm"><strong>30-day holdout</strong><div className="dataops-muted">{pendingEntries.length} entries awaiting expert verification</div></div>
        <div className="rounded-md border p-3 text-sm"><strong>Claims below pilot floor</strong><div className="dataops-muted">{failingClaims} claim(s) require measured outcomes</div></div>
      </div>
      <div data-testid="dataops-holdout-controls" className="mt-4 flex flex-wrap gap-2">
        <button type="button" onClick={registerHoldout} disabled={busy === "register"} className="rounded-md px-3 py-2 text-sm font-semibold text-white disabled:opacity-50" style={{ background: "var(--copilot-accent)" }}>Register holdout</button>
        <button type="button" onClick={verifyFirstHoldout} disabled={!pendingEntries.length || busy !== null} className="rounded-md border px-3 py-2 text-sm font-semibold disabled:opacity-50" style={{ borderColor: "var(--copilot-border)", color: "var(--copilot-text)" }}>Verify next</button>
        {notice ? <span className="self-center text-sm dataops-muted">{notice}</span> : null}
      </div>
      {holdout?.entries.length ? <div className="mt-4 grid gap-2" data-testid="dataops-holdout-list">{holdout.entries.slice(0, 4).map((entry) => <div key={entry.decisionId} className="flex flex-wrap items-center justify-between gap-2 rounded-md border p-3 text-sm" style={{ borderColor: "var(--copilot-border)" }}><span><strong>{entry.decisionId}</strong> <span className="dataops-muted">{entry.evidenceTier}</span></span><button type="button" onClick={() => showProvenance(entry.decisionId)} className="rounded-md border px-2 py-1 text-xs font-semibold" style={{ borderColor: "var(--copilot-border)", color: "var(--copilot-text)" }}>Provenance</button></div>)}</div> : null}
      {selectedProvenance ? <div data-testid="dataops-provenance-drilldown" className="mt-4 rounded-md border p-3 text-sm" style={{ borderColor: "var(--copilot-border)" }}><strong>{selectedProvenance.decisionId}</strong><div className="dataops-muted">{selectedProvenance.evidenceLabel ?? "provenance unavailable"} · {selectedProvenance.complete ? "complete" : "incomplete"}</div></div> : null}
    </section>
  );
}

function evidenceStateStyle(state?: string): CSSProperties {
  if (state === "VALIDATED") return { background: "rgba(34, 197, 94, 0.14)", color: "#15803d" };
  if (state === "FAILED") return { background: "rgba(239, 68, 68, 0.14)", color: "#b91c1c" };
  if (state === "PENDING") return { background: "rgba(245, 158, 11, 0.14)", color: "#b45309" };
  return { background: "rgba(148, 163, 184, 0.14)", color: "#64748b" };
}
