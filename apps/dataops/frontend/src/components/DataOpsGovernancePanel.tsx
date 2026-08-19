import { useEffect, useState } from "react";
import { fetchDataOpsAbstention, fetchDataOpsGovernance, fetchDataOpsHoldout, type DataOpsAbstentionStatus, type DataOpsGovernanceStatus, type DataOpsHoldoutStatus } from "../api";

export default function DataOpsGovernancePanel() {
  const [claims, setClaims] = useState<DataOpsGovernanceStatus | null>(null);
  const [holdout, setHoldout] = useState<DataOpsHoldoutStatus | null>(null);
  const [abstention, setAbstention] = useState<DataOpsAbstentionStatus | null>(null);

  useEffect(() => {
    Promise.all([fetchDataOpsGovernance(), fetchDataOpsHoldout(), fetchDataOpsAbstention()]).then(([claimResult, holdoutResult, abstentionResult]) => {
      setClaims(claimResult);
      setHoldout(holdoutResult);
      setAbstention(abstentionResult);
    });
  }, []);

  const failingClaims = claims?.claims.filter((claim) => claim.passed === false).length ?? 0;
  return (
    <section className="copilot-card p-5" data-testid="dataops-governance-panel">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide dataops-muted">Evidence governance</p>
          <h2 className="mt-1 text-lg font-semibold">Measured proof, clearly separated from modelled value</h2>
        </div>
        <span data-testid="dataops-evidence-label" className="rounded-full px-3 py-1 text-xs font-semibold" style={{ background: "rgba(245, 158, 11, 0.14)", color: "#b45309" }}>
          {failingClaims ? "Modelled — not measured" : "Evidence gate clear"}
        </span>
      </div>
      {abstention?.shouldAbstain ? <div data-testid="dataops-abstention-card" className="mt-4 rounded-md border p-3 text-sm" style={{ borderColor: "#f59e0b" }}><strong>I don&apos;t know yet.</strong> {abstention.reason.split("_").join(" ")} ({abstention.currentEvidence}/{abstention.evidenceFloor} verified).</div> : null}
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div data-testid="dataops-holdout-panel" className="rounded-md border p-3 text-sm"><strong>30-day holdout</strong><div className="dataops-muted">{holdout?.entries.length ?? 0} entries awaiting expert verification</div></div>
        <div className="rounded-md border p-3 text-sm"><strong>Claims below pilot floor</strong><div className="dataops-muted">{failingClaims} claim(s) require measured outcomes</div></div>
      </div>
    </section>
  );
}
